import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Boolean, Integer

from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class DefectSeverity(str, enum.Enum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"

class DefectStatus(str, enum.Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    FIXING = "fixing"
    TESTING = "testing"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

class ImpactArea(str, enum.Enum):
    BOT = "bot"
    BACKEND = "backend"
    DB = "db"
    SECURITY = "security"
    DEVOPS = "devops"

class DetectedBy(str, enum.Enum):
    USER = "user"
    QA = "qa"
    MONITORING = "monitoring"

class Defect(Base):
    __tablename__ = "defect_log"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    environment = Column(String, nullable=False)  # dev, stage, prod
    severity = Column(Enum(DefectSeverity), index=True, nullable=False)
    impact_area = Column(Enum(ImpactArea), nullable=False)
    detected_by = Column(Enum(DetectedBy), nullable=False)
    
    request_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    actor_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    status = Column(Enum(DefectStatus), default=DefectStatus.OPEN, index=True, nullable=False)
    root_cause = Column(Text, nullable=True)
    fix_commit_sha = Column(String(40), nullable=True)
    regression_test_added = Column(Boolean, default=False)
    
    assigned_agents = Column(JSONB, default=list, nullable=False)
    related_incidents = Column(JSONB, default=list, nullable=False)
    metadata_json = Column(JSONB, default=dict, nullable=False)
    
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    actor = relationship("User", back_populates="defects")
    events = relationship("DefectEvent", back_populates="defect", cascade="all, delete-orphan")

class DefectEvent(Base):
    __tablename__ = "defect_event"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defect_log.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # e.g., status_changed, agent_assigned
    actor_id = Column(Integer, ForeignKey("user.id"), nullable=True)

    payload = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    defect = relationship("Defect", back_populates="events")
    actor = relationship("User")
