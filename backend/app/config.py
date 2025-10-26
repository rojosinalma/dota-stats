from pydantic_settings import BaseSettings
from typing import Literal, Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Dota Stats"
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
    OPENDOTA_API_KEY: Optional[str] = None  # Optional API key for higher rate limits

    # Sync Configuration
    SYNC_INTERVAL_MINUTES: int = 60
    VALVE_RATE_LIMIT_DELAY: float = 7.0  # seconds between Valve API calls

    @property
    def OPENDOTA_RATE_LIMIT_DELAY(self) -> float:
        """
        Calculate rate limit delay for OpenDota based on API key presence.
        - With API key: 1200 calls/min = 0.05s delay
        - Without API key: 60 calls/min = 1.0s delay
        """
        if self.OPENDOTA_API_KEY:
            return 0.05  # 1200 calls per minute
        return 1.0  # 60 calls per minute

    # Security
    SECRET_KEY: str
    SESSION_COOKIE_NAME: str = "dota_stats_session"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
