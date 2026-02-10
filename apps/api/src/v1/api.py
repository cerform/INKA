from fastapi import APIRouter
from src.app.api.v1.endpoints import health
from src.app.api.v1.endpoints.admin import roles

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
