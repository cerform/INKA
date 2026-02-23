"""Routes: services — register and list Cloud Run service mappings."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Repo, Service
from ..schemas import ServiceCreate, ServiceResponse
from ..services.audit import log_action
from ..services.rbac import get_current_user_email

router = APIRouter(prefix="/api/services", tags=["services"])


@router.post("/register", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def register_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    repo = db.query(Repo).filter(Repo.id == payload.repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    existing = db.query(Service).filter(
        Service.repo_id == payload.repo_id,
        Service.service_name == payload.service_name,
        Service.env == payload.env,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Service already registered for this env")

    svc = Service(**payload.model_dump())
    db.add(svc)
    log_action(db, actor, "service.register", "service", svc.id, payload.model_dump())
    db.commit()
    db.refresh(svc)
    return svc


@router.get("", response_model=List[ServiceResponse])
def list_services(
    repo_id: Optional[str] = None,
    env: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Service)
    if repo_id:
        q = q.filter(Service.repo_id == repo_id)
    if env:
        q = q.filter(Service.env == env)
    return q.offset(skip).limit(limit).all()
