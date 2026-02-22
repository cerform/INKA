"""
Chaos Metrics Collector for INKA Admin.

Collects point-in-time snapshots during chaos runs and computes:
- MTTR (Mean Time To Recovery)
- Auto-recovery rate (% of experiments that recovered without manual rollback)
- Rollback frequency
- Failed resilience test count
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class ChaosMetricsCollector:
    """
    Records and aggregates chaos experiment metrics.

    Designed to work with any async SQLAlchemy session.
    Pass `session` at call time to keep this class session-agnostic.

    Usage:
        collector = ChaosMetricsCollector()
        await collector.record_snapshot(session, run_id, error_rate=2.1, p95_latency_ms=450)
        mttr = await collector.compute_mttr(session, run_id)
    """

    async def record_snapshot(
        self,
        session,
        run_id: UUID,
        error_rate_pct: Optional[float] = None,
        p95_latency_ms: Optional[int] = None,
        active_connections: Optional[int] = None,
        auto_recovered: Optional[bool] = None,
    ) -> None:
        """Write a metric snapshot for an in-progress chaos run."""
        from libs.chaos.models import ChaosMetric  # avoid circular import

        metric = ChaosMetric(
            run_id=run_id,
            error_rate_pct=error_rate_pct,
            p95_latency_ms=p95_latency_ms,
            active_connections=active_connections,
            auto_recovered=auto_recovered,
            recorded_at=datetime.utcnow(),
        )
        session.add(metric)
        await session.flush()
        logger.debug(
            "chaos_metric_recorded",
            extra={
                "run_id": str(run_id),
                "error_rate_pct": error_rate_pct,
                "p95_latency_ms": p95_latency_ms,
            },
        )

    async def compute_mttr(self, session, run_id: UUID) -> Optional[float]:
        """
        Return MTTR in seconds for a completed/rolled-back run.
        MTTR = ended_at - started_at for that run (time to restore healthy state).
        Returns None if run is still in progress.
        """
        from sqlalchemy import select
        from libs.chaos.models import ChaosRun, RunStatus

        result = await session.execute(
            select(ChaosRun).where(ChaosRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if run is None or run.started_at is None or run.ended_at is None:
            return None
        mttr = (run.ended_at - run.started_at).total_seconds()
        logger.info(
            "chaos_mttr_computed",
            extra={"run_id": str(run_id), "mttr_sec": mttr},
        )
        return mttr

    async def compute_auto_recovery_rate(
        self, session, window_days: int = 30
    ) -> float:
        """
        Returns the percentage of completed runs that auto-recovered
        (i.e., status == COMPLETED without manual rollback) in the given window.
        """
        from sqlalchemy import select, func
        from libs.chaos.models import ChaosRun, ChaosMetric, RunStatus

        since = datetime.utcnow() - timedelta(days=window_days)

        # Total runs in window
        total_result = await session.execute(
            select(func.count(ChaosRun.id)).where(
                ChaosRun.created_at >= since,
                ChaosRun.status.in_([RunStatus.COMPLETED, RunStatus.ROLLED_BACK]),
            )
        )
        total = total_result.scalar() or 0
        if total == 0:
            return 0.0

        # Auto-recovered = COMPLETED (no rollback needed)
        recovered_result = await session.execute(
            select(func.count(ChaosRun.id)).where(
                ChaosRun.created_at >= since,
                ChaosRun.status == RunStatus.COMPLETED,
            )
        )
        recovered = recovered_result.scalar() or 0
        rate = (recovered / total) * 100.0
        logger.info(
            "chaos_auto_recovery_rate",
            extra={"window_days": window_days, "rate_pct": rate, "recovered": recovered, "total": total},
        )
        return rate

    async def rollback_frequency(self, session, window_days: int = 30) -> int:
        """Count externally triggered rollbacks in the given time window."""
        from sqlalchemy import select, func
        from libs.chaos.models import ChaosRun, RunStatus

        since = datetime.utcnow() - timedelta(days=window_days)
        result = await session.execute(
            select(func.count(ChaosRun.id)).where(
                ChaosRun.created_at >= since,
                ChaosRun.status == RunStatus.ROLLED_BACK,
            )
        )
        count = result.scalar() or 0
        logger.info(
            "chaos_rollback_frequency",
            extra={"window_days": window_days, "rollbacks": count},
        )
        return count

    async def failed_resilience_tests(self, session, window_days: int = 30) -> int:
        """Count aborted/failed runs (experiment exposed real weaknesses)."""
        from sqlalchemy import select, func
        from libs.chaos.models import ChaosRun, RunStatus

        since = datetime.utcnow() - timedelta(days=window_days)
        result = await session.execute(
            select(func.count(ChaosRun.id)).where(
                ChaosRun.created_at >= since,
                ChaosRun.status.in_([RunStatus.ABORTED, RunStatus.FAILED]),
            )
        )
        count = result.scalar() or 0
        return count

    async def dashboard_summary(self, session, window_days: int = 30) -> dict:
        """Return all key metrics as a single dict for dashboards/Telegram."""
        mttr_list = []

        from sqlalchemy import select
        from libs.chaos.models import ChaosRun, RunStatus

        since = datetime.utcnow() - timedelta(days=window_days)
        runs_result = await session.execute(
            select(ChaosRun).where(
                ChaosRun.created_at >= since,
                ChaosRun.status.in_([RunStatus.COMPLETED, RunStatus.ROLLED_BACK, RunStatus.ABORTED]),
            )
        )
        runs = runs_result.scalars().all()

        for run in runs:
            if run.started_at and run.ended_at:
                mttr_list.append((run.ended_at - run.started_at).total_seconds())

        avg_mttr = sum(mttr_list) / len(mttr_list) if mttr_list else 0.0

        return {
            "window_days": window_days,
            "avg_mttr_sec": round(avg_mttr, 1),
            "auto_recovery_rate_pct": round(
                await self.compute_auto_recovery_rate(session, window_days), 1
            ),
            "rollback_frequency": await self.rollback_frequency(session, window_days),
            "failed_resilience_tests": await self.failed_resilience_tests(session, window_days),
            "total_runs": len(runs),
        }
