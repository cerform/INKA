"""Routes: pipeline runs — trigger, list, detail."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PipelineRun, Repo, Service, RunStatus
from ..schemas import TriggerRunRequest, TriggerRunResponse, PipelineRunResponse
from ..services.audit import log_action
from ..services.github_actions import github_actions
from ..services.rbac import get_current_user_email, require_role, UserRole

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("/trigger", response_model=TriggerRunResponse)
async def trigger_run(
    payload: TriggerRunRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
    _: object = Depends(require_role(UserRole.DEPLOYER, UserRole.ADMIN)),
):
    repo = db.query(Repo).filter(Repo.id == payload.repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    # Create a pending run record
    run = PipelineRun(
        repo_id=payload.repo_id,
        service_id=payload.service_id,
        actor=actor,
        status=RunStatus.QUEUED,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    log_action(db, actor, "run.trigger", "pipeline_run", run.id, {
        "repo": f"{repo.owner}/{repo.name}",
        "workflow": payload.workflow_file,
        "ref": payload.ref,
    })
    db.commit()
    db.refresh(run)

    # Dispatch to GitHub Actions
    try:
        await github_actions.trigger_workflow(
            owner=repo.owner,
            repo=repo.name,
            workflow_file=payload.workflow_file,
            ref=payload.ref,
            inputs=payload.inputs,
        )
    except Exception as exc:
        run.status = RunStatus.FAILURE
        db.commit()
        raise HTTPException(status_code=502, detail=f"GitHub Actions dispatch failed: {exc}")

    return TriggerRunResponse(
        run_id=run.id,
        github_run_id=run.github_run_id,
        status=run.status,
        message=f"Workflow '{payload.workflow_file}' dispatched on {repo.owner}/{repo.name}@{payload.ref}",
    )


@router.get("", response_model=List[PipelineRunResponse])
def list_runs(
    repo_id: Optional[str] = None,
    service_id: Optional[str] = None,
    status: Optional[str] = None,
    actor: Optional[str] = None,
    since: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(PipelineRun).order_by(PipelineRun.created_at.desc())
    if repo_id:
        q = q.filter(PipelineRun.repo_id == repo_id)
    if service_id:
        q = q.filter(PipelineRun.service_id == service_id)
    if status:
        q = q.filter(PipelineRun.status == status)
    if actor:
        q = q.filter(PipelineRun.actor == actor)
    if since:
        q = q.filter(PipelineRun.created_at >= since)
    return q.offset(skip).limit(limit).all()


@router.get("/{run_id}", response_model=PipelineRunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
