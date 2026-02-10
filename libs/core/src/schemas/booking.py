from typing import Optional
from datetime import datetime
from .base import BaseSchema
from packages.core.models.booking import BookingStatus

class BookingBase(BaseSchema):
    client_id: int
    master_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    deposit_amount: float = 0.0

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseSchema):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None
    deposit_amount: Optional[float] = None

class Booking(BookingBase):
    id: int
    status: BookingStatus
