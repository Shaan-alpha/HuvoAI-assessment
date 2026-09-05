from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # validate_default is required: without it the validator below never runs
    # when the variable is simply absent, which is the exact case it exists to catch.
    gemini_api_key: str = Field(default="", validate_default=True)
    gemini_model: str = Field(default="gemini-3.8-flash")
    gemini_fallback_model: str = Field(default="gemini-2.5-flash")

    @field_validator("gemini_api_key")
    @classmethod
    def _require_key(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add a key "
                "from https://aistudio.google.com/apikey"
            )
        return v.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
