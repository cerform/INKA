"""Routes: repos — register and list GitHub repositories."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Repo
from ..schemas import RepoCreate, RepoResponse
from ..services.audit import log_action
from ..services.rbac import get_current_user_email

router = APIRouter(prefix="/api/repos", tags=["repos"])


@router.post("/register", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
def register_repo(
    payload: RepoCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    existing = db.query(Repo).filter(
        Repo.owner == payload.owner, Repo.name == payload.name
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Repository already registered")

    repo = Repo(**payload.model_dump())
    db.add(repo)
    log_action(db, actor, "repo.register", "repo", repo.id, {"owner": payload.owner, "name": payload.name})
    db.commit()
    db.refresh(repo)
    return repo


@router.get("", response_model=list[RepoResponse])
def list_repos(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return db.query(Repo).offset(skip).limit(limit).all()
