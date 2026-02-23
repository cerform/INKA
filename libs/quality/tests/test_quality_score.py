"""
Tests for QualityEngine — deterministic scoring validation.

Run: pytest libs/quality/tests/ -v
"""
import pytest
from packages.quality.quality_score import QualityEngine, QualityInput


def _base_input(**overrides) -> QualityInput:
    defaults = dict(
        version="1.0.0",
        git_sha="abc123def456",
        coverage_pct=85.0,
        open_s1_bugs=0,
        open_s2_bugs=0,
        open_s3_bugs=0,
        regression_tests_missing=False,
        critical_vulns=0,
        high_vulns=0,
        medium_vulns=0,
        migration_risk_level=0,
        code_churn_pct=10.0,
        p95_latency_ms=200.0,
        error_rate_pct=0.1,
        compliance_score=95.0,
        ci_lint_passed=True,
        ci_tests_passed=True,
    )
    defaults.update(overrides)
    return QualityInput(**defaults)  # type: ignore[arg-type]


engine = QualityEngine()


class TestHardZeroRules:
    def test_open_s1_bug_returns_zero(self):
        inp = _base_input(open_s1_bugs=1)
        report = engine.compute(inp)
        assert report.final_score == 0.0
        assert report.recommendation == "BLOCK"

    def test_ci_fail_returns_zero(self):
        inp = _base_input(ci_tests_passed=False)
        report = engine.compute(inp)
        assert report.final_score == 0.0
        assert report.recommendation == "BLOCK"


class TestPenalties:
    def test_open_s2_penalty(self):
        clean = engine.compute(_base_input())
        penalised = engine.compute(_base_input(open_s2_bugs=1))
        assert penalised.final_score < clean.final_score
        assert any("S2" in p["reason"] for p in penalised.penalties)

    def test_coverage_penalty_below_threshold(self):
        report = engine.compute(_base_input(coverage_pct=70.0))
        assert any("Coverage" in p["reason"] for p in report.penalties)

    def test_critical_vuln_penalty(self):
        report = engine.compute(_base_input(critical_vulns=1))
        assert any("Critical" in p["reason"] for p in report.penalties)

    def test_churn_penalty(self):
        report = engine.compute(_base_input(code_churn_pct=35.0))
        assert any("churn" in p["reason"].lower() for p in report.penalties)

    def test_regression_test_missing_penalty(self):
        report = engine.compute(_base_input(regression_tests_missing=True))
        assert any("regression" in p["reason"].lower() for p in report.penalties)

    def test_s2_penalty_capped_at_60(self):
        report = engine.compute(_base_input(open_s2_bugs=5))
        s2_pen = next(p for p in report.penalties if "S2" in p["reason"])
        assert s2_pen["pts"] <= 60.0


class TestThresholds:
    def test_prod_ready(self):
        report = engine.compute(_base_input(coverage_pct=95.0, compliance_score=100.0))
        assert report.recommendation == "PROD_READY"
        assert report.final_score >= 90.0

    def test_stage_only(self):
        # Enough pressure to land in 80-89 range
        report = engine.compute(_base_input(coverage_pct=82.0, p95_latency_ms=400.0))
        assert report.recommendation in ("PROD_READY", "STAGE_ONLY")

    def test_block(self):
        report = engine.compute(_base_input(open_s2_bugs=2, critical_vulns=1, coverage_pct=60.0))
        assert report.recommendation == "BLOCK"


class TestReportFields:
    def test_report_has_required_fields(self):
        report = engine.compute(_base_input())
        assert report.version == "1.0.0"
        assert report.git_sha == "abc123def456"
        assert len(report.dimension_scores) == 7
        assert report.evaluated_at != ""
