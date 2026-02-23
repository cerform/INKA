from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps.auth import get_db, get_current_user, PermissionChecker
from packages.core.models import User
from packages.core.domains.defects import service, schemas

router = APIRouter()

@router.post("/", response_model=schemas.DefectRead, status_code=status.HTTP_201_CREATED)
def create_defect(
    payload: schemas.DefectCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user)
):
    """
    Creates a new defect record.
    Any authenticated user can report a defect.
    """
    return service.create_defect_with_audit(db, actor.id, payload)

@router.get("/", response_model=List[schemas.DefectRead])
def list_defects(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    impact_area: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    actor: User = Depends(PermissionChecker("defects:read"))
):
    """
    Lists defects with optional filtering.
    Requires 'defects:read' permission.
    """
    return service.list_defects(
        db, 
        severity=severity, 
        status=status, 
        impact_area=impact_area, 
        skip=skip, 
        limit=limit
    )

@router.get("/{defect_id}", response_model=schemas.DefectRead)
def get_defect(
    defect_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(PermissionChecker("defects:read"))
):
    """
    Gets a single defect by ID.
    """
    from packages.core.domains.defects import crud
    defect = crud.get_defect(db, defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect

@router.patch("/{defect_id}", response_model=schemas.DefectRead)
def update_defect(
    defect_id: UUID,
    payload: schemas.DefectUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(PermissionChecker("defects:write"))
):
    """
    Updates a defect record. Enforces business rules for transitions, RCA, and regressions.
    Requires 'defects:write' permission.
    """
    return service.update_defect_with_rules(db, defect_id, actor.id, payload)

@router.get("/{defect_id}/timeline", response_model=List[schemas.DefectTimelineEventRead])
def get_defect_timeline(
    defect_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(PermissionChecker("defects:read"))
):
    """
    Retrieves the audit timeline for a defect.
    """
    return service.get_timeline(db, defect_id)
