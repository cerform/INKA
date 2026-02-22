"""
Telegram Release Command Handler
Provides /release commands for admin/release_manager roles.
Integrates with GitHub Actions workflow_dispatch and release_registry.

Allowed roles: superadmin, release_manager (for promote/rollback)
               admin (for status/history only)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.deps import get_db_session
from app.models.user import UserRole

router = Router()

ALLOWED_ROLES_ALL = {UserRole.SUPERADMIN, UserRole.RELEASE_MANAGER}
ALLOWED_ROLES_READ = {UserRole.SUPERADMIN, UserRole.RELEASE_MANAGER, UserRole.ADMIN}

GH_API = "https://api.github.com"
GH_REPO = os.getenv("GITHUB_REPO", "org/inka")        # e.g. "myorg/inka"
GH_TOKEN = os.getenv("GITHUB_PAT_RELEASE")             # Fine-grained PAT: actions:write


def _gh_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def _check_permission(message: Message, required_roles: set[UserRole]) -> bool:
    """Return True if user has required role, else send denial and return False."""
    async with get_db_session() as session:
        from sqlalchemy import select
        from app.models.user import User
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user is None or UserRole(user.role) not in required_roles:
            await message.answer(
                "🚫 *Access Denied*\n"
                "This command requires `release_manager` or `superadmin` role.",
                parse_mode="Markdown",
            )
            return False
        return True


# ─── /release status ─────────────────────────────────────────────────────────

@router.message(Command("release_status"))
async def cmd_release_status(message: Message) -> None:
    """Show current deployment status for all environments."""
    if not await _check_permission(message, ALLOWED_ROLES_READ):
        return

    async with get_db_session() as session:
        from sqlalchemy import text
        rows = await session.execute(
            text("""
                SELECT environment, version, status, deployed_by, deployed_at, is_canary, canary_percent
                FROM release_registry
                WHERE status IN ('DEPLOYED', 'ROLLED_BACK')
                ORDER BY environment, deployed_at DESC
            """)
        )
        records = rows.fetchall()

    if not records:
        await message.answer("No deployments recorded yet.")
        return

    lines = ["📊 *Release Status*\n"]
    for row in records:
        env, ver, status, by, at, is_canary, pct = row
        canary_tag = f" (canary {pct}%)" if is_canary else ""
        status_icon = "✅" if status == "DEPLOYED" else "🔴"
        lines.append(
            f"{status_icon} *{env.upper()}* — v{ver}{canary_tag}\n"
            f"  Status: `{status}` | By: {by}\n"
            f"  At: {at.strftime('%Y-%m-%d %H:%M') if at else 'N/A'} UTC\n"
        )

    await message.answer("\n".join(lines), parse_mode="Markdown")


# ─── /release promote ────────────────────────────────────────────────────────

@router.message(Command("release_promote"))
async def cmd_release_promote(message: Message) -> None:
    """
    Trigger a deployment promotion.
    Usage: /release_promote <stage|prod> <version>
    Example: /release_promote prod v1.2.3
    """
    if not await _check_permission(message, ALLOWED_ROLES_ALL):
        return

    args = (message.text or "").split()
    if len(args) < 3:
        await message.answer(
            "Usage: `/release_promote <stage|prod> <version>`\n"
            "Example: `/release_promote prod v1.2.3`",
            parse_mode="Markdown",
        )
        return

    _, env, version = args[0], args[1], args[2]
    if env not in ("stage", "prod"):
        await message.answer("❌ Environment must be `stage` or `prod`.", parse_mode="Markdown")
        return

    if not version.startswith("v"):
        await message.answer("❌ Version must start with `v` (e.g. `v1.2.3`).", parse_mode="Markdown")
        return

    workflow = "deploy-stage.yml" if env == "stage" else "deploy-prod.yml"

    await message.answer(
        f"⏳ Triggering *{env.upper()}* deployment for `{version}`...\n"
        "Running pre-flight gate checks.",
        parse_mode="Markdown",
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GH_API}/repos/{GH_REPO}/actions/workflows/{workflow}/dispatches",
            headers=_gh_headers(),
            json={
                "ref": version,
                "inputs": {"version": version},
            },
        )

    if resp.status_code == 204:
        await message.answer(
            f"🚀 *{env.upper()}* deployment triggered for `{version}`\n"
            f"Initiated by: {message.from_user.full_name}\n"
            f"Monitor: https://github.com/{GH_REPO}/actions",
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            f"❌ Failed to trigger deployment: `{resp.status_code}`\n{resp.text}",
            parse_mode="Markdown",
        )


# ─── /release rollback ───────────────────────────────────────────────────────

@router.message(Command("release_rollback"))
async def cmd_release_rollback(message: Message) -> None:
    """
    Trigger a rollback for an environment.
    Usage: /release_rollback <stage|prod|dev> <reason>
    """
    if not await _check_permission(message, ALLOWED_ROLES_ALL):
        return

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Usage: `/release_rollback <env> <reason>`\n"
            "Example: `/release_rollback prod High error rate detected`",
            parse_mode="Markdown",
        )
        return

    _, env, reason = parts
    if env not in ("dev", "stage", "prod"):
        await message.answer("❌ Invalid environment.", parse_mode="Markdown")
        return

    await message.answer(
        f"⚠️ *ROLLBACK* initiated for *{env.upper()}*\n"
        f"Reason: _{reason}_\n\n"
        "Triggering rollback pipeline...",
        parse_mode="Markdown",
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GH_API}/repos/{GH_REPO}/actions/workflows/rollback.yml/dispatches",
            headers=_gh_headers(),
            json={
                "ref": "main",
                "inputs": {
                    "environment": env,
                    "reason": reason,
                    "downgrade_db": "false",
                },
            },
        )

    if resp.status_code == 204:
        await message.answer(
            f"🔴 *ROLLBACK* triggered on *{env.upper()}*\n"
            f"Initiated by: {message.from_user.full_name}\n"
            "RCA required within 24h. Incident logged.",
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            f"❌ Failed to trigger rollback: {resp.status_code}\n{resp.text}",
            parse_mode="Markdown",
        )


# ─── /release history ────────────────────────────────────────────────────────

@router.message(Command("release_history"))
async def cmd_release_history(message: Message) -> None:
    """
    Show last N releases for an environment.
    Usage: /release_history [env] [limit]
    """
    if not await _check_permission(message, ALLOWED_ROLES_READ):
        return

    args = (message.text or "").split()
    env = args[1] if len(args) > 1 else "prod"
    limit = int(args[2]) if len(args) > 2 else 5

    async with get_db_session() as session:
        from sqlalchemy import text
        rows = await session.execute(
            text("""
                SELECT version, status, deployed_by, deployed_at, git_sha
                FROM release_registry
                WHERE environment = :env
                ORDER BY deployed_at DESC
                LIMIT :limit
            """),
            {"env": env, "limit": limit},
        )
        records = rows.fetchall()

    if not records:
        await message.answer(f"No release history for `{env}`.", parse_mode="Markdown")
        return

    lines = [f"📜 *Release History — {env.upper()}* (last {limit})\n"]
    for ver, status, by, at, sha in records:
        icon = "✅" if status == "DEPLOYED" else ("🔴" if status == "ROLLED_BACK" else "⬜")
        lines.append(
            f"{icon} `v{ver}` → {status}\n"
            f"  By {by} | {at.strftime('%Y-%m-%d %H:%M') if at else 'N/A'}\n"
            f"  SHA: `{sha[:8]}`"
        )

    await message.answer("\n".join(lines), parse_mode="Markdown")
