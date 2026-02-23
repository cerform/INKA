"""
FastAPI router for the chaos engineering domain.

Endpoints:
  GET  /chaos/experiments        — list catalog
  POST /chaos/run                — start experiment
  POST /chaos/stop/{run_id}      — stop running experiment
  GET  /chaos/history            — paginated run history
  GET  /chaos/metrics            — dashboard aggregates
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, desc

from packages.chaos.catalog import ExperimentCatalog
from packages.chaos.runner import ChaosRunner
from packages.chaos.metrics import ChaosMetricsCollector
from packages.chaos.safety import (
    ComplianceGateError,
    EnvironmentGateError,
    AbortConditionError,
)
from apps.api.src.app.domains.chaos.models import (
    ExperimentSummary,
    RunExperimentRequest,
    RunResponse,
    StopExperimentRequest,
    HistoryItem,
    DashboardMetrics,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chaos", tags=["chaos"])
catalog = ExperimentCatalog()
metrics_collector = ChaosMetricsCollector()

# ---------------------------------------------------------------------------
# Dependency: DB session (reuse existing pattern)
# ---------------------------------------------------------------------------

async def get_session():
    """
    Yield async DB session.
    In production replace with the app's actual async session factory.
    """
    try:
        from packages.db.session import async_session_factory  # type: ignore
        async with async_session_factory() as session:
            yield session
    except ImportError:
        yield None  # graceful degradation when running without DB


# ---------------------------------------------------------------------------
# GET /chaos/experiments
# ---------------------------------------------------------------------------

@router.get(
    "/experiments",
    response_model=List[ExperimentSummary],
    summary="List all experiments in the catalog",
)
async def list_experiments(env: Optional[str] = Query(None, description="Filter by environment")):
    """
    Returns the immutable experiment catalog.
    Optionally filter by environment: ?env=dev|stage|prod
    """
    if env:
        experiments = catalog.list_for_env(env)
    else:
        experiments = catalog.list_all()

    return [
        ExperimentSummary(
            name=e.name,
            experiment_type=e.experiment_type,
            hypothesis=e.hypothesis,
            blast_radius=e.blast_radius,
            max_duration_sec=e.max_duration_sec,
            abort_error_rate_pct=e.abort_error_rate_pct,
            abort_p95_latency_ms=e.abort_p95_latency_ms,
            rollback_trigger=e.rollback_trigger,
            allowed_envs=sorted(e.allowed_envs),
            requires_compliance=e.requires_compliance,
            description=e.description,
        )
        for e in experiments
    ]


# ---------------------------------------------------------------------------
# POST /chaos/run
# ---------------------------------------------------------------------------

@router.post(
    "/run",
    response_model=RunResponse,
    status_code=202,
    summary="Start a chaos experiment",
)
async def run_experiment(
    request: RunExperimentRequest,
    session=Depends(get_session),
):
    """
    Starts a chaos experiment after safety pre-checks.
    Returns 202 Accepted with run_id; experiment runs asynchronously.
    """
    try:
        runner = ChaosRunner(session=session)
        run_id = await runner.run(
            experiment_name=request.experiment_name,
            env=request.environment.value,
            requester=request.requester,
            compliance_approved=request.compliance_approved,
        )
        logger.info(
            "chaos_api_run_started",
            extra={
                "experiment_id": run_id,
                "experiment": request.experiment_name,
                "env": request.environment,
                "requester": request.requester,
            },
        )
        return RunResponse(
            run_id=run_id,
            experiment_name=request.experiment_name,
            environment=request.environment.value,
            status="running",
            requester=request.requester,
            compliance_approved=request.compliance_approved,
            started_at=None,
            ended_at=None,
            abort_reason=None,
            duration_sec=None,
            message=f"Experiment '{request.experiment_name}' started. run_id={run_id[:8]}",
        )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except EnvironmentGateError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ComplianceGateError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /chaos/stop/{run_id}
# ---------------------------------------------------------------------------

@router.post(
    "/stop/{run_id}",
    response_model=RunResponse,
    summary="Stop a running chaos experiment",
)
async def stop_experiment(
    run_id: str,
    request: StopExperimentRequest,
    session=Depends(get_session),
):
    """
    Issues a graceful stop + rollback for the given run_id.
    """
    try:
        runner = ChaosRunner(session=session)
        message = await runner.stop(run_id=run_id, reason=request.reason)
        return RunResponse(
            run_id=run_id,
            experiment_name="",
            environment="",
            status="aborted",
            requester="api",
            compliance_approved=False,
            started_at=None,
            ended_at=None,
            abort_reason=request.reason,
            duration_sec=None,
            message=message,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET /chaos/history
# ---------------------------------------------------------------------------

@router.get(
    "/history",
    response_model=List[HistoryItem],
    summary="Paginated chaos run history",
)
async def get_history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    env: Optional[str] = Query(None),
    session=Depends(get_session),
):
    """Returns most recent chaos runs, newest first."""
    if session is None:
        return []

    from packages.chaos.models import ChaosRun, Environment

    stmt = select(ChaosRun).order_by(desc(ChaosRun.created_at)).offset(offset).limit(limit)
    if env:
        stmt = stmt.where(ChaosRun.environment == Environment(env))

    result = await session.execute(stmt)
    runs = result.scalars().all()

    return [
        HistoryItem(
            run_id=r.id,
            experiment_name=r.experiment_name,
            environment=r.environment.value,
            status=r.status.value,
            requester=r.requester,
            created_at=r.created_at,
            started_at=r.started_at,
            ended_at=r.ended_at,
            duration_sec=r.duration_sec,
            abort_reason=r.abort_reason,
        )
        for r in runs
    ]


# ---------------------------------------------------------------------------
# GET /chaos/metrics
# ---------------------------------------------------------------------------

@router.get(
    "/metrics",
    response_model=DashboardMetrics,
    summary="Chaos engineering dashboard metrics",
)
async def get_metrics(
    window_days: int = Query(default=30, ge=1, le=365),
    session=Depends(get_session),
):
    """Returns MTTR, auto-recovery rate, rollback frequency, and failed test counts."""
    if session is None:
        return DashboardMetrics(
            window_days=window_days,
            avg_mttr_sec=0.0,
            auto_recovery_rate_pct=0.0,
            rollback_frequency=0,
            failed_resilience_tests=0,
            total_runs=0,
        )

    summary = await metrics_collector.dashboard_summary(session, window_days=window_days)
    return DashboardMetrics(**summary)
