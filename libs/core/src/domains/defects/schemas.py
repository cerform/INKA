from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from .models import DefectSeverity, DefectStatus, ImpactArea, DetectedBy

class DefectBase(BaseModel):
    title: str
    description: Optional[str] = None
    environment: str
    severity: DefectSeverity
    impact_area: ImpactArea
    detected_by: DetectedBy
    request_id: Optional[UUID] = None
    correlation_id: Optional[UUID] = None
    metadata_json: Optional[dict] = Field(default_factory=dict)

class DefectCreate(DefectBase):
    detected_at: datetime = Field(default_factory=datetime.utcnow)

class DefectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[DefectSeverity] = None
    impact_area: Optional[ImpactArea] = None
    status: Optional[DefectStatus] = None
    root_cause: Optional[str] = None
    fix_commit_sha: Optional[str] = None
    regression_test_added: Optional[bool] = None
    assigned_agents: Optional[List[str]] = None
    related_incidents: Optional[List[UUID]] = None
    metadata_json: Optional[dict] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class DefectRead(DefectBase):
    id: UUID
    actor_id: UUID
    status: DefectStatus
    root_cause: Optional[str] = None
    fix_commit_sha: Optional[str] = None
    regression_test_added: bool
    assigned_agents: List[str]
    related_incidents: List[UUID]
    detected_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DefectTimelineEventRead(BaseModel):
    id: UUID
    defect_id: UUID
    event_type: str
    actor_id: Optional[UUID] = None
    payload: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True
