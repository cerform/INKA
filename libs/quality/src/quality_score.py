"""
Quality Score Engine — INKA Admin
==================================

Implements the deterministic weighted scoring algorithm.

FORMULA
-------
  raw_score = Σ (dimension_weight × dimension_raw_score)   [0..100]
  final_score = max(0, raw_score − Σ penalties)

WEIGHTS
-------
  test_coverage  : 20%
  defect_status  : 20%
  security_scan  : 15%
  migration_risk : 10%
  code_stability : 10%
  performance    : 10%
  compliance     : 15%
  ─────────────────
  TOTAL          : 100%

PENALTY MATRIX
--------------
  Open S1 bug           → SCORE = 0  (hard zero)
  Open S2 bug           → -30 per occurrence (cap at -60)
  Coverage < threshold  → -20  (threshold = 80%)
  Critical vuln         → -25 per occurrence (cap at -50)
  High vuln             → -10 per occurrence (cap at -20)
  No regression test    → -15
  High code churn >30%  → -10

THRESHOLDS (deployment gates)
------------------------------
  PROD_READY  : score >= 90
  STAGE_ONLY  : 80 <= score < 90
  BLOCK       : score < 80
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

# ─────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────

WEIGHTS: dict[str, float] = {
    "test_coverage": 0.20,
    "defect_status": 0.20,
    "security_scan": 0.15,
    "migration_risk": 0.10,
    "code_stability": 0.10,
    "performance": 0.10,
    "compliance": 0.15,
}

COVERAGE_THRESHOLD = 80.0        # % — below this triggers -20 penalty
CHURN_THRESHOLD = 30.0           # % — above this triggers -10 penalty
P95_LATENCY_BUDGET_MS = 500.0    # ms — SLA for p95 latency

DEPLOYMENT_THRESHOLDS = {
    "PROD_READY": 90.0,
    "STAGE_ONLY": 80.0,
}


# ─────────────────────────────────────────────────────────
# Input / Output schemas
# ─────────────────────────────────────────────────────────

@dataclass
class QualityInput:
    """All raw metrics required to compute a quality score."""

    # Identity
    version: str
    git_sha: str

    # Test coverage
    coverage_pct: float               # 0–100

    # Defect registry
    open_s1_bugs: int                 # Severity-1 (blocker/critical)
    open_s2_bugs: int                 # Severity-2 (major)
    open_s3_bugs: int = 0             # Severity-3 (minor) — informational
    regression_tests_missing: bool = False  # True if any bug lacks regression test

    # Security scan (trivy / snyk / bandit)
    critical_vulns: int = 0
    high_vulns: int = 0
    medium_vulns: int = 0

    # Migration risk (0=none, 1=low, 2=medium, 3=high)
    migration_risk_level: Literal[0, 1, 2, 3] = 0

    # Code churn (% of lines changed relative to previous release)
    code_churn_pct: float = 0.0

    # Performance benchmarks
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate_pct: float = 0.0       # % of 5xx responses

    # Compliance score (0–100), fed from Compliance Agent
    compliance_score: float = 100.0

    # CI pipeline status
    ci_lint_passed: bool = True
    ci_tests_passed: bool = True


@dataclass
class QualityReport:
    """Fully computed quality report for a release."""

    # Identity
    version: str
    git_sha: str
    evaluated_at: str

    # Raw inputs (reflected for transparency)
    coverage_pct: float
    open_bugs: int           # S1
    open_s2: int
    critical_vulns: int
    high_vulns: int
    migration_risk: str
    code_churn_pct: float
    p95_latency_ms: float
    compliance_score: float

    # Scoring
    dimension_scores: dict[str, float]
    penalties: list[dict[str, Any]]
    raw_score: float
    final_score: float

    recommendation: Literal["PROD_READY", "STAGE_ONLY", "BLOCK"]


# ─────────────────────────────────────────────────────────
# Scoring helpers
# ─────────────────────────────────────────────────────────

_MIGRATION_LABELS = {0: "NONE", 1: "LOW", 2: "MEDIUM", 3: "HIGH"}


def _score_coverage(pct: float) -> float:
    """Linear 0–100 within range [50%, 100%]."""
    return max(0.0, min(100.0, (pct - 50.0) * 2.0))


def _score_defects(s1: int, s2: int, s3: int) -> float:
    """Penalise open bugs; S1 zeroes this dimension entirely."""
    if s1 > 0:
        return 0.0
    base = 100.0
    base -= s2 * 25.0      # each S2 costs 25 pts in this dimension
    base -= s3 * 5.0       # each S3 costs 5 pts
    return max(0.0, base)


def _score_security(critical: int, high: int, medium: int) -> float:
    base = 100.0
    base -= critical * 30.0
    base -= high * 15.0
    base -= medium * 5.0
    return max(0.0, base)


def _score_migration(risk_level: int) -> float:
    mapping = {0: 100.0, 1: 80.0, 2: 50.0, 3: 10.0}
    return mapping[risk_level]


def _score_churn(pct: float) -> float:
    """Full marks up to 15%, linear decay to zero at 60%."""
    if pct <= 15.0:
        return 100.0
    if pct >= 60.0:
        return 0.0
    return 100.0 * (1.0 - (pct - 15.0) / 45.0)


def _score_performance(p95_ms: float, error_rate: float) -> float:
    """Score based on p95 latency and error rate."""
    latency_score = max(0.0, 100.0 - (p95_ms / P95_LATENCY_BUDGET_MS) * 50.0)
    error_score = max(0.0, 100.0 - error_rate * 20.0)
    return (latency_score + error_score) / 2.0


# ─────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────

class QualityEngine:
    """Deterministic quality scoring engine."""

    def compute(self, inp: QualityInput) -> QualityReport:
        penalties: list[dict[str, Any]] = []

        # ── 1. Compute raw dimension scores (0–100 each) ──────────────────────
        dim_raw: dict[str, float] = {
            "test_coverage": _score_coverage(inp.coverage_pct),
            "defect_status": _score_defects(inp.open_s1_bugs, inp.open_s2_bugs, inp.open_s3_bugs),
            "security_scan": _score_security(inp.critical_vulns, inp.high_vulns, inp.medium_vulns),
            "migration_risk": _score_migration(inp.migration_risk_level),
            "code_stability": _score_churn(inp.code_churn_pct),
            "performance": _score_performance(inp.p95_latency_ms, inp.error_rate_pct),
            "compliance": inp.compliance_score,
        }

        # ── 2. Weighted raw score ─────────────────────────────────────────────
        raw_score = sum(dim_raw[k] * WEIGHTS[k] for k in WEIGHTS) * 1.0

        # ── 3. CI gate check (CI failure is a hard blocker, not a dimension) ──
        if not inp.ci_tests_passed:
            penalties.append({"reason": "CI tests failed", "pts": raw_score})
            return self._build_report(inp, dim_raw, penalties, raw_score, 0.0)
        if not inp.ci_lint_passed:
            penalties.append({"reason": "CI lint failed", "pts": 10})

        # ── 4. Hard-zero rule: any open S1 → score = 0 ───────────────────────
        if inp.open_s1_bugs > 0:
            penalties.append(
                {"reason": f"Open S1 bug(s): {inp.open_s1_bugs}", "pts": raw_score}
            )
            return self._build_report(inp, dim_raw, penalties, raw_score, 0.0)

        # ── 5. Cumulative penalties ───────────────────────────────────────────
        penalty_pts: float = 0.0

        # S2 open bugs: -30 each, capped at -60
        if inp.open_s2_bugs > 0:
            s2_penalty = min(inp.open_s2_bugs * 30.0, 60.0)
            penalties.append({"reason": f"Open S2 bug(s): {inp.open_s2_bugs}", "pts": s2_penalty})
            penalty_pts += s2_penalty

        # Coverage below threshold
        if inp.coverage_pct < COVERAGE_THRESHOLD:
            penalties.append({"reason": f"Coverage {inp.coverage_pct:.1f}% < {COVERAGE_THRESHOLD}%", "pts": 20})
            penalty_pts += 20

        # Critical vulns: -25 each, capped at -50
        if inp.critical_vulns > 0:
            v_penalty = min(inp.critical_vulns * 25.0, 50.0)
            penalties.append({"reason": f"Critical vuln(s): {inp.critical_vulns}", "pts": v_penalty})
            penalty_pts += v_penalty

        # High vulns: -10 each, capped at -20
        if inp.high_vulns > 0:
            h_penalty = min(inp.high_vulns * 10.0, 20.0)
            penalties.append({"reason": f"High vuln(s): {inp.high_vulns}", "pts": h_penalty})
            penalty_pts += h_penalty

        # Missing regression tests
        if inp.regression_tests_missing:
            penalties.append({"reason": "Missing regression test for bug fix", "pts": 15})
            penalty_pts += 15

        # High code churn
        if inp.code_churn_pct > CHURN_THRESHOLD:
            penalties.append({"reason": f"Code churn {inp.code_churn_pct:.0f}% > {CHURN_THRESHOLD:.0f}%", "pts": 10})
            penalty_pts += 10

        # CI lint failure (accumulated above)
        for p in penalties:
            if "lint" in p["reason"]:
                penalty_pts += float(p["pts"])


        final_score = max(0.0, raw_score - penalty_pts)

        return self._build_report(inp, dim_raw, penalties, raw_score, final_score)

    # ─────────────────────────────────────────────────────
    @staticmethod
    def _build_report(
        inp: QualityInput,
        dim_raw: dict[str, float],
        penalties: list[dict[str, Any]],
        raw_score: float,
        final_score: float,
    ) -> QualityReport:
        # Weighted dimension contribution scores for display (max contribution)
        dim_scores = {k: float(f"{dim_raw[k] * WEIGHTS[k]:.2f}") for k in WEIGHTS}

        if final_score >= DEPLOYMENT_THRESHOLDS["PROD_READY"]:
            recommendation: Literal["PROD_READY", "STAGE_ONLY", "BLOCK"] = "PROD_READY"
        elif final_score >= DEPLOYMENT_THRESHOLDS["STAGE_ONLY"]:
            recommendation = "STAGE_ONLY"
        else:
            recommendation = "BLOCK"

        return QualityReport(
            version=inp.version,
            git_sha=inp.git_sha,
            evaluated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            coverage_pct=inp.coverage_pct,
            open_bugs=inp.open_s1_bugs,
            open_s2=inp.open_s2_bugs,
            critical_vulns=inp.critical_vulns,
            high_vulns=inp.high_vulns,
            migration_risk=_MIGRATION_LABELS[inp.migration_risk_level],
            code_churn_pct=inp.code_churn_pct,
            p95_latency_ms=inp.p95_latency_ms,
            compliance_score=inp.compliance_score,
            dimension_scores=dim_scores,
            penalties=penalties,
            raw_score=float(f"{raw_score:.2f}"),
            final_score=float(f"{final_score:.2f}"),
            recommendation=recommendation,
        )
