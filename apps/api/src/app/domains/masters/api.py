from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from apps.api.app.deps.auth import get_db, PermissionChecker
from packages.core.domains.masters.models import Master

router = APIRouter()

class MasterSchema(BaseModel):
    id: UUID
    user_id: UUID | None
    name: str
    active: bool

    model_config = ConfigDict(from_attributes=True)

class MasterCreate(BaseModel):
    name: str
    user_id: UUID | None = None

@router.post("/", response_model=MasterSchema, dependencies=[Depends(PermissionChecker("masters:create"))])
def create_master(master_in: MasterCreate, db: Session = Depends(get_db)):
    master = Master(**master_in.model_dump())
    db.add(master)
    db.commit()
    db.refresh(master)
    return master

@router.get("/", response_model=List[MasterSchema], dependencies=[Depends(PermissionChecker("masters:read"))])
def get_masters(db: Session = Depends(get_db)):
    return db.query(Master).all()
