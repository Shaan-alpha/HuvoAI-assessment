from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from app.analytics import LeadAnalytics, extract_analytics
from app.llm import ExtractionError, GeminiClient
from app.session import InMemoryStore, SessionStore, Turn

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Northstar Homes — AI Sales Agent")


@lru_cache
def get_store() -> SessionStore:
    return InMemoryStore()


@lru_cache
def get_llm() -> GeminiClient:
    # Constructed lazily so importing the app does not require an API key —
    # the deterministic test suite overrides this dependency entirely.
    return GeminiClient()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    channel: Literal["chat", "voice"] = "chat"

    @field_validator("message")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be blank")
        return v.strip()


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    store: Annotated[SessionStore, Depends(get_store)],
    llm: Annotated[GeminiClient, Depends(get_llm)],
) -> ChatResponse:
    session = store.get_or_create(body.session_id)
    reply = llm.chat(session, body.message, body.channel)
    session.turns.append(Turn(role="user", content=body.message))
    session.turns.append(Turn(role="model", content=reply))
    return ChatResponse(session_id=session.id, reply=reply)


@app.post("/api/analytics/{session_id}", response_model=LeadAnalytics)
def analytics(
    session_id: str,
    store: Annotated[SessionStore, Depends(get_store)],
    llm: Annotated[GeminiClient, Depends(get_llm)],
) -> LeadAnalytics:
    # `get`, not `get_or_create`: an unknown id must not mint a session that
    # then lives for the process lifetime. An empty record still beats a 404.
    session = store.get(session_id)
    if session is None:
        return LeadAnalytics()
    try:
        return extract_analytics(llm, session)
    except ExtractionError as err:
        # A zeroed record would render in the UI as a real reading of the
        # conversation. Failing loudly is the same principle the schema exists
        # to serve: never let an absence pass for a finding.
        raise HTTPException(status_code=503, detail=f"Lead extraction failed: {err}") from err


@app.post("/api/reset/{session_id}")
def reset(
    session_id: str,
    store: Annotated[SessionStore, Depends(get_store)],
) -> dict[str, bool]:
    store.reset(session_id)
    return {"ok": True}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
