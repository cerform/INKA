from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.session import get_db


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session
