import pytest

from app.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    s = Settings(_env_file=None)
    assert s.gemini_api_key == "test-key-123"
    assert s.gemini_model == "gemini-3.5-flash-lite"


def test_the_three_models_are_distinct():
    """Quota is metered per model, so chat, fallback and analytics must differ.

    Collapsing any two makes them share one daily cap, which is the constraint
    that actually binds on the free tier.
    """
    s = Settings(_env_file=None, gemini_api_key="k")
    assert len({s.gemini_model, s.gemini_fallback_model, s.gemini_analytics_model}) == 3


def test_settings_fails_fast_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        Settings(_env_file=None)


def test_model_is_overridable(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    assert Settings(_env_file=None).gemini_model == "gemini-2.5-flash"
