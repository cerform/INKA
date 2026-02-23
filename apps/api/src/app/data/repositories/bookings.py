from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.bookings.repository import BookingRepository
from packages.core.models import Booking


class SqlAlchemyBookingRepository(BookingRepository):
    async def list_by_tenant(self, db: AsyncSession, tenant_id: int) -> list[Booking]:
        result = await db.execute(
            select(Booking).where(Booking.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, booking: Booking) -> Booking:
        db.add(booking)
        await db.flush()
        return booking
