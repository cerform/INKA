"""Unit tests for SafetyController."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from packages.chaos.catalog import EXPERIMENTS, ExperimentDefinition
from packages.chaos.safety import (
    SafetyController,
    ComplianceGateError,
    EnvironmentGateError,
    AbortConditionError,
)


@pytest.fixture
def controller():
    return SafetyController()


@pytest.fixture
def latency_exp():
    return EXPERIMENTS["api_latency_injection"]


@pytest.fixture
def random_500_exp():
    return EXPERIMENTS["random_500_injection"]


# ── pre-conditions ──────────────────────────────────────────────────────────

class TestEnvGate:
    def test_allowed_env_passes(self, controller, latency_exp):
        """api_latency_injection is allowed in all envs."""
        controller.check_pre_conditions(latency_exp, env="dev")
        controller.check_pre_conditions(latency_exp, env="stage")
        controller.check_pre_conditions(latency_exp, env="prod", compliance_approved=True)

    def test_random_500_blocked_in_prod(self, controller, random_500_exp):
        """random_500_injection must be blocked in prod at env gate level."""
        with pytest.raises(EnvironmentGateError, match="not allowed in environment 'prod'"):
            controller.check_pre_conditions(random_500_exp, env="prod")

    def test_random_500_allowed_in_dev(self, controller, random_500_exp):
        controller.check_pre_conditions(random_500_exp, env="dev")

    def test_unknown_env_raises(self, controller, latency_exp):
        with pytest.raises(EnvironmentGateError):
            controller.check_pre_conditions(latency_exp, env="unknown_env")


class TestComplianceGate:
    def test_prod_without_compliance_raises(self, controller, latency_exp):
        with pytest.raises(ComplianceGateError, match="compliance approval"):
            controller.check_pre_conditions(latency_exp, env="prod", compliance_approved=False)

    def test_prod_with_compliance_passes(self, controller, latency_exp):
        controller.check_pre_conditions(latency_exp, env="prod", compliance_approved=True)

    def test_dev_without_compliance_passes(self, controller, latency_exp):
        controller.check_pre_conditions(latency_exp, env="dev", compliance_approved=False)


class TestMaxDuration:
    def test_exceeds_global_limit_raises(self, controller):
        bad_exp = ExperimentDefinition(
            name="bad_exp",
            experiment_type="api_latency",
            hypothesis="test",
            blast_radius="none",
            max_duration_sec=999,  # > 300
            abort_error_rate_pct=None,
            abort_p95_latency_ms=None,
            rollback_trigger="none",
            allowed_envs=frozenset({"dev"}),
        )
        with pytest.raises(ValueError, match="exceeds global limit"):
            controller.check_pre_conditions(bad_exp, env="dev")


# ── abort conditions ─────────────────────────────────────────────────────────

class TestAbortConditions:
    def test_error_rate_breach_raises(self, controller, latency_exp):
        with pytest.raises(AbortConditionError, match="Error rate"):
            controller.check_abort_conditions(
                experiment=latency_exp,
                run_id="test-run-123",
                error_rate_pct=15.0,  # threshold is 10.0
                p95_latency_ms=500,
            )

    def test_p95_breach_raises(self, controller, latency_exp):
        with pytest.raises(AbortConditionError, match="p95 latency"):
            controller.check_abort_conditions(
                experiment=latency_exp,
                run_id="test-run-123",
                error_rate_pct=1.0,
                p95_latency_ms=2500,  # threshold is 2000
            )

    def test_s1_defect_triggers_abort(self, controller, latency_exp):
        with pytest.raises(AbortConditionError, match="S1 defect"):
            controller.check_abort_conditions(
                experiment=latency_exp,
                run_id="test-run-123",
                error_rate_pct=0.0,
                p95_latency_ms=100,
                s1_defect_active=True,
            )

    def test_max_duration_breach_raises(self, controller, latency_exp):
        # started 10 minutes ago (experiment max is 5 min = 300 s)
        old_start = datetime.utcnow() - timedelta(seconds=400)
        with pytest.raises(AbortConditionError, match="exceeded max duration"):
            controller.check_abort_conditions(
                experiment=latency_exp,
                run_id="test-run-123",
                error_rate_pct=0.0,
                p95_latency_ms=100,
                started_at=old_start,
            )

    def test_within_thresholds_passes(self, controller, latency_exp):
        controller.check_abort_conditions(
            experiment=latency_exp,
            run_id="test-run-123",
            error_rate_pct=2.0,
            p95_latency_ms=800,
        )


# ── catalog completeness ─────────────────────────────────────────────────────

class TestCatalogCompleteness:
    def test_all_experiments_have_required_fields(self):
        required_fields = [
            "name", "experiment_type", "hypothesis", "blast_radius",
            "max_duration_sec", "rollback_trigger", "allowed_envs",
        ]
        for name, exp in EXPERIMENTS.items():
            for field in required_fields:
                assert getattr(exp, field), f"Experiment '{name}' missing '{field}'"

    def test_all_experiments_within_global_max(self):
        for name, exp in EXPERIMENTS.items():
            assert exp.max_duration_sec <= 300, (
                f"Experiment '{name}' max_duration_sec={exp.max_duration_sec} exceeds 300 s"
            )

    def test_catalog_has_exactly_9_experiments(self):
        assert len(EXPERIMENTS) == 9

    def test_random_500_not_allowed_in_prod(self):
        exp = EXPERIMENTS["random_500_injection"]
        assert "prod" not in exp.allowed_envs

    def test_high_blast_radius_requires_compliance(self):
        """Experiments that can impact prod infra must require compliance."""
        infra_experiments = {"cloud_run_instance_kill", "secret_rotation_simulation"}
        for name in infra_experiments:
            exp = EXPERIMENTS[name]
            assert exp.requires_compliance is True, (
                f"Experiment '{name}' impacts infra but requires_compliance=False"
            )
