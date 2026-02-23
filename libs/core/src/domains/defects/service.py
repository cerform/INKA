from uuid import UUID
from typing import List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .models import Defect, DefectStatus, DefectSeverity, ImpactArea
from .schemas import DefectCreate, DefectUpdate
from . import crud
from ..audit.service import audit_service

# Business rules: Restricted status transitions
VALID_TRANSITIONS = {
    DefectStatus.OPEN: [DefectStatus.TRIAGED, DefectStatus.REJECTED],
    DefectStatus.TRIAGED: [DefectStatus.ASSIGNED, DefectStatus.REJECTED, DefectStatus.OPEN],
    DefectStatus.ASSIGNED: [DefectStatus.FIXING, DefectStatus.TRIAGED],
    DefectStatus.FIXING: [DefectStatus.TESTING, DefectStatus.ASSIGNED],
    DefectStatus.TESTING: [DefectStatus.RESOLVED, DefectStatus.FIXING],
    DefectStatus.RESOLVED: [DefectStatus.CLOSED, DefectStatus.TESTING],
    DefectStatus.CLOSED: [DefectStatus.RESOLVED],  # Re-opening if needed
    DefectStatus.REJECTED: [DefectStatus.OPEN],
}

def create_defect_with_audit(db: Session, actor_id: UUID, payload: DefectCreate) -> Defect:
    defect = crud.create_defect(db, actor_id, payload)
    
    # Create initial timeline event
    crud.create_timeline_event(
        db, 
        defect_id=defect.id,
        event_type="defect_created",
        actor_id=actor_id,
        payload={"severity": defect.severity.value, "impact_area": defect.impact_area.value}
    )
    
    # Global Audit Log integration
    audit_service.log(
        db=db,
        actor_id=actor_id,
        action="defect_created",
        entity_id=defect.id,
        request_id=payload.request_id,
        after_payload=payload.model_dump(mode="json")
    )
    
    return defect

def update_defect_with_rules(db: Session, defect_id: UUID, actor_id: UUID, payload: DefectUpdate) -> Defect:
    defect = crud.get_defect(db, defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    old_status = defect.status
    old_data = {
        "status": defect.status.value,
        "severity": defect.severity.value,
        "root_cause": defect.root_cause,
        "regression_test_added": defect.regression_test_added
    }

    update_data = payload.model_dump(exclude_unset=True)

    # 1. Validate Status Transition
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status != old_status:
            if new_status not in VALID_TRANSITIONS.get(old_status, []):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status transition from {old_status} to {new_status}"
                )

            # 2. Check RCA for S1/S2 being closed
            if new_status == DefectStatus.CLOSED:
                if defect.severity in [DefectSeverity.S1, DefectSeverity.S2]:
                    # Need to check if root_cause is being set in this update or already exists
                    rc = update_data.get("root_cause") or defect.root_cause
                    if not rc:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Root cause analysis is mandatory to close {defect.severity} defects"
                        )
                
                # 3. Check Regression test added
                reg_test = update_data.get("regression_test_added")
                if reg_test is None:
                    reg_test = defect.regression_test_added
                
                if not reg_test:
                    raise HTTPException(
                        status_code=400, 
                        detail="Regression test must be added before closing a defect"
                    )

            # Update timestamps based on status
            if new_status == DefectStatus.TRIAGED and not defect.acknowledged_at:
                update_data["acknowledged_at"] = datetime.now(timezone.utc)
            elif new_status == DefectStatus.RESOLVED:
                update_data["resolved_at"] = datetime.now(timezone.utc)

    # Apply update
    updated_defect = crud.patch_defect(db, defect_id, payload)
    
    after_data = {
        "status": updated_defect.status.value,
        "severity": updated_defect.severity.value,
        "root_cause": updated_defect.root_cause,
        "regression_test_added": updated_defect.regression_test_added
    }

    # Create timeline event if significant changes occurred
    if any(k in update_data for k in ["status", "severity", "assigned_agents", "root_cause"]):
        crud.create_timeline_event(
            db,
            defect_id=defect.id,
            event_type="defect_updated",
            actor_id=actor_id,
            payload={
                "before": old_data,
                "after": after_data
            }
        )
        
        # Global Audit Log integration
        audit_service.log(
            db=db,
            actor_id=actor_id,
            action="defect_updated",
            entity_id=defect.id,
            before_payload=old_data,
            after_payload=after_data
        )

    return updated_defect

def list_defects(db: Session, **kwargs) -> List[Defect]:
    return crud.list_defects(db, **kwargs)

def get_timeline(db: Session, defect_id: UUID) -> List[Any]:
    return crud.get_timeline(db, defect_id)
