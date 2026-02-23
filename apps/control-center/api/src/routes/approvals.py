"""Routes: approvals — request, approve, reject."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Approval, Deployment, ApprovalStatus
from ..schemas import ApprovalRequest, ApprovalDecision, ApprovalResponse
from ..services.audit import log_action
from ..services.rbac import get_current_user_email, require_role, UserRole

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.post("/request", response_model=ApprovalResponse, status_code=201)
def request_approval(
    payload: ApprovalRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    dep = db.query(Deployment).filter(Deployment.id == payload.deployment_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")

    # Only one pending approval per deployment
    existing = db.query(Approval).filter(
        Approval.deployment_id == payload.deployment_id,
        Approval.status == ApprovalStatus.PENDING,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Pending approval already exists for this deployment")

    approval = Approval(
        deployment_id=payload.deployment_id,
        env=payload.env,
        requested_by=payload.requested_by,
    )
    db.add(approval)
    log_action(db, actor, "approval.request", "approval", approval.id, {
        "deployment_id": payload.deployment_id,
        "env": payload.env.value,
    })
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve(
    approval_id: str,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
    _: object = Depends(require_role(UserRole.ADMIN, UserRole.DEPLOYER)),
):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Approval already {approval.status.value}")

    approval.status = ApprovalStatus.APPROVED
    approval.approved_by = actor
    approval.approved_at = datetime.utcnow()
    approval.reason = payload.reason

    log_action(db, actor, "approval.approve", "approval", approval.id, {
        "reason": payload.reason
    })
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject(
    approval_id: str,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
    _: object = Depends(require_role(UserRole.ADMIN, UserRole.DEPLOYER)),
):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Approval already {approval.status.value}")

    approval.status = ApprovalStatus.REJECTED
    approval.approved_by = actor
    approval.approved_at = datetime.utcnow()
    approval.reason = payload.reason

    log_action(db, actor, "approval.reject", "approval", approval.id, {
        "reason": payload.reason
    })
    db.commit()
    db.refresh(approval)
    return approval


@router.get("", response_model=List[ApprovalResponse])
def list_approvals(
    status: Optional[str] = None,
    env: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Approval).order_by(Approval.created_at.desc())
    if status:
        q = q.filter(Approval.status == status)
    if env:
        q = q.filter(Approval.env == env)
    return q.offset(skip).limit(limit).all()
