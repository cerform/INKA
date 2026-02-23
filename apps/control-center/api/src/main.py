"""CI/CD Control Center — FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base
from .routes import repos, services, runs, deployments, approvals, webhooks, audit, dora

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("control-center")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (Alembic handles migrations in production)
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Control Center API started — tables verified")
    yield
    logger.info("Control Center API shutting down")


app = FastAPI(
    title="INKA CI/CD Control Center API",
    version="1.0.0",
    description=(
        "Single pane of glass for pipeline runs, deployments, approvals, "
        "DORA metrics, and audit logs."
    ),
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
origins = (
    ["*"] if settings.ENVIRONMENT == "development"
    else settings.ALLOWED_ORIGINS.split(",")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(repos.router)
app.include_router(services.router)
app.include_router(runs.router)
app.include_router(deployments.router)
app.include_router(approvals.router)
app.include_router(webhooks.router)
app.include_router(audit.router)
app.include_router(dora.router)


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "cicd-control-center-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["health"])
async def root():
    return {"message": "INKA CI/CD Control Center API — visit /docs"}
