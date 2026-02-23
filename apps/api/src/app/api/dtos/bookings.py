from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BookingCreateDTO(BaseModel):
    client_id: int
    master_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None


class BookingDTO(BookingCreateDTO):
    id: int
    tenant_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class SlotDTO(BaseModel):
    start_time: datetime
    end_time: datetime
