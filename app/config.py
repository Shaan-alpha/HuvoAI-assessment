from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # validate_default is required: without it the validator below never runs
    # when the variable is simply absent, which is the exact case it exists to catch.
    gemini_api_key: str = Field(default="", validate_default=True)
    # Free-tier quota is metered per model, and the daily cap is the binding
    # constraint: gemini-3.8-flash allows only 20 requests per DAY, which one
    # scenario run exhausts twice over. The lite tier is far more generous.
    #
    # 3.5-flash-lite was chosen on measured behaviour, not just quota: asked
    # "bhai 3 BHK ka rate kya hai?" it answers in romanized Hinglish, while
    # 3.1-flash-lite answers the same question in English and fails the
    # script-mirroring requirement outright.
    gemini_model: str = Field(default="gemini-3.5-flash-lite")

    # Falls back UP in quality, not down: 3.8-flash is the stronger model but
    # has the tighter daily cap, so it is held in reserve rather than led with.
    gemini_fallback_model: str = Field(default="gemini-3.8-flash")

    # Its own bucket again, so the end-of-conversation extraction never competes
    # with the conversation. Language fidelity does not matter for structured
    # extraction at temperature 0, so the weaker lite model is fine here.
    gemini_analytics_model: str = Field(default="gemini-3.1-flash-lite")

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
