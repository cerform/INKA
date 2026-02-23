from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dtos.bookings import BookingCreateDTO
from app.domain.bookings.repository import BookingRepository
from packages.core.models import Booking


class BookingService:
    def __init__(self, repo: BookingRepository) -> None:
        self._repo = repo

    async def list_bookings(self, db: AsyncSession, tenant_id: int) -> list[Booking]:
        return await self._repo.list_by_tenant(db=db, tenant_id=tenant_id)

    async def create_booking(
        self,
        db: AsyncSession,
        tenant_id: int,
        actor_id: int | None,
        payload: BookingCreateDTO,
    ) -> Booking:
        booking = Booking(
            tenant_id=tenant_id,
            client_id=payload.client_id,
            master_id=payload.master_id,
            service_id=payload.service_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            notes=payload.notes,
        )
        booking = await self._repo.create(db=db, booking=booking)
        await db.commit()
        await db.refresh(booking)
        return booking
