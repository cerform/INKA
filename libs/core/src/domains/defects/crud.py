from uuid import UUID
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from .models import Defect, DefectEvent, DefectStatus
from .schemas import DefectCreate, DefectUpdate

def create_defect(db: Session, actor_id: int, payload: DefectCreate) -> Defect:
    db_obj = Defect(
        **payload.model_dump(),
        actor_id=actor_id,
        status=DefectStatus.OPEN
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_defect(db: Session, defect_id: UUID) -> Optional[Defect]:
    return db.query(Defect).filter(Defect.id == defect_id).first()

def list_defects(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    impact_area: Optional[str] = None
) -> List[Defect]:
    query = db.query(Defect)
    if status:
        query = query.filter(Defect.status == status)
    if severity:
        query = query.filter(Defect.severity == severity)
    if impact_area:
        query = query.filter(Defect.impact_area == impact_area)
    
    return query.order_by(Defect.created_at.desc()).offset(skip).limit(limit).all()

def patch_defect(db: Session, defect_id: UUID, payload: DefectUpdate) -> Optional[Defect]:
    db_obj = get_defect(db, defect_id)
    if not db_obj:
        return None
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def create_timeline_event(
    db: Session, 
    defect_id: UUID, 
    event_type: str, 
    actor_id: Optional[int] = None, 
    payload: Optional[dict] = None
) -> DefectEvent:
    db_event = DefectEvent(
        defect_id=defect_id,
        event_type=event_type,
        actor_id=actor_id,
        payload=payload
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_timeline(db: Session, defect_id: UUID) -> List[DefectEvent]:
    return db.query(DefectEvent).filter(DefectEvent.defect_id == defect_id).order_by(DefectEvent.created_at.asc()).all()
