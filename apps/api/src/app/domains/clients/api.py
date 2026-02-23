from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from app.deps.auth import get_db, PermissionChecker, get_tenant_id
from packages.core.models import Client, User

router = APIRouter()

class ClientSchema(BaseModel):
    id: int
    tenant_id: int
    full_name: str
    phone: str
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)

class ClientCreate(BaseModel):
    full_name: str
    phone: str
    notes: str | None = None

@router.post("/", response_model=ClientSchema)
def create_client(
    client_in: ClientCreate, 
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    actor: User = Depends(PermissionChecker("clients:create"))
):
    client = Client(tenant_id=tenant_id, **client_in.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/", response_model=List[ClientSchema])
def get_clients(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    actor: User = Depends(PermissionChecker("clients:read"))
):
    return db.query(Client).filter(Client.tenant_id == tenant_id).all()
