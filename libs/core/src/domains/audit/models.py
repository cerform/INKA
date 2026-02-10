import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class AuditLog(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    action = Column(Text, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Enrichment fields
    request_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    before_payload = Column(JSONB, nullable=True)
    after_payload = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    actor = relationship("User", back_populates="audit_logs")
