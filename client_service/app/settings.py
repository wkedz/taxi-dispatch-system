from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DISPATCHER_BASE_URL: str = "http://dispatcher:8000"
    FREQUENCY_SECONDS: int = 5
    GRID_SIZE: int = 100
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
