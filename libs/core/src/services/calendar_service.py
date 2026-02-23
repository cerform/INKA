from datetime import datetime, date, time, timedelta, timezone
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from packages.core.models import (
    Booking, 
    WorkingHours, 
    TimeOff, 
    SalonWorkingHours, 
    SalonClosedDay, 
    Master, 
    Service
)

class CalendarService:
    """
    Service for managing salon and master calendars, 
    computing available slots, and validating bookings.
    """

    def get_available_slots(
        self, 
        db: Session, 
        tenant_id: int, 
        master_id: int, 
        service_id: int, 
        search_date: date
    ) -> List[Tuple[datetime, datetime]]:
        """
        Calculates available booking slots for a given master and service on a specific date.
        
        Logic:
        1. Get Salon Working Hours for the day.
        2. Get Master Working Hours for the day.
        3. Check if Salon is closed on this date.
        4. Calculate the intersection of Salon and Master hours.
        5. Retrieve existing Bookings and Master TimeOff for the date.
        6. Generate slots of 'service_duration' within the intersection, 
           skipping intervals blocked by bookings or time-off.
        """
        # 1. Fetch Service details
        service = db.get(Service, service_id)
        if not service or service.tenant_id != tenant_id:
            return []
        
        duration = timedelta(minutes=service.duration_minutes)

        # 2. Check if Salon is closed
        closed_day = db.execute(
            select(SalonClosedDay).where(
                SalonClosedDay.tenant_id == tenant_id,
                SalonClosedDay.date == search_date
            )
        ).scalar_one_or_none()
        
        if closed_day:
            return []

        # 3. Get Day of Week (0=Monday, 6=Sunday)
        weekday = search_date.weekday()

        # 4. Fetch Salon and Master Working Hours
        salon_hours = db.execute(
            select(SalonWorkingHours).where(
                SalonWorkingHours.tenant_id == tenant_id,
                SalonWorkingHours.day_of_week == weekday,
                SalonWorkingHours.is_closed == False
            )
        ).scalar_one_or_none()

        master_hours = db.execute(
            select(WorkingHours).where(
                WorkingHours.tenant_id == tenant_id,
                WorkingHours.master_id == master_id,
                WorkingHours.day_of_week == weekday,
                WorkingHours.is_active == True
            )
        ).scalar_one_or_none()

        if not salon_hours or not master_hours:
            return []

        # 5. Determine the Time Bounds (Intersection)
        start_time = max(salon_hours.open_time, master_hours.start_time)
        end_time = min(salon_hours.close_time, master_hours.end_time)

        if start_time >= end_time:
            return []

        # Convert to full datetimes for the specific date (stored as UTC)
        # Note: In production, we'd handle the tenant's specific timezone here.
        # For MVP, we assume UTC logic for slot generation.
        day_start = datetime.combine(search_date, start_time, tzinfo=timezone.utc)
        day_end = datetime.combine(search_date, end_time, tzinfo=timezone.utc)

        # 6. Fetch Occupied Intervals (Bookings and TimeOff)
        # Existing Bookings
        bookings = db.execute(
            select(Booking).where(
                Booking.tenant_id == tenant_id,
                Booking.master_id == master_id,
                Booking.status.in_(["pending", "confirmed"]),
                Booking.start_time < day_end,
                Booking.end_time > day_start
            )
        ).scalars().all()

        # Master TimeOff
        time_offs = db.execute(
            select(TimeOff).where(
                TimeOff.tenant_id == tenant_id,
                TimeOff.master_id == master_id,
                TimeOff.start_time < day_end,
                TimeOff.end_time > day_start
            )
        ).scalars().all()

        # Combine all blocked intervals
        blocked_intervals: List[Tuple[datetime, datetime]] = []
        for b in bookings:
            blocked_intervals.append((b.start_time, b.end_time))
        for t in time_offs:
            blocked_intervals.append((t.start_time, t.end_time))
        
        # Sort blocked intervals by start time
        blocked_intervals.sort(key=lambda x: x[0])

        # 7. Generate Slots
        available_slots = []
        current_time = day_start
        
        while current_time + duration <= day_end:
            slot_end = current_time + duration
            is_blocked = False
            
            for b_start, b_end in blocked_intervals:
                # If slot overlaps with any blocked interval
                if current_time < b_end and slot_end > b_start:
                    is_blocked = True
                    # Jump current_time to end of blocked interval to optimize
                    current_time = b_end
                    break
            
            if not is_blocked:
                available_slots.append((current_time, slot_end))
                # Move forward by 30 mins or duration (stepping logic)
                current_time += timedelta(minutes=30) 
            
        return available_slots

calendar_service = CalendarService()
