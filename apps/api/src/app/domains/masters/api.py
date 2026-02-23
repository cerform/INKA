from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from app.deps.auth import get_db, PermissionChecker, get_tenant_id
from packages.core.models import Master, User

router = APIRouter()

class MasterSchema(BaseModel):
    id: int
    tenant_id: int
    user_id: int | None
    name: str
    active: bool

    model_config = ConfigDict(from_attributes=True)

class MasterCreate(BaseModel):
    name: str
    user_id: int | None = None

@router.post("/", response_model=MasterSchema)
def create_master(
    master_in: MasterCreate, 
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    actor: User = Depends(PermissionChecker("masters:create"))
):
    master = Master(tenant_id=tenant_id, **master_in.model_dump())
    db.add(master)
    db.commit()
    db.refresh(master)
    return master

@router.get("/", response_model=List[MasterSchema])
def get_masters(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    actor: User = Depends(PermissionChecker("masters:read"))
):
    return db.query(Master).filter(Master.tenant_id == tenant_id).all()
