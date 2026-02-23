"""Routes: DORA metrics — compute the four key engineering metrics."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Deployment, PipelineRun, RunStatus
from ..schemas import DORAMetricsResponse

router = APIRouter(prefix="/api/dora", tags=["dora"])

_FREQ_LABELS = [
    (1.0, "Multiple per day"),
    (1 / 1, "Daily"),
    (1 / 7, "Weekly"),
    (1 / 30, "Monthly"),
    (0, "Less than monthly"),
]


def _frequency_label(deploys_per_day: float) -> str:
    for threshold, label in _FREQ_LABELS:
        if deploys_per_day >= threshold:
            return label
    return "Less than monthly"


@router.get("/metrics", response_model=DORAMetricsResponse)
def get_dora_metrics(
    period_days: int = Query(default=30, ge=1, le=365),
    service_id: Optional[str] = None,
    env: Optional[str] = None,
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=period_days)

    dep_q = db.query(Deployment).filter(Deployment.deployed_at >= since)
    if service_id:
        dep_q = dep_q.filter(Deployment.service_id == service_id)
    if env:
        dep_q = dep_q.filter(Deployment.env == env)

    deployments = dep_q.order_by(Deployment.deployed_at.asc()).all()
    total_deployments = len(deployments)
    rollbacks = sum(1 for d in deployments if d.rollback_of is not None)
    failed_deployments = rollbacks  # Rollbacks are our proxy for change failures

    # ── Deployment Frequency ─────────────────────────────────────────────────
    freq = total_deployments / period_days if period_days > 0 else 0.0

    # ── Lead Time (commit → deploy) ──────────────────────────────────────────
    # Join pipeline_runs by image_digest (best-effort)
    lead_times: list[float] = []
    for dep in deployments:
        if dep.image_digest:
            run = db.query(PipelineRun).filter(
                PipelineRun.image_digest == dep.image_digest,
                PipelineRun.status == RunStatus.SUCCESS,
            ).order_by(PipelineRun.finished_at.desc()).first()
            if run and run.started_at and dep.deployed_at:
                delta = (dep.deployed_at - run.started_at).total_seconds() / 3600
                if 0 < delta < 72:  # sanity: ignore > 3 days
                    lead_times.append(delta)

    avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0.0

    # ── MTTR ─────────────────────────────────────────────────────────────────
    # Approximate: time between a rollback and the next successful deploy
    mttr_samples: list[float] = []
    for i, dep in enumerate(deployments):
        if dep.rollback_of and i + 1 < len(deployments):
            next_dep = deployments[i + 1]
            delta_h = (next_dep.deployed_at - dep.deployed_at).total_seconds() / 3600
            if 0 < delta_h < 168:  # sanity: ignore > 1 week
                mttr_samples.append(delta_h)

    avg_mttr = sum(mttr_samples) / len(mttr_samples) if mttr_samples else 0.0

    # ── Change Failure Rate ───────────────────────────────────────────────────
    cfr = rollbacks / total_deployments if total_deployments > 0 else 0.0

    return DORAMetricsResponse(
        period_days=period_days,
        deployment_frequency=round(freq, 4),
        deployment_frequency_label=_frequency_label(freq),
        lead_time_hours=round(avg_lead_time, 2),
        mean_time_to_restore_hours=round(avg_mttr, 2),
        change_failure_rate=round(cfr, 4),
        total_deployments=total_deployments,
        failed_deployments=failed_deployments,
        rollbacks=rollbacks,
    )
