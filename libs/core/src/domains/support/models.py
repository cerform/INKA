import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class DebugSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"

class DebugSession(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    reason = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(DebugSessionStatus), default=DebugSessionStatus.ACTIVE)
    is_break_glass = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="debug_sessions")

class TestRun(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False) # e.g., running, success, fail
    metadata_json = Column(JSONB, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    creator = relationship("User")
