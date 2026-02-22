#!/usr/bin/env python3
"""
Release Registry: Register a new deployment.
Called from CI after a successful Cloud Run deployment.
"""
from __future__ import annotations

import os
import tomllib
import uuid
from datetime import datetime, timezone

import psycopg2


def main() -> None:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    version = os.environ.get("VERSION") or _get_version_from_toml()
    git_sha = os.environ["GIT_SHA"]
    deployed_by = os.environ["DEPLOYED_BY"]
    environment = os.environ["ENVIRONMENT"]
    is_canary = os.environ.get("IS_CANARY", "false").lower() == "true"
    canary_percent = int(os.environ.get("CANARY_PERCENT", "100")) if is_canary else 100
    rollback_revision = os.environ.get("ROLLBACK_REVISION")

    # Mark previous deployment as SUPERSEDED
    cur.execute(
        """
        UPDATE release_registry
        SET status = 'SUPERSEDED'
        WHERE environment = %s AND status = 'DEPLOYED'
        """,
        (environment,),
    )

    cur.execute(
        """
        INSERT INTO release_registry (
            id, version, environment, git_sha, deployed_by,
            deployed_at, is_canary, canary_percent, status, rollback_revision
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            version,
            environment,
            git_sha,
            deployed_by,
            datetime.now(timezone.utc),
            is_canary,
            canary_percent,
            "DEPLOYED",
            rollback_revision,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Release registered: v{version} → {environment} (canary={is_canary})")


def _get_version_from_toml() -> str:
    with open("pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["version"]


if __name__ == "__main__":
    main()
