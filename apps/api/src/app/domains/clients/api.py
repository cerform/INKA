from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from apps.api.app.deps.auth import get_db, PermissionChecker
from packages.core.domains.clients.models import Client

router = APIRouter()

class ClientSchema(BaseModel):
    id: UUID
    full_name: str
    phone: str
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)

class ClientCreate(BaseModel):
    full_name: str
    phone: str
    notes: str | None = None

@router.post("/", response_model=ClientSchema, dependencies=[Depends(PermissionChecker("clients:create"))])
def create_client(client_in: ClientCreate, db: Session = Depends(get_db)):
    client = Client(**client_in.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/", response_model=List[ClientSchema], dependencies=[Depends(PermissionChecker("clients:read"))])
def get_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()
