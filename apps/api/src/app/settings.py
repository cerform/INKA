from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str = "dev"
    log_level: str = "INFO"

    database_url: str = "postgresql://user:pass@localhost:5432/db"
    telegram_bot_token: str = "your_bot_token"
    project_name: str = "INKA Admin"
    api_v1_str: str = "/api/v1"

    class Config:
        env_file = ".env"

settings = Settings()
