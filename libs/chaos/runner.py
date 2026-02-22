"""
ChaosRunner — Orchestrates chaos experiment lifecycle.

Lifecycle:
  PENDING → RUNNING → (abort check loop) → COMPLETED | ABORTED | ROLLED_BACK

The runner:
1. Validates pre-conditions via SafetyController
2. Persists a ChaosRun record (all actions are auditable)
3. Executes the experiment (delegates to experiment-specific adapters)
4. Polls metrics every POLL_INTERVAL_SEC and checks abort conditions
5. On abort: triggers RollbackManager and marks run ROLLED_BACK
6. Emits structured JSON logs with experiment_id on every line
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from libs.chaos.catalog import ExperimentCatalog, ExperimentDefinition
from libs.chaos.safety import SafetyController, AbortConditionError, ComplianceGateError, EnvironmentGateError
from libs.chaos.rollback import RollbackManager
from libs.chaos.metrics import ChaosMetricsCollector

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 15  # how often to sample metrics during run


# ---------------------------------------------------------------------------
# Lightweight metric sampler (production: replace with Cloud Monitoring query)
# ---------------------------------------------------------------------------

async def _sample_metrics(experiment_name: str) -> dict:
    """
    Sample real-time metrics.
    Production: query Cloud Monitoring or internal /metrics endpoint.
    Dev/test: returns stub values.
    """
    # In production:
    # resp = await httpx.AsyncClient().get("http://localhost:8000/internal/metrics")
    # return resp.json()
    await asyncio.sleep(0.05)
    return {"error_rate_pct": 0.0, "p95_latency_ms": 200, "active_connections": 10}


async def _start_experiment(experiment: ExperimentDefinition, env: str) -> None:
    """
    Dispatch experiment start to the correct adapter.
    Production: call internal API or gcloud CLI.
    """
    logger.info(
        "chaos_experiment_started",
        extra={"experiment": experiment.name, "env": env, "type": experiment.experiment_type},
    )
    # Each type has its own adapter in production.
    # For now: log the action and simulate startup delay.
    await asyncio.sleep(0.2)


async def _stop_experiment(experiment: ExperimentDefinition) -> None:
    """Signal the experiment to stop its injection/load."""
    logger.info("chaos_experiment_stopping", extra={"experiment": experiment.name})
    await asyncio.sleep(0.1)


# ---------------------------------------------------------------------------
# ChaosRunner
# ---------------------------------------------------------------------------


class ChaosRunner:
    """
    Main orchestrator for chaos experiments.

    Usage:
        runner = ChaosRunner(session=db_session)
        run_id = await runner.run(
            experiment_name="api_latency_injection",
            env="stage",
            requester="telegram:@admin",
            compliance_approved=False,
        )
        await runner.stop(run_id, reason="manual stop")
    """

    def __init__(self, session=None):
        self._session = session
        self._catalog = ExperimentCatalog()
        self._safety = SafetyController()
        self._rollback = RollbackManager()
        self._metrics = ChaosMetricsCollector()
        # In-memory registry of active runs (run_id → asyncio.Task)
        self._active_tasks: dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(
        self,
        experiment_name: str,
        env: str,
        requester: str,
        compliance_approved: bool = False,
    ) -> str:
        """
        Start a chaos experiment.
        Returns the run_id on success.
        Raises safety gate errors synchronously before the run record is created.
        """
        experiment = self._catalog.get(experiment_name)

        # Pre-flight safety check (synchronous — raises on failure)
        self._safety.check_pre_conditions(experiment, env, compliance_approved)

        run_id = str(uuid.uuid4())
        logger.info(
            "chaos_run_created",
            extra={
                "experiment_id": run_id,
                "experiment": experiment.name,
                "env": env,
                "requester": requester,
                "compliance_approved": compliance_approved,
            },
        )

        if self._session:
            await self._persist_run_start(run_id, experiment, env, requester, compliance_approved)

        # Launch background task
        task = asyncio.create_task(
            self._execute_loop(run_id, experiment, env),
            name=f"chaos-{run_id[:8]}",
        )
        self._active_tasks[run_id] = task
        task.add_done_callback(lambda t: self._active_tasks.pop(run_id, None))
        return run_id

    async def stop(self, run_id: str, reason: str = "manual stop") -> str:
        """
        Abort a running experiment by run_id.
        Triggers rollback and returns result message.
        """
        task = self._active_tasks.get(run_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, AbortConditionError):
                pass

        logger.info(
            "chaos_run_stopped",
            extra={"run_id": run_id, "reason": reason},
        )
        if self._session:
            await self._persist_run_end(run_id, "aborted", abort_reason=reason)

        return f"Experiment {run_id[:8]} stopped: {reason}"

    # ------------------------------------------------------------------
    # Internal execution loop
    # ------------------------------------------------------------------

    async def _execute_loop(
        self,
        run_id: str,
        experiment: ExperimentDefinition,
        env: str,
    ) -> None:
        started_at = datetime.utcnow()

        if self._session:
            await self._persist_run_status(run_id, "running", started_at)

        try:
            await _start_experiment(experiment, env)

            # Poll until max_duration or abort condition
            elapsed = 0.0
            while elapsed < experiment.max_duration_sec:
                await asyncio.sleep(POLL_INTERVAL_SEC)
                elapsed = (datetime.utcnow() - started_at).total_seconds()

                metrics_data = await _sample_metrics(experiment.name)
                error_rate = metrics_data.get("error_rate_pct")
                p95 = metrics_data.get("p95_latency_ms")

                if self._session:
                    await self._metrics.record_snapshot(
                        self._session,
                        run_id,
                        error_rate_pct=error_rate,
                        p95_latency_ms=p95,
                        active_connections=metrics_data.get("active_connections"),
                    )

                # Safety check — raises AbortConditionError on breach
                self._safety.check_abort_conditions(
                    experiment=experiment,
                    run_id=run_id,
                    error_rate_pct=error_rate,
                    p95_latency_ms=p95,
                    started_at=started_at,
                )

            # Normal completion
            await _stop_experiment(experiment)
            logger.info(
                "chaos_run_completed",
                extra={"experiment_id": run_id, "experiment": experiment.name, "env": env},
            )
            if self._session:
                await self._persist_run_end(run_id, "completed")

        except AbortConditionError as exc:
            logger.warning(
                "chaos_run_aborted",
                extra={"experiment_id": run_id, "reason": str(exc)},
            )
            await self._do_rollback(run_id, experiment, reason=str(exc))

        except asyncio.CancelledError:
            logger.warning(
                "chaos_run_cancelled",
                extra={"experiment_id": run_id},
            )
            await self._do_rollback(run_id, experiment, reason="Task cancelled externally")
            raise

    async def _do_rollback(
        self,
        run_id: str,
        experiment: ExperimentDefinition,
        reason: str,
    ) -> None:
        try:
            result = await self._rollback.rollback(run_id, experiment.experiment_type)
            logger.info(
                "chaos_rollback_result",
                extra={"run_id": run_id, "result": result},
            )
            if self._session:
                await self._persist_run_end(run_id, "rolled_back", abort_reason=reason)
        except Exception as rollback_exc:
            logger.error(
                "chaos_rollback_failed",
                extra={"run_id": run_id, "error": str(rollback_exc)},
            )
            if self._session:
                await self._persist_run_end(run_id, "failed", abort_reason=f"Rollback failed: {rollback_exc}")

    # ------------------------------------------------------------------
    # DB persistence helpers
    # ------------------------------------------------------------------

    async def _persist_run_start(
        self,
        run_id: str,
        experiment: ExperimentDefinition,
        env: str,
        requester: str,
        compliance_approved: bool,
    ) -> None:
        from libs.chaos.models import ChaosRun, RunStatus, Environment

        run = ChaosRun(
            id=uuid.UUID(run_id),
            experiment_name=experiment.name,
            environment=Environment(env),
            status=RunStatus.PENDING,
            requester=requester,
            compliance_approved=compliance_approved,
        )
        self._session.add(run)
        await self._session.flush()

    async def _persist_run_status(self, run_id: str, status: str, started_at: datetime) -> None:
        from sqlalchemy import update
        from libs.chaos.models import ChaosRun, RunStatus
        import uuid as _uuid

        await self._session.execute(
            update(ChaosRun)
            .where(ChaosRun.id == _uuid.UUID(run_id))
            .values(status=RunStatus(status), started_at=started_at)
        )
        await self._session.flush()

    async def _persist_run_end(
        self,
        run_id: str,
        status: str,
        abort_reason: Optional[str] = None,
    ) -> None:
        from sqlalchemy import update
        from libs.chaos.models import ChaosRun, RunStatus
        import uuid as _uuid

        await self._session.execute(
            update(ChaosRun)
            .where(ChaosRun.id == _uuid.UUID(run_id))
            .values(
                status=RunStatus(status),
                ended_at=datetime.utcnow(),
                abort_reason=abort_reason,
            )
        )
        await self._session.commit()
