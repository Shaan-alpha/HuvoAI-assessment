import pytest

from app.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    s = Settings(_env_file=None)
    assert s.gemini_api_key == "test-key-123"
    assert s.gemini_model == "gemini-3.8-flash"


def test_settings_fails_fast_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        Settings(_env_file=None)


def test_model_is_overridable(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    assert Settings(_env_file=None).gemini_model == "gemini-2.5-flash"
