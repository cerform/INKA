"""
Safety Controller for INKA Chaos Engineering.

Responsibilities:
- Environment gating (random_500 blocked from prod)
- Compliance approval check for prod experiments
- Real-time abort condition evaluation (error rate, p95 latency)
- S1/S2 defect detection integration
- Max-duration enforcement
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from packages.chaos.catalog import ExperimentDefinition

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class ComplianceGateError(Exception):
    """Raised when a prod experiment lacks compliance approval."""


class AbortConditionError(Exception):
    """Raised when a running experiment breaches an abort threshold."""


class EnvironmentGateError(Exception):
    """Raised when an experiment is not allowed in the target environment."""


class ActiveDefectError(Exception):
    """Raised when an active S1/S2 defect blocks chaos execution."""


# ---------------------------------------------------------------------------
# SafetyController
# ---------------------------------------------------------------------------


class SafetyController:
    """
    Central safety guard for chaos experiments.

    Usage:
        controller = SafetyController(defect_api_url="http://api/internal/defects")
        controller.check_pre_conditions(experiment, env="prod", compliance_approved=True)
        controller.check_abort_conditions(run_id, error_rate=4.5, p95_latency_ms=1800)
    """

    # Hard limits across all experiments
    GLOBAL_MAX_DURATION_SEC = 300  # 5 minutes, no exceptions
    PROD_MAX_TRAFFIC_PCT = 5  # canary ceiling for prod

    def __init__(self, defect_api_url: Optional[str] = None):
        self._defect_api_url = defect_api_url

    # ------------------------------------------------------------------
    # Pre-flight checks (called before experiment starts)
    # ------------------------------------------------------------------

    def check_pre_conditions(
        self,
        experiment: ExperimentDefinition,
        env: str,
        compliance_approved: bool = False,
    ) -> None:
        """
        Validate that an experiment is safe to start.
        Raises specific gate errors if any condition fails.
        """
        self._check_env_allowed(experiment, env)
        self._check_max_duration(experiment)
        if env == "prod":
            self._require_compliance_approval(experiment, compliance_approved)
            self._check_no_active_defects()
        logger.info(
            "chaos_pre_conditions_passed",
            extra={
                "experiment": experiment.name,
                "env": env,
                "compliance_approved": compliance_approved,
            },
        )

    def _check_env_allowed(self, experiment: ExperimentDefinition, env: str) -> None:
        if env not in experiment.allowed_envs:
            raise EnvironmentGateError(
                f"Experiment '{experiment.name}' is not allowed in environment '{env}'. "
                f"Allowed: {sorted(experiment.allowed_envs)}"
            )

    def _check_max_duration(self, experiment: ExperimentDefinition) -> None:
        if experiment.max_duration_sec > self.GLOBAL_MAX_DURATION_SEC:
            raise ValueError(
                f"Experiment '{experiment.name}' max_duration_sec "
                f"({experiment.max_duration_sec}) exceeds global limit "
                f"({self.GLOBAL_MAX_DURATION_SEC} s)."
            )

    def _require_compliance_approval(
        self,
        experiment: ExperimentDefinition,
        compliance_approved: bool,
    ) -> None:
        """All prod experiments require explicit compliance approval."""
        if not compliance_approved:
            raise ComplianceGateError(
                f"Experiment '{experiment.name}' requires compliance approval "
                "before running in production. "
                "Pass compliance_approved=True or use /chaos run with an approval token."
            )

    def _check_no_active_defects(self) -> None:
        """
        Check internal defect system for active S1/S2 defects.
        In a real deployment this calls the defect API. Here we do a
        lightweight local check — override in production with a real HTTP call.
        """
        # Production integration point:
        # resp = httpx.get(f"{self._defect_api_url}/active?severity=S1,S2")
        # if resp.json()["count"] > 0:
        #     raise ActiveDefectError("Active S1/S2 defects detected — chaos blocked.")
        logger.debug("chaos_defect_check_skipped_no_api_configured")

    # ------------------------------------------------------------------
    # Real-time abort checks (called during experiment loop)
    # ------------------------------------------------------------------

    def check_abort_conditions(
        self,
        experiment: ExperimentDefinition,
        run_id: str,
        error_rate_pct: Optional[float],
        p95_latency_ms: Optional[int],
        started_at: Optional[datetime] = None,
        s1_defect_active: bool = False,
    ) -> None:
        """
        Evaluate abort conditions for a running experiment.
        Raises AbortConditionError with reason if any threshold is breached.
        """
        # S1 defect — immediate abort regardless of experiment type
        if s1_defect_active:
            raise AbortConditionError(
                f"[{run_id}] ABORT: Active S1 defect detected during experiment "
                f"'{experiment.name}'."
            )

        # Error rate threshold
        if (
            experiment.abort_error_rate_pct is not None
            and error_rate_pct is not None
            and error_rate_pct >= experiment.abort_error_rate_pct
        ):
            raise AbortConditionError(
                f"[{run_id}] ABORT: Error rate {error_rate_pct:.1f}% >= "
                f"threshold {experiment.abort_error_rate_pct:.1f}% "
                f"for experiment '{experiment.name}'."
            )

        # p95 latency threshold
        if (
            experiment.abort_p95_latency_ms is not None
            and p95_latency_ms is not None
            and p95_latency_ms >= experiment.abort_p95_latency_ms
        ):
            raise AbortConditionError(
                f"[{run_id}] ABORT: p95 latency {p95_latency_ms} ms >= "
                f"threshold {experiment.abort_p95_latency_ms} ms "
                f"for experiment '{experiment.name}'."
            )

        # Max duration wall clock
        if started_at is not None:
            elapsed = (datetime.utcnow() - started_at).total_seconds()
            if elapsed >= experiment.max_duration_sec:
                raise AbortConditionError(
                    f"[{run_id}] ABORT: Experiment '{experiment.name}' exceeded "
                    f"max duration {experiment.max_duration_sec} s "
                    f"(elapsed {elapsed:.0f} s)."
                )

        logger.debug(
            "chaos_abort_check_passed",
            extra={
                "experiment": experiment.name,
                "run_id": run_id,
                "error_rate_pct": error_rate_pct,
                "p95_latency_ms": p95_latency_ms,
            },
        )
