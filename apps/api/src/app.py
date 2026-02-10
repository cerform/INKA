from fastapi import FastAPI
from contextlib import asynccontextmanager
from packages.core.config import settings
from apps.api.v1.api import api_router

from apps.bot.main import bot, set_webhook

from packages.core.logging import setup_logging
from apps.api.deps.logging_middleware import LoggingMiddleware

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up INKA Admin...")
    await set_webhook()
    yield
    # Shutdown
    print("Shutting down INKA Admin...")
    await bot.session.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to INKA Admin API"}
