import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.settings import settings
from app.health import probe_router, router as health_router
from app.api.v1.router import router as v1_router
from app.middleware.tenant import TenantMiddleware
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Observability imports
from packages.observability import (
    setup_logging,
    setup_tracing,
    setup_sentry,
    get_logger,
    TraceContextMiddleware,
)

try:
    from landing import router as landing_router
except ImportError:
    landing_router = None


def create_app() -> FastAPI:
    # 1. Structured logging (replaces basicConfig)
    setup_logging(
        log_level=settings.log_level,
        environment=settings.env,
        service_name="inka-api",
    )

    # 2. Distributed tracing (OpenTelemetry)
    setup_tracing(service_name="inka-api", environment=settings.env)

    # 3. Error tracking (Sentry) — no-op if dsn is empty
    setup_sentry(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        version=settings.version,
    )

    logger = get_logger(__name__)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )


    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # In production, restrict this to *.inka.app
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trace context middleware (must be before TenantMiddleware)
    app.add_middleware(TraceContextMiddleware)
    app.add_middleware(TenantMiddleware)

    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(probe_router, tags=["Health"])
    app.include_router(v1_router, prefix=settings.api_v1_str)
    
    # Include landing page
    if landing_router:
        app.include_router(landing_router, tags=["Landing"])

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request, exc):
        logger.error("Database error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Database operation failed"},
        )

    @app.get("/")
    async def root():
        return {
            "service": settings.project_name,
            "version": settings.version,
            "env": settings.env,
            "status": "running"
        }

    logger.info("INKA API started", env=settings.env)
    return app


app = create_app()
