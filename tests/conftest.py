import pytest
from fastapi.testclient import TestClient

from app.analytics import LeadAnalytics
from app.main import app, get_llm, get_store
from app.session import InMemoryStore


class FakeLLM:
    """Deterministic stand-in so API tests never touch the network."""

    def __init__(self):
        self.last_channel = None
        self.last_message = None

    def chat(self, session, message, channel):
        self.last_channel = channel
        self.last_message = message
        return f"[{channel}] echo: {message}"

    def extract(self, transcript, schema, instruction):
        lines = [ln for ln in transcript.splitlines() if ln.strip()]
        return LeadAnalytics(summary=f"turns={len(lines)}")


@pytest.fixture
def fake_llm():
    return FakeLLM()


@pytest.fixture
def client(fake_llm):
    store = InMemoryStore()
    app.dependency_overrides[get_llm] = lambda: fake_llm
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()
