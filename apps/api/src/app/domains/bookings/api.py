from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from app.deps.auth import get_db, get_current_user, PermissionChecker, get_tenant_id
from packages.core.models import Booking, User

router = APIRouter()

class BookingSchema(BaseModel):
    id: int
    tenant_id: int
    client_id: int
    master_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    status: str
    created_by: int | None

    model_config = ConfigDict(from_attributes=True)

class BookingCreateRequest(BaseModel):
    client_id: int
    master_id: int
    service_id: int
    start_time: datetime
    end_time: datetime

class SlotResponse(BaseModel):
    start_time: datetime
    end_time: datetime

@router.get("/available-slots", response_model=List[SlotResponse])
def get_available_slots(
    master_id: int,
    service_id: int,
    date: datetime,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    actor: User = Depends(PermissionChecker("bookings:read"))
):
    from packages.core.services.calendar_service import calendar_service
    slots = calendar_service.get_available_slots(
        db=db,
        tenant_id=tenant_id,
        master_id=master_id,
        service_id=service_id,
        search_date=date.date()
    )
    return [{"start_time": s[0], "end_time": s[1]} for s in slots]

@router.post("/", response_model=BookingSchema)
def create_booking(
    booking_in: BookingCreateRequest,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    actor: User = Depends(PermissionChecker("bookings:create"))
):
    from packages.core.services.booking_service import booking_service
    try:
        booking = booking_service.create_booking(
            db=db,
            tenant_id=tenant_id,
            created_by=actor.id,
            **booking_in.model_dump()
        )
        db.commit()
        db.refresh(booking)
        return booking
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking"
        )

@router.get("/", response_model=List[BookingSchema])
def get_bookings(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    actor: User = Depends(PermissionChecker("bookings:read"))
):
    return db.query(Booking).filter(Booking.tenant_id == tenant_id).all()
