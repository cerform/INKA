"""
Quality Score Telegram Handler

Commands:
  /release quality {version}
  /release quality latest

Returns score breakdown + deployment recommendation.
"""
from __future__ import annotations

import logging
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from packages.quality.quality_score import QualityEngine, QualityInput, QualityReport


logger = logging.getLogger(__name__)
router = Router(name="quality")

# ─────────────────────────────────────────────────────────
# Message formatting helpers
# ─────────────────────────────────────────────────────────

RECOMMENDATION_EMOJI: dict[str, str] = {
    "PROD_READY": "✅",
    "STAGE_ONLY": "⚠️",
    "BLOCK": "🚫",
}


def _score_bar(score: float, width: int = 10) -> str:
    """Render a compact ASCII progress bar for the score."""
    filled = round(score / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {score:.1f}/100"


def _render_report(report: QualityReport) -> str:  # noqa: PLR0912
    """Format QualityReport as a Telegram-friendly message (MarkdownV2-safe)."""
    emoji = RECOMMENDATION_EMOJI.get(report.recommendation, "❓")
    lines: list[str] = [
        f"📊 *Quality Report — v{_esc(report.version)}*",
        f"Git SHA: `{_esc(report.git_sha[:12])}`",
        "",
        f"*Score:* {_score_bar(report.final_score)}",
        "",
        "─────────────────────────",
        "*Dimension Breakdown*",
        f"  Test Coverage      : {report.coverage_pct:>5.1f}%  → {report.dimension_scores['test_coverage']:>4.1f}pts",
        f"  Defect Status      : {report.open_bugs}S1 / {report.open_s2}S2 open  → {report.dimension_scores['defect_status']:>4.1f}pts",
        f"  Security Scan      : {report.critical_vulns} crit / {report.high_vulns} high → {report.dimension_scores['security_scan']:>4.1f}pts",
        f"  Migration Risk     : {report.migration_risk} → {report.dimension_scores['migration_risk']:>4.1f}pts",
        f"  Code Stability     : churn {report.code_churn_pct:.0f}% → {report.dimension_scores['code_stability']:>4.1f}pts",
        f"  Performance        : p95={report.p95_latency_ms:.0f}ms → {report.dimension_scores['performance']:>4.1f}pts",
        f"  Compliance         : {report.compliance_score}/{report.dimension_scores['compliance']:>4.1f}pts",
        "─────────────────────────",
    ]

    if report.penalties:
        lines.append("*Applied Penalties*")
        for penalty in report.penalties:
            lines.append(f"  ⛔ {_esc(penalty['reason'])}: -{penalty['pts']}")
        lines.append("")

    lines += [
        f"*Recommendation: {emoji} {_esc(report.recommendation)}*",
        "",
        f"🕐 Evaluated: {_esc(report.evaluated_at)}",
    ]
    return "\n".join(lines)


def _esc(text: str) -> str:
    """Minimal escaping for Telegram Markdown."""
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ─────────────────────────────────────────────────────────
# Registry stub — replace with DB/API lookup in production
# ─────────────────────────────────────────────────────────

async def _fetch_quality_input(version: str) -> QualityInput | None:
    """
    Fetch raw quality metrics for a given version.
    In production: query CI artifact store / defect DB / security scanner API.
    Returns None if version not found.
    """
    # TODO: replace stub with real data source
    from packages.quality.data_source import QualityDataSource  # lazy import
    ds = QualityDataSource()
    return await ds.get(version)


# ─────────────────────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────────────────────

@router.message(Command("release"))
async def release_quality_handler(message: Message) -> None:
    """
    Handle:
      /release quality {version}
      /release quality latest
    """
    args = (message.text or "").split()
    # Expected: /release quality <version|latest>
    if len(args) < 3 or args[1].lower() != "quality":
        await message.answer(
            "Usage:\n"
            "  `/release quality {version}`\n"
            "  `/release quality latest`",
            parse_mode="Markdown",
        )
        return

    version = args[2].lower()
    
    # Show loading state
    progress_msg = await message.answer(
        f"⏳ Computing quality score for `{_esc(version)}`…",
        parse_mode="Markdown"
    )

    try:
        quality_input = await _fetch_quality_input(version)
        if quality_input is None:
            await message.answer(
                f"❌ Version `{_esc(version)}` not found in release registry.",
                parse_mode="Markdown"
            )
            return

        engine = QualityEngine()
        report = engine.compute(quality_input)
        
        # Send formatted report
        await message.answer(_render_report(report), parse_mode="Markdown")
        
        # Log metrics
        logger.info(
            "quality_score_served",
            extra={
                "version": report.version,
                "score": report.final_score,
                "recommendation": report.recommendation,
                "user_id": message.from_user.id if message.from_user else None,
            },
        )
        
        # Clean up progress message
        await progress_msg.delete()
        
    except Exception as e:
        logger.error(f"Error computing quality score: {e}")
        await message.answer(
            f"❌ Error computing quality score: `{str(e)[:100]}`",
            parse_mode="Markdown"
        )
