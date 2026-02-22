"""
Quality Data Source Stub
========================
Replace this with real integrations:
  - CI artifact store (coverage.xml, junit.xml)
  - Defect tracker (Jira / Linear API)
  - Security scanner (Trivy, Snyk, Bandit JSON output)
  - Performance benchmarks (k6 / Locust JSON output)
  - Compliance Agent scoring endpoint
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from libs.quality.src.quality_score import QualityInput


class QualityDataSource:
    """
    Fetches QualityInput for a given version.

    Resolution order:
      1. Release registry JSON file (QUALITY_REGISTRY_PATH env var)
      2. Return None → version not found
    """

    def __init__(self, registry_path: Optional[str] = None) -> None:
        self._path = Path(
            registry_path or os.getenv("QUALITY_REGISTRY_PATH", "quality_registry.json")
        )

    async def get(self, version: str) -> Optional[QualityInput]:
        """Return QualityInput for the specified version or None if not found."""
        if not self._path.exists():
            return None

        data: dict = json.loads(self._path.read_text())
        releases: list[dict] = data.get("releases", [])

        if version == "latest":
            record = releases[-1] if releases else None
        else:
            record = next((r for r in releases if r.get("version") == version), None)

        if record is None:
            return None

        return QualityInput(**record)
