from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_actor_id, get_db_session, get_tenant_id
from app.api.dtos.bookings import BookingCreateDTO, BookingDTO
from app.data.repositories.bookings import SqlAlchemyBookingRepository
from app.domain.bookings.service import BookingService

router = APIRouter()
booking_service = BookingService(repo=SqlAlchemyBookingRepository())


@router.get("/", response_model=list[BookingDTO])
async def list_bookings(
    db: AsyncSession = Depends(get_db_session),
    tenant_id: int = Depends(get_tenant_id),
) -> list[BookingDTO]:
    return await booking_service.list_bookings(db=db, tenant_id=tenant_id)


@router.post("/", response_model=BookingDTO, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreateDTO,
    db: AsyncSession = Depends(get_db_session),
    tenant_id: int = Depends(get_tenant_id),
    actor_id: int | None = Depends(get_actor_id),
) -> BookingDTO:
    return await booking_service.create_booking(
        db=db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        payload=payload,
    )
