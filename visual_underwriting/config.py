from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VISUAL_UNDERWRITING_", env_file=".env", extra="ignore")

    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-3-5-sonnet-latest")
    anthropic_timeout_seconds: float = Field(default=20.0, gt=0)
    anthropic_max_retries: int = Field(default=2, ge=0)

    max_image_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    geofence_radius_meters: float = Field(default=500.0, gt=0)
    low_confidence_threshold: float = Field(default=0.65, ge=0.0, le=1.0)

    image_hash_storage: str = Field(default="memory")
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_key_prefix: str = Field(default="visual-underwriting:image-hash")
    redis_hash_ttl_seconds: int | None = Field(default=None, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
