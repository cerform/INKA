from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from functools import lru_cache

def _get_db_uri():
    from packages.core.config import settings
    return str(settings.SQLALCHEMY_DATABASE_URI)

@lru_cache()
def _get_async_engine():
    uri = _get_db_uri()
    return create_async_engine(
        uri.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
        future=True,
    )

@lru_cache()
def _get_sync_engine():
    uri = _get_db_uri()
    return create_engine(
        uri.replace("postgresql+asyncpg://", "postgresql://"),
        echo=False,
        future=True,
    )

def SessionLocal():
    engine = _get_sync_engine()
    _SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    return _SessionLocal()

async def get_db():
    """Dependency for FastAPI endpoints."""
    engine = _get_async_engine()
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
