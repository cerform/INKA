# Service model placeholder - actual model is in domains
# This file kept for backward compatibility with imports
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

# Define a minimal Service only if needed for backward compatibility
# Most code should use domains/bookings/models.py instead
class Service(Base):
    __tablename__ = "service"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    price = Column(Numeric(precision=10, scale=2), nullable=False)

    tenant = relationship("Tenant", back_populates="services")
    bookings = relationship("Booking", back_populates="service")
    __table_args__ = {"extend_existing": True}
