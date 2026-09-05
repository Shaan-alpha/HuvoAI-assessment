import uuid
from typing import Protocol

from pydantic import BaseModel, Field

SPEAKERS = {"user": "Customer", "model": "Priya"}


class Turn(BaseModel):
    role: str  # "user" | "model" — matches the Gemini content roles
    content: str


class Session(BaseModel):
    id: str
    turns: list[Turn] = Field(default_factory=list)
    bookings: list[str] = Field(default_factory=list)
    channel: str = "chat"

    def transcript(self) -> str:
        """Render the conversation for the analytics extraction pass."""
        return "\n".join(f"{SPEAKERS.get(t.role, t.role)}: {t.content}" for t in self.turns)


class SessionStore(Protocol):
    """The persistence seam.

    Swapping InMemoryStore for a Redis or Postgres implementation is the only
    change needed to run more than one worker. Nothing above this interface
    knows where sessions live.
    """

    def get_or_create(self, sid: str | None) -> Session: ...

    def reset(self, sid: str) -> None: ...


class InMemoryStore:
    """Process-local session storage.

    A sales conversation is short, so the full turn history *is* the memory —
    no summarisation, no vector store, no slot-tracking state machine. Single
    process only, by design. See SessionStore for the seam.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, sid: str | None) -> Session:
        if sid is None:
            sid = uuid.uuid4().hex
        if sid not in self._sessions:
            self._sessions[sid] = Session(id=sid)
        return self._sessions[sid]

    def reset(self, sid: str) -> None:
        if sid in self._sessions:
            self._sessions[sid] = Session(id=sid)
