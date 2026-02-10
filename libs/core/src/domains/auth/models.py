import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class User(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    role = Column(String, default="read_only") # admin, manager, master, read_only
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    master_profile = relationship("Master", back_populates="user", uselist=False)
    created_bookings = relationship("Booking", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="actor")
    debug_sessions = relationship("DebugSession", back_populates="user")
