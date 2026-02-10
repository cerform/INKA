from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Time, Boolean
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class WorkingHours(Base):
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("master.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0-6 (ISO weekday)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)

    master = relationship("Master", back_populates="working_hours")

class TimeOff(Base):
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("master.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    description = Column(String, nullable=True)

    master = relationship("Master", back_populates="time_off")
