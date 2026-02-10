from typing import Any
from packages.core.domains.bookings.models import Booking
from packages.core.domains.bookings.conflict import has_conflict
from packages.core.domains.audit.service import audit_service

class BookingService:
    def create_booking(self, db: Any, data: Any, actor: Any) -> Booking:
        if has_conflict(db, data.master_id, data.start_time, data.end_time):
            raise ValueError("Time slot is already occupied")

        booking = Booking(
            client_id=data.client_id,
            master_id=data.master_id,
            start_time=data.start_time,
            end_time=data.end_time,
            status="planned",
            created_by=actor.id,
        )
        db.add(booking)
        db.flush() # Get the ID before logging
        
        audit_service.log(db, actor.id, "booking.create", booking.id)
        return booking

booking_service = BookingService()
