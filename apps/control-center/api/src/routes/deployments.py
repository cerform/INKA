"""Routes: deployments — deploy, rollback, list."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Deployment, Service, Repo, PipelineRun, RunStatus
from ..schemas import DeployRequest, RollbackRequest, DeploymentResponse
from ..services.audit import log_action
from ..services.github_actions import github_actions
from ..services.rbac import get_current_user_email, require_role, UserRole

router = APIRouter(prefix="/api", tags=["deployments"])


@router.post("/deploy", response_model=DeploymentResponse)
async def deploy(
    payload: DeployRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
    _: object = Depends(require_role(UserRole.DEPLOYER, UserRole.ADMIN)),
):
    svc = db.query(Service).filter(Service.id == payload.service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    repo = db.query(Repo).filter(Repo.id == svc.repo_id).first()

    # Record deployment
    deployment = Deployment(
        service_id=payload.service_id,
        env=payload.env,
        image_digest=payload.image_digest,
        deployed_by=actor,
        traffic_config={"latest": 100},
    )
    db.add(deployment)
    log_action(db, actor, "deployment.trigger", "deployment", deployment.id, {
        "service": svc.service_name,
        "env": payload.env.value,
        "image_digest": payload.image_digest,
    })
    db.commit()
    db.refresh(deployment)

    # Trigger GitHub Actions deploy workflow
    if repo:
        try:
            await github_actions.trigger_workflow(
                owner=repo.owner,
                repo=repo.name,
                workflow_file=payload.workflow_file,
                ref="main",
                inputs={
                    "environment": payload.env.value,
                    "service": svc.cloud_run_service,
                    "image_digest": payload.image_digest,
                    "deployment_id": deployment.id,
                },
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Workflow dispatch failed: {exc}")

    return deployment


@router.post("/rollback", response_model=DeploymentResponse)
async def rollback(
    payload: RollbackRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
    _: object = Depends(require_role(UserRole.DEPLOYER, UserRole.ADMIN)),
):
    svc = db.query(Service).filter(Service.id == payload.service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    if not payload.to_revision and not payload.to_image_digest:
        raise HTTPException(status_code=400, detail="Provide to_revision or to_image_digest")

    repo = db.query(Repo).filter(Repo.id == svc.repo_id).first()

    # Find the last stable deployment to set rollback_of
    prev = db.query(Deployment).filter(
        Deployment.service_id == payload.service_id,
        Deployment.env == payload.env,
    ).order_by(Deployment.deployed_at.desc()).first()

    rollback_dep = Deployment(
        service_id=payload.service_id,
        env=payload.env,
        image_digest=payload.to_image_digest or "",
        cloud_run_revision=payload.to_revision,
        deployed_by=actor,
        rollback_of=prev.id if prev else None,
        traffic_config={"latest": 100},
    )
    db.add(rollback_dep)
    log_action(db, actor, "deployment.rollback", "deployment", rollback_dep.id, {
        "service": svc.service_name,
        "env": payload.env.value,
        "to_revision": payload.to_revision,
        "reason": payload.reason,
    })
    db.commit()
    db.refresh(rollback_dep)

    # Trigger rollback workflow
    if repo:
        try:
            await github_actions.trigger_workflow(
                owner=repo.owner,
                repo=repo.name,
                workflow_file="rollback.yml",
                ref="main",
                inputs={
                    "environment": payload.env.value,
                    "reason": payload.reason,
                },
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Rollback workflow dispatch failed: {exc}")

    return rollback_dep


@router.get("/deployments", response_model=List[DeploymentResponse])
def list_deployments(
    service_id: Optional[str] = None,
    env: Optional[str] = None,
    since: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Deployment).order_by(Deployment.deployed_at.desc())
    if service_id:
        q = q.filter(Deployment.service_id == service_id)
    if env:
        q = q.filter(Deployment.env == env)
    if since:
        q = q.filter(Deployment.deployed_at >= since)
    return q.offset(skip).limit(limit).all()
