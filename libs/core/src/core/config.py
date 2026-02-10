from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "INKA Admin"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: str | None = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict[str, any]) -> str:
        if isinstance(v, str):
            return v
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        ))

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_URL: str | None = None

    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: str | None, values: dict[str, any]) -> str:
        if isinstance(v, str):
            return v
        return str(RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
        ))

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: AnyHttpUrl | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
