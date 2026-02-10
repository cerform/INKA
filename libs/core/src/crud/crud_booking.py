from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from packages.core.crud.base import CRUDBase
from packages.core.models.booking import Booking, BookingStatus
from packages.core.schemas.booking import BookingCreate, BookingUpdate

class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    async def get_conflicts(
        self, db: AsyncSession, *, master_id: int, start_time: datetime, end_time: datetime, exclude_id: Optional[int] = None
    ) -> List[Booking]:
        """
        Returns a list of bookings that overlap with the given time range for a specific master.
        """
        query = select(Booking).where(
            and_(
                Booking.master_id == master_id,
                Booking.status != BookingStatus.CANCELLED,
                or_(
                    and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                    and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                    and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
                )
            )
        )
        if exclude_id:
            query = query.where(Booking.id != exclude_id)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def create_with_conflict_check(
        self, db: AsyncSession, *, obj_in: BookingCreate
    ) -> Tuple[Optional[Booking], Optional[str]]:
        # 1. Check for conflicts
        conflicts = await self.get_conflicts(
            db, 
            master_id=obj_in.master_id, 
            start_time=obj_in.start_time, 
            end_time=obj_in.end_time
        )
        if conflicts:
            return None, "Time slot is already occupied"

        # 2. TODO: Check master availability (WorkingHours)
        
        # 3. Create booking
        return await self.create(db, obj_in=obj_in), None

booking = CRUDBooking(Booking)
