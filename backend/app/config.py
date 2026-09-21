"""Application settings, loaded from the environment only.

Secrets never appear in code or in defaults that would work in production.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://assurelens:change-me-locally@localhost:5432/assurelens"

    # Comma-separated. Locked to the frontend origin — never "*". [TRD 9]
    cors_allow_origins: str = "http://localhost:3000"

    # Suite 3 reaches the deliberately-vulnerable target over HTTP only. [TRD 1.2]
    target_service_url: str = "http://localhost:8001"

    # Every run records the seed it used, so results are reproducible. [TRD 3.4]
    default_seed: int = 42

    log_level: str = "INFO"
    engine_version: str = "0.1.0"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
