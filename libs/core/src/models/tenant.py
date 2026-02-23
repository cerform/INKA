import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from packages.db.base_class import Base

class TenantStatus(str, enum.Enum):
    CREATED = "created"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class Tenant(Base):
    __tablename__ = "tenant"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=True) # For custom domains
    name = Column(String, nullable=False)
    type = Column(String, default="beauty") # e.g., "beauty", "tattoo"
    status = Column(SQLEnum(TenantStatus), default=TenantStatus.ACTIVE, nullable=False)
    timezone = Column(String, default="Asia/Jerusalem", nullable=False)
    theme_config = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships (Optional: back-refs can be added to domain models)
    users = relationship("User", back_populates="tenant")
    masters = relationship("Master", back_populates="tenant")
    clients = relationship("Client", back_populates="tenant", overlaps="masters")
    bookings = relationship("Booking", back_populates="tenant")
    services = relationship("Service", back_populates="tenant")
    # working_hours and time_off relationship names might vary in other models
    # but we'll stick to what was there or what is standard
    working_hours = relationship("WorkingHours", back_populates="tenant")
    time_off = relationship("TimeOff", back_populates="tenant")
    salon_hours = relationship("SalonWorkingHours", back_populates="tenant")
    salon_closed_days = relationship("SalonClosedDay", back_populates="tenant")
