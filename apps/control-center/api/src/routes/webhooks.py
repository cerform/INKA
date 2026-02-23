"""Routes: GitHub webhooks — validate HMAC signature, ingest workflow events."""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import PipelineRun, RunStatus
from ..schemas import WebhookAck
from ..services.audit import log_action

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _verify_signature(payload: bytes, signature_header: str | None) -> bool:
    """Validate X-Hub-Signature-256 using HMAC-SHA256."""
    if not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _map_gh_status(gh_conclusion: str | None, gh_status: str) -> RunStatus:
    """Map GitHub Actions status/conclusion to internal RunStatus."""
    if gh_status == "queued":
        return RunStatus.QUEUED
    if gh_status == "in_progress":
        return RunStatus.IN_PROGRESS
    if gh_status == "completed":
        mapping = {
            "success": RunStatus.SUCCESS,
            "failure": RunStatus.FAILURE,
            "cancelled": RunStatus.CANCELLED,
        }
        return mapping.get(gh_conclusion or "", RunStatus.FAILURE)
    return RunStatus.IN_PROGRESS


@router.post("/github", response_model=WebhookAck)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str = Header(default="ping"),
    db: Session = Depends(get_db),
):
    payload_bytes = await request.body()

    # Validate HMAC signature if webhook secret is configured
    if settings.GITHUB_WEBHOOK_SECRET:
        if not _verify_signature(payload_bytes, x_hub_signature_256):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    if x_github_event == "ping":
        return WebhookAck(received=True, event="ping")

    body: dict[str, Any] = await request.json() if not payload_bytes else json.loads(payload_bytes)
    action = body.get("action")

    if x_github_event == "workflow_run":
        wf_run = body.get("workflow_run", {})
        gh_run_id = str(wf_run.get("id", ""))
        gh_status = wf_run.get("status", "")
        gh_conclusion = wf_run.get("conclusion")
        head_sha = wf_run.get("head_sha", "")
        actor_login = wf_run.get("triggering_actor", {}).get("login", "github-actions")
        run_started_at = wf_run.get("run_started_at")
        updated_at = wf_run.get("updated_at")

        new_status = _map_gh_status(gh_conclusion, gh_status)

        # Find or create matching pipeline run record
        run = db.query(PipelineRun).filter(
            PipelineRun.github_run_id == gh_run_id
        ).first()

        if run:
            run.status = new_status
            run.commit_sha = head_sha or run.commit_sha
            if new_status in (RunStatus.SUCCESS, RunStatus.FAILURE, RunStatus.CANCELLED):
                run.finished_at = datetime.utcnow()
        else:
            # Auto-create a record for untracked runs (e.g. direct pushes)
            run = PipelineRun(
                github_run_id=gh_run_id,
                commit_sha=head_sha,
                status=new_status,
                actor=actor_login,
                started_at=datetime.utcnow(),
            )
            db.add(run)

        log_action(db, actor_login, f"webhook.workflow_run.{action}", "pipeline_run",
                   run.id if run.id else gh_run_id,
                   {"gh_status": gh_status, "conclusion": gh_conclusion})
        db.commit()

    return WebhookAck(received=True, event=x_github_event, action=action)
