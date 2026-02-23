"""
Telegram Chaos Command Handler for INKA Admin.

Commands (restricted to: admin, resilience_authority):
  /chaos_list              — show all experiments in catalog
  /chaos_run <name> [env]  — start an experiment
  /chaos_stop <run_id>     — abort a running experiment
  /chaos_history           — show last 10 runs

Unauthorized users receive a silent denial with audit log entry.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.deps import get_db_session
from app.models.user import UserRole

logger = logging.getLogger(__name__)
router = Router()

# Roles allowed to run chaos experiments
CHAOS_ROLES = {UserRole.SUPERADMIN, UserRole.ADMIN}
# Env where the role name "resilience_authority" is stored
RESILIENCE_AUTHORITY_ROLE = "resilience_authority"

# Internal API base URL (same service or via internal VPC URL)
CHAOS_API_BASE = os.getenv("CHAOS_API_BASE", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------

async def _check_chaos_permission(message: Message) -> bool:
    """
    Check if requester has admin or resilience_authority role.
    Denies silently and logs unauthorized attempts.
    """
    async with get_db_session() as session:
        from sqlalchemy import select
        from app.models.user import User

        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user is None:
        logger.warning(
            "chaos_unauthorized_attempt",
            extra={
                "telegram_id": message.from_user.id,
                "username": message.from_user.username,
                "command": message.text,
            },
        )
        await message.answer(
            "🚫 *Access Denied*\n"
            "Chaos commands require `admin` or `resilience_authority` role.\n"
            "_This attempt has been logged._",
            parse_mode="Markdown",
        )
        return False

    role = getattr(user, "role", None)
    if role not in (
        UserRole.SUPERADMIN.value,
        UserRole.ADMIN.value,
        RESILIENCE_AUTHORITY_ROLE,
    ):
        logger.warning(
            "chaos_unauthorized_attempt",
            extra={
                "telegram_id": message.from_user.id,
                "username": message.from_user.username,
                "role": role,
                "command": message.text,
            },
        )
        await message.answer(
            "🚫 *Access Denied*\n"
            "Chaos commands require `admin` or `resilience_authority` role.",
            parse_mode="Markdown",
        )
        return False

    return True


def _requester_tag(message: Message) -> str:
    return f"telegram:@{message.from_user.username or message.from_user.id}"


# ---------------------------------------------------------------------------
# /chaos_list — list available experiments
# ---------------------------------------------------------------------------

@router.message(Command("chaos_list"))
async def cmd_chaos_list(message: Message) -> None:
    """
    Show all experiments in the chaos catalog.
    Usage: /chaos_list [env]
    Example: /chaos_list stage
    """
    if not await _check_chaos_permission(message):
        return

    args = (message.text or "").split()
    env_filter = args[1] if len(args) > 1 else None

    url = f"{CHAOS_API_BASE}/chaos/experiments"
    if env_filter:
        url += f"?env={env_filter}"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            experiments = resp.json()
        except Exception as exc:
            await message.answer(f"❌ Failed to load catalog: `{exc}`", parse_mode="Markdown")
            return

    if not experiments:
        await message.answer("No experiments available for this environment.")
        return

    header = "🧪 *Chaos Experiment Catalog*"
    if env_filter:
        header += f" `[{env_filter}]`"
    lines = [header + "\n"]

    for i, exp in enumerate(experiments, 1):
        compliance = "🔐 compliance required" if exp["requires_compliance"] else "✅ no approval needed"
        envs = ", ".join(sorted(exp["allowed_envs"]))
        lines.append(
            f"*{i}. {exp['name']}*\n"
            f"  _{exp['description']}_\n"
            f"  💥 Blast: `{exp['blast_radius']}`\n"
            f"  ⏱ Max: {exp['max_duration_sec'] // 60}m | {compliance}\n"
            f"  🌍 Envs: `{envs}`\n"
        )

    # Telegram limit — split if too long
    text = "\n".join(lines)
    if len(text) > 4096:
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            await message.answer(chunk, parse_mode="Markdown")
    else:
        await message.answer(text, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# /chaos_run <experiment> [env] [--approve]
# ---------------------------------------------------------------------------

@router.message(Command("chaos_run"))
async def cmd_chaos_run(message: Message) -> None:
    """
    Start a chaos experiment.
    Usage: /chaos_run <experiment_name> [dev|stage|prod] [--approve]
    Example: /chaos_run api_latency_injection stage
    Example (prod with compliance): /chaos_run cloud_run_instance_kill prod --approve
    """
    if not await _check_chaos_permission(message):
        return

    parts = (message.text or "").split()
    # parts[0] = /chaos_run, parts[1] = name, parts[2?] = env, parts[3?] = --approve
    if len(parts) < 2:
        await message.answer(
            "Usage: `/chaos_run <experiment_name> [env] [--approve]`\n"
            "Example: `/chaos_run api_latency_injection stage`\n"
            "Use `/chaos_list` to see available experiments.",
            parse_mode="Markdown",
        )
        return

    experiment_name = parts[1]
    env = parts[2] if len(parts) > 2 and parts[2] in ("dev", "stage", "prod") else "dev"
    compliance_approved = "--approve" in parts

    # Prod safety reminder
    if env == "prod" and not compliance_approved:
        await message.answer(
            "⚠️ *Production chaos requires explicit approval!*\n"
            f"Re-run with `--approve` flag:\n"
            f"`/chaos_run {experiment_name} prod --approve`\n\n"
            "This confirms you have compliance team sign-off.",
            parse_mode="Markdown",
        )
        return

    await message.answer(
        f"⏳ Starting experiment `{experiment_name}` on *{env.upper()}*...\n"
        f"Running safety pre-checks...",
        parse_mode="Markdown",
    )

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                f"{CHAOS_API_BASE}/chaos/run",
                json={
                    "experiment_name": experiment_name,
                    "environment": env,
                    "compliance_approved": compliance_approved,
                    "requester": _requester_tag(message),
                },
            )
        except Exception as exc:
            await message.answer(f"❌ API error: `{exc}`", parse_mode="Markdown")
            return

    if resp.status_code == 202:
        data = resp.json()
        run_id = data.get("run_id", "N/A")
        await message.answer(
            f"🔥 *Chaos experiment started!*\n\n"
            f"Experiment: `{experiment_name}`\n"
            f"Environment: `{env}`\n"
            f"Run ID: `{run_id[:8]}`\n"
            f"Requester: {_requester_tag(message)}\n\n"
            f"Monitor with: `/chaos_history`\n"
            f"Stop with: `/chaos_stop {run_id[:8]}`",
            parse_mode="Markdown",
        )
    elif resp.status_code == 403:
        await message.answer(
            f"🔐 *Safety gate blocked the experiment:*\n`{resp.json().get('detail', 'Unknown')}`",
            parse_mode="Markdown",
        )
    elif resp.status_code == 404:
        await message.answer(
            f"❓ *Unknown experiment:* `{experiment_name}`\n"
            "Use `/chaos_list` to see valid names.",
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            f"❌ Failed: HTTP {resp.status_code}\n`{resp.text}`",
            parse_mode="Markdown",
        )


# ---------------------------------------------------------------------------
# /chaos_stop <run_id>
# ---------------------------------------------------------------------------

@router.message(Command("chaos_stop"))
async def cmd_chaos_stop(message: Message) -> None:
    """
    Abort a running chaos experiment.
    Usage: /chaos_stop <run_id>
    """
    if not await _check_chaos_permission(message):
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "Usage: `/chaos_stop <run_id>`\nGet run_id from `/chaos_history`.",
            parse_mode="Markdown",
        )
        return

    run_id = parts[1]
    requester = _requester_tag(message)

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                f"{CHAOS_API_BASE}/chaos/stop/{run_id}",
                json={"reason": f"Manual stop by {requester}"},
            )
        except Exception as exc:
            await message.answer(f"❌ API error: `{exc}`", parse_mode="Markdown")
            return

    if resp.status_code == 200:
        data = resp.json()
        await message.answer(
            f"⛔ *Experiment stopped + rollback triggered*\n\n"
            f"Run ID: `{run_id}`\n"
            f"Message: _{data.get('message', 'OK')}_\n"
            f"Stopped by: {requester}",
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            f"❌ Stop failed: HTTP {resp.status_code}\n`{resp.text}`",
            parse_mode="Markdown",
        )


# ---------------------------------------------------------------------------
# /chaos_history — last 10 runs
# ---------------------------------------------------------------------------

@router.message(Command("chaos_history"))
async def cmd_chaos_history(message: Message) -> None:
    """
    Show last 10 chaos experiment runs.
    Usage: /chaos_history [env]
    """
    if not await _check_chaos_permission(message):
        return

    parts = (message.text or "").split()
    env_filter = parts[1] if len(parts) > 1 else None

    url = f"{CHAOS_API_BASE}/chaos/history?limit=10"
    if env_filter:
        url += f"&env={env_filter}"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            runs = resp.json()
        except Exception as exc:
            await message.answer(f"❌ API error: `{exc}`", parse_mode="Markdown")
            return

    if not runs:
        await message.answer("📭 No chaos runs recorded yet.")
        return

    STATUS_ICONS = {
        "completed": "✅",
        "running": "🔄",
        "aborted": "⛔",
        "rolled_back": "🔁",
        "failed": "💥",
        "pending": "⏳",
    }

    lines = ["📜 *Chaos Run History* (last 10)\n"]
    for run in runs:
        icon = STATUS_ICONS.get(run["status"], "❓")
        duration = f"{run['duration_sec']:.0f}s" if run.get("duration_sec") else "N/A"
        abort = f"\n  ⚠️ _{run['abort_reason']}_" if run.get("abort_reason") else ""
        lines.append(
            f"{icon} `{str(run['run_id'])[:8]}` — *{run['experiment_name']}*\n"
            f"  Env: `{run['environment']}` | Duration: `{duration}`\n"
            f"  By: {run['requester']}{abort}\n"
        )

    # Also fetch metrics summary
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            m_resp = await client.get(f"{CHAOS_API_BASE}/chaos/metrics")
            metrics = m_resp.json() if m_resp.status_code == 200 else {}
    except Exception:
        metrics = {}

    if metrics:
        lines.append(
            f"\n📊 *30-Day Metrics*\n"
            f"  MTTR: `{metrics.get('avg_mttr_sec', 0):.0f}s` | "
            f"Auto-recovery: `{metrics.get('auto_recovery_rate_pct', 0):.1f}%`\n"
            f"  Rollbacks: `{metrics.get('rollback_frequency', 0)}` | "
            f"Failed tests: `{metrics.get('failed_resilience_tests', 0)}`"
        )

    await message.answer("\n".join(lines), parse_mode="Markdown")
