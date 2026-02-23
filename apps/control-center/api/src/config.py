from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql://cicd:cicd@localhost:5432/cicd_control"

    # GitHub Integration
    GITHUB_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_API_URL: str = "https://api.github.com"

    # GCP
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "europe-west1"
    ARTIFACT_REGISTRY_HOST: str = "europe-west1-docker.pkg.dev"
    ARTIFACT_REPO: str = "inka-repo"

    # App
    SECRET_KEY: str = "changeme-in-production"
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "*"


settings = Settings()
