from fastapi import APIRouter

from app.domains.bookings.api import router as bookings_router
from app.domains.masters.api import router as masters_router
from app.domains.clients.api import router as clients_router
from app.domains.defects.api import router as defects_router
from app.domains.tenants.api import router as tenants_router

router = APIRouter()
router.include_router(bookings_router, prefix="/bookings", tags=["Bookings"])
router.include_router(masters_router, prefix="/masters", tags=["Masters"])
router.include_router(clients_router, prefix="/clients", tags=["Clients"])
router.include_router(defects_router, prefix="/defects", tags=["Defects"])
router.include_router(tenants_router, prefix="/tenants", tags=["Tenants"])
