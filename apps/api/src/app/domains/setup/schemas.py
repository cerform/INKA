from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SalonSpecification(BaseModel):
    """Specification types for salons"""
    tatmoo: str = "Tattoo"
    piercing: str = "Piercing"
    nail_art: str = "Nail Art"
    beauty: str = "Beauty"
    all: str = "All Services"


class WorkScheduleCreate(BaseModel):
    day_of_week: str  # monday, tuesday, etc
    is_working: bool = True
    start_time: Optional[str] = "09:00"
    end_time: Optional[str] = "21:00"


class WorkScheduleRead(WorkScheduleCreate):
    id: str
    setup_id: str


class SalonSetupCreate(BaseModel):
    salon_name: str = Field(..., min_length=1, max_length=255)
    specialization: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    work_start_time: str = "09:00"
    work_end_time: str = "21:00"
    timezone: str = "UTC"
    work_schedule: Optional[List[WorkScheduleCreate]] = None


class SalonSetupUpdate(BaseModel):
    salon_name: Optional[str] = None
    specialization: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    timezone: Optional[str] = None
    is_completed: Optional[bool] = None


class SalonSetupRead(SalonSetupCreate):
    id: str
    admin_id: str
    api_key: str
    is_completed: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    work_schedule: List[WorkScheduleRead] = []


class SetupResponse(BaseModel):
    status: str
    message: str
    data: Optional[SalonSetupRead] = None
