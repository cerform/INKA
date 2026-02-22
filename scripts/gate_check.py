#!/usr/bin/env python3
"""
Deployment Gate Check Script
Validates all conditions before allowing a deployment to proceed.
Usage: python scripts/gate_check.py --env=stage [--strict]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GateFailure:
    check: str
    reason: str


@dataclass
class GateResult:
    passed: bool
    failures: list[GateFailure] = field(default_factory=list)


# ─── Individual Checks ──────────────────────────────────────────────────────


def check_version_bumped() -> GateFailure | None:
    """Compare pyproject.toml version against latest git tag."""
    try:
        with open("pyproject.toml", "rb") as f:
            current = tomllib.load(f)["project"]["version"]

        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return None  # No tags yet — first release, allow
        latest_tag = result.stdout.strip().lstrip("v")

        if current == latest_tag:
            return GateFailure(
                check="version_bump",
                reason=f"Version {current} is identical to latest tag v{latest_tag}. Bump pyproject.toml version.",
            )
    except Exception as e:
        return GateFailure(check="version_bump", reason=str(e))
    return None


def check_coverage(threshold: int = 80) -> GateFailure | None:
    """Read coverage.xml and verify line-rate meets threshold."""
    coverage_file = Path("coverage.xml")
    if not coverage_file.exists():
        return GateFailure(check="coverage", reason="coverage.xml not found. Run pytest first.")
    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        line_rate = float(root.attrib.get("line-rate", "0")) * 100
        if line_rate < threshold:
            return GateFailure(
                check="coverage",
                reason=f"Coverage {line_rate:.1f}% is below threshold {threshold}%"
            )
    except Exception as e:
        return GateFailure(check="coverage", reason=str(e))
    return None


def check_defects(env: str) -> GateFailure | None:
    """Query defect registry API for open S1/S2 defects."""
    import httpx

    api_url = os.getenv("DEFECT_API_URL")
    api_key = os.getenv("DEFECT_API_KEY")

    if not api_url:
        print("⚠️  DEFECT_API_URL not set — skipping defect check")
        return None

    try:
        severities = "S1,S2" if env in ("stage", "prod") else "S1"
        resp = httpx.get(
            f"{api_url}/api/v1/defects",
            params={"severity": severities, "status": "OPEN"},
            headers={"X-API-Key": api_key or ""},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data["count"] > 0:
            defects_str = ", ".join(f"{d['id']} ({d['severity']})" for d in data["defects"])
            return GateFailure(
                check="defects",
                reason=f"Open defects blocking deployment: {defects_str}"
            )
    except Exception as e:
        return GateFailure(check="defects", reason=f"Defect API error: {e}")
    return None


def check_vulnerability_scan() -> GateFailure | None:
    """Check Trivy scan report for CRITICAL vulnerabilities."""
    for service in ("api", "bot", "admin"):
        report_file = Path(f"trivy-{service}.json")
        if not report_file.exists():
            continue
        try:
            data = json.loads(report_file.read_text())
            for result in data.get("Results", []):
                for vuln in result.get("Vulnerabilities", []):
                    if vuln.get("Severity") == "CRITICAL":
                        return GateFailure(
                            check="vulnerability_scan",
                            reason=f"CRITICAL vulnerability in {service}: {vuln['VulnerabilityID']} ({vuln.get('PkgName', 'unknown')})"
                        )
        except Exception as e:
            return GateFailure(check="vulnerability_scan", reason=f"Error reading trivy report: {e}")
    return None


def check_changelog_updated() -> GateFailure | None:
    """Verify CHANGELOG.md has been modified since last release tag."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return None  # No tags yet
        last_tag = result.stdout.strip()
        diff = subprocess.run(
            ["git", "diff", last_tag, "--name-only", "--", "CHANGELOG.md"],
            capture_output=True, text=True
        )
        if "CHANGELOG.md" not in diff.stdout:
            return GateFailure(
                check="changelog",
                reason=f"CHANGELOG.md not updated since {last_tag}"
            )
    except Exception as e:
        return GateFailure(check="changelog", reason=str(e))
    return None


def check_migration_safety() -> GateFailure | None:
    """Verify new migrations have both upgrade and downgrade implemented."""
    migration_dir = Path("libs/database/alembic/versions")
    if not migration_dir.exists():
        return None

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD", "--",
             "libs/database/alembic/versions/"],
            capture_output=True, text=True
        )
        new_migrations = [f for f in result.stdout.splitlines() if f.endswith(".py")]

        for migration_path in new_migrations:
            content = Path(migration_path).read_text()
            if "def downgrade" not in content:
                return GateFailure(
                    check="migration_safety",
                    reason=f"Migration {migration_path} has no downgrade() function. Add reversible downgrade or mark as irreversible and get explicit approval."
                )
            if "raise NotImplementedError" in content and "downgrade" in content:
                return GateFailure(
                    check="migration_safety",
                    reason=f"Migration {migration_path} has irreversible downgrade. Explicit approval required."
                )
    except Exception as e:
        return GateFailure(check="migration_safety", reason=str(e))
    return None


# ─── Gate Runner ─────────────────────────────────────────────────────────────


def run_gate(env: str, strict: bool) -> GateResult:
    checks = [
        ("Version Bump", check_version_bumped()),
        ("Coverage ≥ 80%", check_coverage(80)),
        ("Defect Registry", check_defects(env)),
        ("Vulnerability Scan", check_vulnerability_scan()),
        ("Changelog Updated", check_changelog_updated()),
        ("Migration Safety", check_migration_safety()),
    ]

    failures = []
    for name, result in checks:
        if result is None:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {result.reason}")
            failures.append(result)

    return GateResult(passed=len(failures) == 0, failures=failures)


def main() -> None:
    parser = argparse.ArgumentParser(description="INKA Deployment Gate Check")
    parser.add_argument("--env", choices=["dev", "stage", "prod"], required=True)
    parser.add_argument("--strict", action="store_true",
                        help="Fail on any check failure (vs warn-only for dev)")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  🔐 INKA Deployment Gate — {args.env.upper()}")
    print(f"{'='*50}\n")

    result = run_gate(args.env, args.strict)

    print(f"\n{'='*50}")
    if result.passed:
        print("  🟢 GATE PASSED — deployment approved")
        sys.exit(0)
    else:
        print(f"  🔴 GATE BLOCKED — {len(result.failures)} check(s) failed")
        if args.env == "dev" and not args.strict:
            print("  ⚠️  DEV mode: warnings only (use --strict to enforce)")
            sys.exit(0)
        sys.exit(1)


if __name__ == "__main__":
    main()
