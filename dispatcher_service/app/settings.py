from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://user:password@database:5432/taxi_dispatch_db"

    ASSIGN_TIMEOUT_SEC: float = 5.0
    ASSIGN_RETRIES: int = 2

    HEARTBEAT_TTL_SEC: int = 30
    HEARTBEAT_SWEEP_INTERVAL_SEC: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
