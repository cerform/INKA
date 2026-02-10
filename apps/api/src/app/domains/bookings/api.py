from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from apps.api.app.deps.auth import get_db, get_current_user, PermissionChecker
from packages.core.domains.bookings.models import Booking
from packages.core.domains.bookings.service import booking_service
from packages.core.domains.auth.models import User

router = APIRouter()

class BookingSchema(BaseModel):
    id: UUID
    client_id: UUID
    master_id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    created_by: UUID

    model_config = ConfigDict(from_attributes=True)

class BookingCreateRequest(BaseModel):
    client_id: UUID
    master_id: UUID
    start_time: datetime
    end_time: datetime

@router.post("/", response_model=BookingSchema)
def create_booking(
    booking_in: BookingCreateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(PermissionChecker("bookings:create"))
):
    try:
        return booking_service.create_booking(db, booking_in, actor)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

@router.get("/", response_model=List[BookingSchema], dependencies=[Depends(PermissionChecker("bookings:read"))])
def get_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()
