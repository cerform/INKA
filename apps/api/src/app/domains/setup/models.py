from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from packages.db.base_class import Base
from datetime import datetime


class SalonSetup(Base):
    """Configuration for salon during initial setup"""
    __tablename__ = "salon_setup"
    
    id = Column(String, primary_key=True, index=True)
    admin_id = Column(String, nullable=False, unique=True, index=True)
    
    salon_name = Column(String, nullable=False)
    specialization = Column(String, nullable=True)  # tattoo, piercing, nail art, etc
    telegram_bot_token = Column(String, nullable=True)
    api_key = Column(String, nullable=True, unique=True, index=True)
    
    # Calendar settings
    work_start_time = Column(String, default="09:00")  # HH:MM format
    work_end_time = Column(String, default="21:00")
    timezone = Column(String, default="UTC")
    
    # Status
    is_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SalonWorkSchedule(Base):
    """Work schedule/calendar for salon"""
    __tablename__ = "salon_work_schedule"
    
    id = Column(String, primary_key=True, index=True)
    setup_id = Column(String, index=True, nullable=False)
    
    day_of_week = Column(String, nullable=False)  # monday, tuesday, etc
    is_working = Column(Boolean, default=True)
    start_time = Column(String, nullable=True)  # HH:MM format
    end_time = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
