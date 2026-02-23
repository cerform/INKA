from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from packages.core.models import Booking, BookingStatus, Master, User
from packages.core.services.calendar_service import calendar_service

class BookingService:
    """
    Service for managing the booking lifecycle with safety checks.
    """

    def create_booking(
        self,
        db: Session,
        tenant_id: int,
        client_id: int,
        master_id: int,
        service_id: int,
        start_time: datetime,
        end_time: datetime,
        created_by: int
    ) -> Booking:
        """
        Creates a new booking ensuring no double-booking occurs.
        Uses SELECT FOR UPDATE on the master record to serialize 
        booking attempts for that master.
        """
        # 1. Lock the master record to prevent race conditions for this specific master
        # (Alternatively, we could use an advisory lock on master_id)
        master = db.execute(
            select(Master).where(Master.id == master_id).with_for_update()
        ).scalar_one_or_none()
        
        if not master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Master not found"
            )

        # 2. Check availability one more time while holding the lock
        # This ensures that no other booking was created in the millisecond since the client saw the slot.
        # Note: calendar_service.get_available_slots can be used, but a simpler check is faster.
        overlapping = db.execute(
            select(Booking).where(
                Booking.tenant_id == tenant_id,
                Booking.master_id == master_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                Booking.start_time < end_time,
                Booking.end_time > start_time
            )
        ).scalars().all()

        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This slot has just been taken"
            )

        # 3. Create the booking
        booking = Booking(
            tenant_id=tenant_id,
            client_id=client_id,
            master_id=master_id,
            service_id=service_id,
            start_time=start_time,
            end_time=end_time,
            created_by=created_by,
            status=BookingStatus.PENDING
        )
        db.add(booking)
        
        # In M4, we might also record stock deduction placeholder here if needed
        
        return booking

    def complete_booking(
        self,
        db: Session,
        tenant_id: int,
        booking_id: int
    ) -> Booking:
        """
        Marks a booking as completed and deducts materials.
        In a real scenario, we'd have a mapping of Service -> Materials.
        For now, we implement a placeholder for deduction logic.
        """
        booking = db.get(Booking, booking_id)
        if not booking or booking.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking.status != BookingStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Only confirmed bookings can be completed")

        booking.status = BookingStatus.COMPLETED
        
        # 2. Automatic Stock Deduction (M4)
        from packages.core.models.service_material import ServiceMaterial
        from packages.core.services.inventory_service import inventory_service
        
        # Find all materials associated with this booking's service
        materials_to_deduct = db.execute(
            select(ServiceMaterial).where(
                ServiceMaterial.tenant_id == tenant_id,
                ServiceMaterial.service_id == booking.service_id
            )
        ).scalars().all()
        
        for sm in materials_to_deduct:
            material = inventory_service.adjust_stock(
                db=db,
                tenant_id=tenant_id,
                material_id=sm.material_id,
                delta=-sm.quantity_required,
                reason=f"Booking {booking_id} completion deduction",
                booking_id=booking_id
            )
            
            # 3. Check for Low Stock Alert
            if material.stock_quantity <= material.reorder_threshold:
                # Find the tenant's admins (User with role 'ADMIN' or 'OWNER')
                # In a real app, this might becached or handled via a dedicated NotifyAdmin service.
                admins = db.execute(
                    select(User).where(
                        User.tenant_id == tenant_id,
                        User.is_active == True
                        # Add role filter if Role model is clear, 
                        # otherwise default to all active users for the tenant
                    )
                ).scalars().all()
                
                # 4. Notify Admins
                # In a real app, 'notification_service' would be injected.
                # Here we show the intended call.
                from packages.core.services.notification_service import NotificationService
                
                for admin in admins:
                    # Example: notification_service.send_low_stock_notification(...)
                    # We skip the actual await call here as it requires a Bot instance 
                    # that isn't typically available in the core service layer without DI.
                    pass
        
        return booking

booking_service = BookingService()
