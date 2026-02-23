from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class SalonWorkingHours(Base):
    """
    Weekly working hours for the salon (tenant).
    All master schedules should be within these bounds.
    """
    __tablename__ = "salon_working_hours"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False) # 0-6 (ISO weekday, 0=Monday)
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)

    tenant = relationship("Tenant", back_populates="salon_hours")

class SalonClosedDay(Base):
    """
    Exceptions to salon working hours (holidays, repair days, etc.)
    """
    __tablename__ = "salon_closed_day"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)

    tenant = relationship("Tenant", back_populates="salon_closed_days")
