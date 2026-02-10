from sqlalchemy import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
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
