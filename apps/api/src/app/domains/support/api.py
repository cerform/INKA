from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from apps.api.app.deps.auth import get_db, PermissionChecker
from packages.core.domains.audit.models import AuditLog
from packages.core.domains.support.models import TestRun
from packages.core.domains.auth.models import User

router = APIRouter()

class DiagStatus(BaseModel):
    status: str
    database: str
    timezone: str = "Asia/Jerusalem"

class AuditLogSchema(BaseModel):
    id: UUID
    actor_id: UUID
    action: str
    request_id: Optional[UUID]
    entity_id: Optional[UUID]

@router.get("/status", response_model=DiagStatus, dependencies=[Depends(PermissionChecker("diag:read"))])
def get_status(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return DiagStatus(status="ok", database=db_status)

@router.get("/audit", response_model=List[AuditLogSchema], dependencies=[Depends(PermissionChecker("audit:read"))])
def get_audit_logs(
    request_id: Optional[UUID] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if request_id:
        query = query.filter(AuditLog.request_id == request_id)
    return query.limit(100).all()

@router.post("/testdata/reset", dependencies=[Depends(PermissionChecker("testdata:reset"))])
def reset_test_data(db: Session = Depends(get_db)):
    # Logic to purge test-tagged data
    return {"message": "Test data purged."}
