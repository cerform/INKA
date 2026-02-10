from fastapi import FastAPI
from src.app.settings import settings
from src.app.health import router as health_router
from src.app.logging import setup_logging
from src.app.domains.clients.api import router as clients_router
from src.app.domains.masters.api import router as masters_router
from src.app.domains.bookings.api import router as bookings_router
from src.app.domains.support.api import router as support_router

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    app.include_router(health_router, prefix="/health")
    app.include_router(clients_router, prefix="/api/v1/clients", tags=["Clients"])
    app.include_router(masters_router, prefix="/api/v1/masters", tags=["Masters"])
    app.include_router(bookings_router, prefix="/api/v1/bookings", tags=["Bookings"])
    app.include_router(support_router, prefix="/api/v1/support", tags=["Support"])

    @app.get("/")
    async def root():
        return {"message": "Welcome to INKA Admin API", "env": settings.env}

    return app

app = create_app()
