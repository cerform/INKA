"""
Quality Data Source
===================

Integrations:
  - Release registry (JSON file cache)
  - CI artifact store (coverage.xml, junit.xml)
  - Defect tracker (stub: replace with Jira/Linear API)
  - Security scanner (Trivy JSON output)
  - Performance benchmarks (stub: k6/Locust results)
  - Compliance Agent (stub: scoring endpoint)

Resolution order:
  1. Release registry JSON (primary source)
  2. Optional: Real-time fetch from CI/defect APIs
  3. Fallback: Return None if version not found

Environment Variables:
  QUALITY_REGISTRY_PATH        Path to quality_registry.json (default: quality_registry.json)
  DEFECT_API_URL               Defect tracker API endpoint (optional)
  DEFECT_API_TOKEN             Auth token for defect tracker
  COMPLIANCE_AGENT_URL         Compliance Agent scoring endpoint (optional)
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from packages.quality.quality_score import QualityInput

logger = logging.getLogger(__name__)


class QualityDataSource:
    """
    Fetches QualityInput for a given version.

    Supports multiple backends:
      1. Local registry (JSON file) — fast, cached
      2. Defect tracker API — real-time (Jira/Linear/etc)
      3. CI artifact store — coverage, test results
      4. Compliance Agent — scoring endpoint
    """

    def __init__(
        self,
        registry_path: Optional[str] = None,
        defect_api_url: Optional[str] = None,
        compliance_agent_url: Optional[str] = None,
    ) -> None:
        """
        Initialize data source.

        Args:
            registry_path: Path to quality_registry.json (env: QUALITY_REGISTRY_PATH)
            defect_api_url: Defect tracker API endpoint (env: DEFECT_API_URL)
            compliance_agent_url: Compliance Agent endpoint (env: COMPLIANCE_AGENT_URL)
        """
        self._registry_path = Path(
            registry_path or os.getenv("QUALITY_REGISTRY_PATH", "quality_registry.json")
        )
        self._defect_api_url = defect_api_url or os.getenv("DEFECT_API_URL")
        self._compliance_agent_url = compliance_agent_url or os.getenv("COMPLIANCE_AGENT_URL")
        self._defect_api_token = os.getenv("DEFECT_API_TOKEN")

    async def get(self, version: str) -> Optional[QualityInput]:
        """
        Fetch QualityInput for the specified version.

        Tries:
          1. Local registry (fast)
          2. Real-time APIs if configured
          3. Return None if not found

        Args:
            version: Version string (e.g., "1.3.0") or "latest"

        Returns:
            QualityInput if found, None otherwise
        """
        # ── Try local registry first (fastest) ──────────────────────────────
        record = self._get_from_registry(version)
        if record:
            logger.info(f"Loaded quality input for {version} from local registry")
            return QualityInput(**record)

        # ── Try real-time APIs if configured ───────────────────────────────
        if self._defect_api_url:
            try:
                record = await self._fetch_from_defect_api(version)
                if record:
                    logger.info(f"Loaded quality input for {version} from defect API")
                    return QualityInput(**record)
            except Exception as e:
                logger.warning(f"Failed to fetch from defect API: {e}")

        logger.warning(f"Quality input not found for version {version}")
        return None

    def _get_from_registry(self, version: str) -> Optional[dict]:
        """Load from local JSON registry."""
        if not self._registry_path.exists():
            return None

        try:
            data: dict = json.loads(self._registry_path.read_text())
            releases: list[dict] = data.get("releases", [])

            if version == "latest":
                return releases[-1] if releases else None

            return next((r for r in releases if r.get("version") == version), None)
        except Exception as e:
            logger.error(f"Failed to read registry: {e}")
            return None

    async def _fetch_from_defect_api(self, version: str) -> Optional[dict]:
        """
        Stub: Fetch defect counts from Jira/Linear/etc.

        TODO: Implement real API client.
        For now, returns None (falls back to local registry).

        Expected response format:
        {
            "version": "1.3.0",
            "git_sha": "abc123...",
            "open_s1_bugs": 0,
            "open_s2_bugs": 0,
            "open_s3_bugs": 0,
            ...
        }
        """
        # Placeholder for real API implementation
        return None

    async def _fetch_from_compliance_agent(self, version: str) -> Optional[float]:
        """
        Stub: Fetch compliance score from Compliance Agent.

        TODO: Implement real endpoint call.
        """
        # Placeholder for real API implementation
        return 100.0

    def save_to_registry(self, quality_input: QualityInput) -> None:
        """
        Append QualityInput to the local registry.
        Used by CI/CD to persist computed scores.
        """
        registry_data = {"releases": []}
        if self._registry_path.exists():
            registry_data = json.loads(self._registry_path.read_text())

        # Convert to dict, excluding auto-generated fields
        record = {
            "version": quality_input.version,
            "git_sha": quality_input.git_sha,
            "coverage_pct": quality_input.coverage_pct,
            "open_s1_bugs": quality_input.open_s1_bugs,
            "open_s2_bugs": quality_input.open_s2_bugs,
            "open_s3_bugs": quality_input.open_s3_bugs,
            "regression_tests_missing": quality_input.regression_tests_missing,
            "critical_vulns": quality_input.critical_vulns,
            "high_vulns": quality_input.high_vulns,
            "medium_vulns": quality_input.medium_vulns,
            "migration_risk_level": quality_input.migration_risk_level,
            "code_churn_pct": quality_input.code_churn_pct,
            "p95_latency_ms": quality_input.p95_latency_ms,
            "p99_latency_ms": quality_input.p99_latency_ms,
            "error_rate_pct": quality_input.error_rate_pct,
            "compliance_score": quality_input.compliance_score,
            "ci_lint_passed": quality_input.ci_lint_passed,
            "ci_tests_passed": quality_input.ci_tests_passed,
        }

        # Avoid duplicates
        registry_data["releases"] = [
            r for r in registry_data["releases"] if r["version"] != quality_input.version
        ]
        registry_data["releases"].append(record)

        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._registry_path.write_text(json.dumps(registry_data, indent=2))
        logger.info(f"Saved quality input for {quality_input.version} to registry")
