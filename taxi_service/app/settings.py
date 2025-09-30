from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DISPATCHER_BASE_URL: HttpUrl = "http://dispatcher:8000"

    TAXI_SERVICE_PORT: int = 8081
    TAXI_HOST: str = "0.0.0.0"

    PUBLIC_CALLBACK_URL: HttpUrl | None = None

    TIME_SCALE: float = 1.0
    SPEED_MIN: int = 1
    SPEED_MAX: int = 3

    GRID_SIZE: int = 100

    HEARTBEAT_INTERVAL_SEC: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
