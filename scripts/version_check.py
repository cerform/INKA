#!/usr/bin/env python3
"""
Version Bump Enforcement Script
Fails if pyproject.toml version equals the latest git tag when code has changed.
Used in CI and pre-commit hooks.
"""
from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path


CODE_PATHS = ["apps/", "libs/"]


def get_current_version() -> str:
    with open("pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["version"]


def get_latest_tag() -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip().lstrip("v")


def git_code_changed_since_tag(tag: str) -> bool:
    """Check if any code file changed since the given tag."""
    result = subprocess.run(
        ["git", "diff", f"v{tag}", "--name-only", "--"] + CODE_PATHS,
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())


def main() -> None:
    current = get_current_version()
    latest_tag = get_latest_tag()

    if latest_tag is None:
        print(f"✅ No previous tags found — first release (version: {current})")
        sys.exit(0)

    print(f"Current version:  {current}")
    print(f"Latest git tag:   v{latest_tag}")

    if current == latest_tag:
        if git_code_changed_since_tag(latest_tag):
            print(
                f"\n❌ BLOCKED: Version {current} equals latest tag v{latest_tag} "
                f"but code changes exist.\n"
                f"  → Bump the version in pyproject.toml before committing.\n"
                f"  → PATCH for bug fixes, MINOR for features, MAJOR for breaking changes."
            )
            sys.exit(1)
        else:
            print("✅ Version unchanged and no code changes detected.")
    else:
        print(f"✅ Version bumped: v{latest_tag} → {current}")
        # Validate SemVer format
        parts = current.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            print(f"❌ Invalid SemVer format: {current}. Expected MAJOR.MINOR.PATCH")
            sys.exit(1)
        print("✅ Valid SemVer format confirmed.")

    sys.exit(0)


if __name__ == "__main__":
    main()
