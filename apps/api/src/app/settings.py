from packages.core.config import settings as core_settings
import os

class Settings:
    def __init__(self):
        self.env = core_settings.ENVIRONMENT
        self.log_level = core_settings.LOG_LEVEL
        self.project_name = core_settings.PROJECT_NAME
        self.version = core_settings.VERSION
        self.api_v1_str = core_settings.API_V1_STR
        self.database_url = core_settings.DATABASE_URL
        self.telegram_bot_token = core_settings.TELEGRAM_BOT_TOKEN
        self.sentry_dsn = os.environ.get("SENTRY_DSN", "")

settings = Settings()
