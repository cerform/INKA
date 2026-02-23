from typing import AsyncGenerator, Optional

from fastapi import Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.session import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


def get_tenant_id(request: Request) -> int:
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None and not getattr(request.state, "is_platform_admin", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant could not be resolved. Please use correct domain.",
        )
    return tenant_id


def get_actor_id(x_actor_id: Optional[int] = Header(default=None)) -> Optional[int]:
    return x_actor_id
