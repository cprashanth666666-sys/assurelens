"""Application settings, loaded from the environment only.

Secrets never appear in code, and no default is supplied that would silently
"work" in production. A missing DATABASE_URL must fail loudly at startup, not
present itself as a database that happens to be down.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required, deliberately. A default pointing at localhost would let a
    # missing or unbound environment variable start the app successfully and
    # report `database: down` — indistinguishable from a sleeping database,
    # so the operator waits for a cold start that never finishes. The local
    # value lives in .env.example, where it cannot reach production.
    database_url: str

    # Comma-separated. Locked to the frontend origin — never "*". [TRD 9]
    cors_allow_origins: str = "http://localhost:3000"

    # Suite 3 reaches the deliberately-vulnerable target over HTTP only. [TRD 1.2]
    target_service_url: str = "http://localhost:8001"

    # Every run records the seed it used, so results are reproducible. [TRD 3.4]
    default_seed: int = 42

    log_level: str = "INFO"
    engine_version: str = "0.1.0"

    @field_validator("target_service_url")
    @classmethod
    def _ensure_scheme(cls, value: str) -> str:
        """Normalise a scheme-less host into a URL.

        Render's `fromService` env-var injection yields `host:port` with no
        scheme. Passed to httpx unchanged, that raises UnsupportedProtocol —
        and every probe control would then gate on G8_TARGET_UNREACHABLE,
        which looks exactly like correct, designed behaviour. A configuration
        error masquerading as an assurance verdict is the one failure mode
        this product must not have, so the scheme is repaired here rather
        than trusted to the deployment.
        """
        value = value.strip().rstrip("/")
        if not value:
            raise ValueError("target_service_url must not be empty")
        if "://" not in value:
            # Bare localhost is plain HTTP; anything else is assumed public.
            local = value.startswith(("localhost", "127.0.0.1", "target_service"))
            value = f"{'http' if local else 'https'}://{value}"
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment
