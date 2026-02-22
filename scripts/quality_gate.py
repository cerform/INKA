#!/usr/bin/env python3
"""
CI Quality Gate Script — INKA Admin
=====================================
Runs during CI (GitHub Actions / Cloud Build) after tests + scans.
Exits non-zero if the quality score fails the deployment gate.

Usage:
  python scripts/quality_gate.py --target stage  # gate: 80
  python scripts/quality_gate.py --target prod    # gate: 90
  python scripts/quality_gate.py --version 1.2.3  # override version

Environment variables consumed:
  QUALITY_REGISTRY_PATH   Path to quality_registry.json
  GITHUB_SHA              Injected by GitHub Actions
  COVERAGE_PCT            From pytest-cov (e.g. exported by CI step)
  OPEN_S1_BUGS            From defect tracker API / 0 default
  OPEN_S2_BUGS            From defect tracker API / 0 default
  CRITICAL_VULNS          From Trivy/Snyk JSON output / 0 default
  HIGH_VULNS              From Trivy/Snyk JSON output / 0 default
  MIGRATION_RISK_LEVEL    0-3 / 0 default
  CODE_CHURN_PCT          From git diff stats / 0 default
  P95_LATENCY_MS          From benchmark run / 0 default
  ERROR_RATE_PCT          From benchmark run / 0 default
  COMPLIANCE_SCORE        From Compliance Agent / 100 default
  REGRESSION_TESTS_MISS   true/false / false default
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone

# Allow running from repo root without install
sys.path.insert(0, os.getcwd())

from libs.quality.src.quality_score import QualityEngine, QualityInput, QualityReport, DEPLOYMENT_THRESHOLDS

# ─────────────────────────────────────────────────────────
# Deployment gates
# ─────────────────────────────────────────────────────────

GATE: dict[str, float] = {
    "stage": DEPLOYMENT_THRESHOLDS["STAGE_ONLY"],   # 80
    "prod": DEPLOYMENT_THRESHOLDS["PROD_READY"],    # 90
}


def _env_float(name: str, default: float = 0.0) -> float:
    return float(os.getenv(name, str(default)))


def _env_int(name: str, default: int = 0) -> int:
    return int(os.getenv(name, str(default)))


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes")


def collect_input(version: str) -> QualityInput:
    git_sha = os.getenv("GITHUB_SHA", os.getenv("COMMIT_SHA", "unknown"))
    return QualityInput(
        version=version,
        git_sha=git_sha,
        coverage_pct=_env_float("COVERAGE_PCT", 0.0),
        open_s1_bugs=_env_int("OPEN_S1_BUGS", 0),
        open_s2_bugs=_env_int("OPEN_S2_BUGS", 0),
        open_s3_bugs=_env_int("OPEN_S3_BUGS", 0),
        regression_tests_missing=_env_bool("REGRESSION_TESTS_MISS", False),
        critical_vulns=_env_int("CRITICAL_VULNS", 0),
        high_vulns=_env_int("HIGH_VULNS", 0),
        medium_vulns=_env_int("MEDIUM_VULNS", 0),
        migration_risk_level=_env_int("MIGRATION_RISK_LEVEL", 0),  # type: ignore[arg-type]
        code_churn_pct=_env_float("CODE_CHURN_PCT", 0.0),
        p95_latency_ms=_env_float("P95_LATENCY_MS", 0.0),
        p99_latency_ms=_env_float("P99_LATENCY_MS", 0.0),
        error_rate_pct=_env_float("ERROR_RATE_PCT", 0.0),
        compliance_score=_env_float("COMPLIANCE_SCORE", 100.0),
        ci_lint_passed=_env_bool("CI_LINT_PASSED", True),
        ci_tests_passed=_env_bool("CI_TESTS_PASSED", True),
    )


def _render_console(report: QualityReport, target: str, gate: float) -> None:
    """Print human-readable report to stdout."""
    status_icon = {
        "PROD_READY": "✅",
        "STAGE_ONLY": "⚠️ ",
        "BLOCK": "🚫",
    }
    print("\n" + "═" * 55)
    print("  INKA Quality Gate Report")
    print("═" * 55)
    print(f"  Version      : {report.version}")
    print(f"  Git SHA      : {report.git_sha[:12]}")
    print(f"  Target       : {target.upper()}")
    print(f"  Gate         : {gate:.0f} pts required")
    print(f"  Final Score  : {report.final_score:.1f} pts")
    print(f"  Recommendation: {status_icon.get(report.recommendation, '?')} {report.recommendation}")
    print("─" * 55)
    print("  Dimension Scores:")
    for dim, score in report.dimension_scores.items():
        print(f"    {dim:<20} : {score:>5.1f} pts")
    if report.penalties:
        print("─" * 55)
        print("  Penalties:")
        for p in report.penalties:
            print(f"    ⛔ {p['reason']}: -{p['pts']}")
    print("═" * 55 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="INKA Quality Gate")
    parser.add_argument("--target", choices=["stage", "prod"], default="stage",
                        help="Deployment target environment")
    parser.add_argument("--version", default=os.getenv("VERSION", "unknown"),
                        help="Release version string (e.g. 1.2.3)")
    parser.add_argument("--output-json", default="",
                        help="Write JSON report to this path (optional)")
    args = parser.parse_args()

    gate_threshold = GATE[args.target]
    quality_input = collect_input(args.version)

    engine = QualityEngine()
    report = engine.compute(quality_input)

    _render_console(report, args.target, gate_threshold)

    # ── Optionally persist JSON report ────────────────────────────────────────
    if args.output_json:
        import dataclasses
        report_dict = dataclasses.asdict(report)
        with open(args.output_json, "w") as fh:
            json.dump(report_dict, fh, indent=2)
        print(f"📄 Quality report written to {args.output_json}")

    # ── Gate decision ─────────────────────────────────────────────────────────
    if report.final_score < gate_threshold:
        print(
            f"❌ DEPLOYMENT BLOCKED: score {report.final_score:.1f} < {gate_threshold:.0f} "
            f"required for {args.target.upper()}"
        )
        sys.exit(1)

    print(f"✅ Quality gate PASSED for {args.target.upper()} deployment.")
    sys.exit(0)


if __name__ == "__main__":
    main()
