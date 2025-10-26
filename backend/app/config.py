from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Dota Stats"
    DEBUG: bool = False
    LOG_LEVEL: Literal["INFO", "DEBUG"] = "INFO"

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # RabbitMQ / Celery
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672

    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"db+{self.DATABASE_URL}"

    # Steam API
    STEAM_API_KEY: str
    STEAM_OPENID_CALLBACK_URL: str

    # API Configuration
    API_PROVIDER: Literal["valve", "opendota"] = "valve"
    VALVE_API_BASE_URL: str = "https://api.steampowered.com"
    OPENDOTA_API_BASE_URL: str = "https://api.opendota.com/api"

    # Sync Configuration
    SYNC_INTERVAL_MINUTES: int = 60
    VALVE_RATE_LIMIT_DELAY: float = 7.0  # seconds between Valve API calls
    OPENDOTA_RATE_LIMIT_DELAY: float = 1.0  # seconds between OpenDota API calls

    # Security
    SECRET_KEY: str
    SESSION_COOKIE_NAME: str = "dota_stats_session"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
