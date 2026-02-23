from typing import Protocol
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Booking


class BookingRepository(Protocol):
    async def list_by_tenant(self, db: AsyncSession, tenant_id: int) -> list[Booking]:
        ...

    async def create(self, db: AsyncSession, booking: Booking) -> Booking:
        ...
