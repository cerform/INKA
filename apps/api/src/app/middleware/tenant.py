from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from packages.core.models.tenant import Tenant, TenantStatus
from packages.db.session import get_db
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    SKIP_EXACT = {"/health", "/healthz", "/readyz", "/ready", "/version", "/", "/docs", "/redoc", "/openapi.json"}
    SKIP_PREFIXES = ("/health/", "/api/v1/tenants/config/")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Skip tenant resolution for health checks, probes, docs, and public config
        if path in self.SKIP_EXACT or any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return await call_next(request)

        host = request.headers.get("host", "")
        # Basic logic: host is tenant-slug.domain.com or just tenant-slug (local)
        # In production, we might use a dedicated header from the load balancer
        
        tenant_slug = host.split(".")[0]
        
        # If it's the admin domain, we might treat it as a platform tenant or skip isolation
        if tenant_slug == "admin":
            request.state.tenant_id = None # Global access
            request.state.is_platform_admin = True
            return await call_next(request)

        # Resolve tenant from DB
        async for session in get_db():
            result = await session.execute(
                select(Tenant).where(Tenant.slug == tenant_slug)
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                # Try fallback to domain mapping
                result = await session.execute(
                    select(Tenant).where(Tenant.domain == host)
                )
                tenant = result.scalar_one_or_none()

            if not tenant:
                logger.warning(f"Tenant not found for host: {host}")
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            if tenant.status != TenantStatus.ACTIVE:
                logger.warning(f"Tenant {tenant.slug} is {tenant.status}")
                raise HTTPException(status_code=403, detail=f"Tenant is {tenant.status}")

            request.state.tenant_id = tenant.id
            request.state.tenant_slug = tenant.slug
            break

        response = await call_next(request)
        return response
