from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from packages.core.config import settings

# Async Engine (for API)
async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    future=True,
)

# Sync Engine (for Bot and Migration logic)
sync_engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql+asyncpg://", "postgresql://"),
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)

async def get_db():
    """Dependency for FastAPI endpoints."""
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
    async_session = sessionmaker(
        async_engine, class_=_AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
