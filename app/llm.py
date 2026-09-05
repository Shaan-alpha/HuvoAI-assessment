import logging
import threading
import time
from typing import Callable

from google import genai
from google.genai import types
from pydantic import BaseModel

from app import booking
from app.config import get_settings
from app.prompt import compose
from app.session import Session

log = logging.getLogger(__name__)

# The free tier allows only a handful of requests per minute. Serialise calls and
# hold a floor between them so a burst — a scenario suite, or an impatient
# clicker — degrades into a queue instead of a wall of 429s.
MIN_SECONDS_BETWEEN_CALLS = 4.0

# Gemini 3.x reserves a thinking budget before emitting any visible text. Measured
# on gemini-3.8-flash: 88 thinking tokens to produce a 1-token reply, and an empty
# response entirely when max_output_tokens was small. A sales agent that must feel
# live on a phone call cannot pay that. LOW is the floor this model accepts —
# MINIMAL is rejected with 400 INVALID_ARGUMENT.
THINKING_LEVEL = "LOW"


class _Throttle:
    """Process-wide floor on the interval between API calls."""

    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last
            if self._last and elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last = time.monotonic()


_throttle = _Throttle(MIN_SECONDS_BETWEEN_CALLS)


def to_contents(session: Session) -> list[types.Content]:
    """Convert our stored turns into SDK history."""
    return [
        types.Content(role=t.role, parts=[types.Part(text=t.content)])
        for t in session.turns
    ]


def make_booking_tool(session: Session) -> Callable[[str, str, str, str], str]:
    """Build a booking tool bound to one session, so the outcome is recorded.

    The SDK derives the tool schema from the signature and docstring below, so
    there is no hand-written function declaration to drift out of sync.
    """

    def book_site_visit(name: str, phone: str, date: str, time_slot: str) -> str:
        """Books a site visit at Northstar One. Call this only after confirming every detail with the customer.

        Args:
            name: The customer's full name.
            phone: The customer's 10-digit Indian mobile number, digits only.
            date: The visit date in YYYY-MM-DD format.
            time_slot: The one-hour slot as HH:MM-HH:MM, between 10:00 and 18:00.
        """
        result = booking.attempt(name, phone, date, time_slot)
        session.bookings.append(
            result.reference if result.ok else f"FAILED: {date} {time_slot}"
        )
        return result.message

    return book_site_visit


class GeminiClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model
        self._fallback = settings.gemini_fallback_model

    def _config(self, session: Session, channel: str) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=compose(channel),
            tools=[make_booking_tool(session)],
            thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
            temperature=0.7,
        )

    def chat(self, session: Session, message: str, channel: str) -> str:
        """Send one turn and return the agent's reply.

        Uses client.chats rather than models.generate_content: the SDK warns
        that automatic function calling is unsupported on the latter. History
        is passed in from our own Session, which stays the source of truth.
        """
        config = self._config(session, channel)
        history = to_contents(session)

        for model in (self._model, self._fallback):
            try:
                _throttle.wait()
                chat = self._client.chats.create(
                    model=model, config=config, history=history
                )
                reply = (chat.send_message(message).text or "").strip()
                if reply:
                    return reply
                log.warning("Model %s returned an empty reply", model)
            except Exception:
                log.warning("Model %s failed; trying next", model, exc_info=True)

        return (
            "Sorry, I'm having trouble connecting right now. "
            "Can I have someone from our team call you back shortly?"
        )

    def extract(self, transcript: str, schema: type[BaseModel], instruction: str) -> BaseModel:
        """Extract a structured record from a finished transcript.

        The schema is deliberately NOT restated in the prompt — the SDK docs warn
        that duplicating it degrades output quality. The instruction carries the
        scoring rubric and nothing about JSON shape.
        """
        _throttle.wait()
        response = self._client.models.generate_content(
            model=self._model,
            contents=f"{instruction}\n\n<transcript>\n{transcript}\n</transcript>",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
                temperature=0.0,
            ),
        )
        return response.parsed
