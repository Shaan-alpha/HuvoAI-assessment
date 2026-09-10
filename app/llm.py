import logging
import threading
import time
from datetime import date
from typing import Callable

from google import genai
from google.genai import types
from pydantic import BaseModel

from app import booking
from app.config import get_settings
from app.prompt import compose_for_turn
from app.session import BookingRecord, Session

log = logging.getLogger(__name__)


class ExtractionError(RuntimeError):
    """Every analytics model failed.

    Raised rather than returning an all-defaults record: a zeroed lead is
    indistinguishable from a real conversation that revealed nothing, and the
    whole point of this schema is that absence and invention look different.
    """


# The free tier allows 5 requests per minute per model, enforced per project
# (quota id GenerateRequestsPerMinutePerProjectPerModel-FreeTier). 12s is the
# exact floor; 13 leaves a margin for clock skew. Serialising here means a
# burst — a scenario suite, or an impatient clicker — degrades into a queue
# instead of a wall of 429s.
MIN_SECONDS_BETWEEN_CALLS = 13.0

MAX_ATTEMPTS_PER_MODEL = 2


class _Throttle:
    """A minimum interval between calls, tracked per model.

    Per model matters: quota is metered per model, so falling back to a second
    model must not inherit the first model's cooldown — otherwise the fallback
    is useless exactly when it is needed.
    """

    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._lock = threading.Lock()
        self._last: dict[str, float] = {}

    def wait(self, key: str) -> None:
        """Reserve this model's next slot, then sleep outside the lock.

        Sleeping while holding the lock would make the wait global rather than
        per model — a 13-second cooldown on the primary would stall the
        fallback and every concurrent request with it, which is the exact
        opposite of what this class exists to do.
        """
        with self._lock:
            now = time.monotonic()
            last = self._last.get(key)
            wake = max(now, last + self._min_interval) if last is not None else now
            self._last[key] = wake
        delay = wake - time.monotonic()
        if delay > 0:
            time.sleep(delay)


_throttle = _Throttle(MIN_SECONDS_BETWEEN_CALLS)


def thinking_for(model: str) -> types.ThinkingConfig:
    """Keep the model from spending its reply budget on thinking.

    Measured on gemini-3.8-flash: 88 thinking tokens to produce a 1-token reply,
    and an entirely empty response when max_output_tokens was small. A sales
    agent that must feel live on a phone call cannot pay that.

    The parameter differs by generation. thinking_level is Gemini 3.x only —
    2.x rejects it with 400 INVALID_ARGUMENT and takes a numeric budget instead.
    Getting this wrong silently breaks the fallback path.
    """
    if model.startswith("gemini-3"):
        # MINIMAL is rejected by 3.8-flash; LOW is the floor it accepts.
        return types.ThinkingConfig(thinking_level="LOW")
    return types.ThinkingConfig(thinking_budget=0)


def _retry_after(err: Exception) -> float | None:
    """Pull the server's suggested retry delay out of a 429, if present."""
    text = str(err)
    if "RESOURCE_EXHAUSTED" not in text and "429" not in text:
        return None
    marker = "'retryDelay': '"
    if marker in text:
        try:
            return float(text.split(marker)[1].split("s'")[0])
        except (IndexError, ValueError):
            pass
    return MIN_SECONDS_BETWEEN_CALLS


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
            time_slot: A one-hour slot starting on the hour, as HH:MM-HH:MM, between
                10:00 and 18:00. For example 11:00-12:00. Half-hour starts and
                longer blocks are rejected.
        """
        result = booking.attempt(name, phone, date, time_slot)
        session.bookings.append(
            BookingRecord(
                ok=result.ok,
                date=date.strip(),
                time_slot=time_slot.strip(),
                reference=result.reference,
            )
        )
        return result.message

    return book_site_visit


class GeminiClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._models = [settings.gemini_model, settings.gemini_fallback_model]
        # Own quota bucket — see Settings.gemini_analytics_model.
        self._analytics_models = [settings.gemini_analytics_model, settings.gemini_model]

    def chat(self, session: Session, message: str, channel: str) -> str:
        """Send one turn and return the agent's reply.

        Uses client.chats rather than models.generate_content: the SDK warns
        that automatic function calling is unsupported on the latter. History
        comes from our own Session, which stays the source of truth.
        """
        history = to_contents(session)
        instruction = compose_for_turn(channel, date.today())

        for model in self._models:
            config = types.GenerateContentConfig(
                system_instruction=instruction,
                tools=[make_booking_tool(session)],
                thinking_config=thinking_for(model),
                temperature=0.7,
            )
            for attempt in range(MAX_ATTEMPTS_PER_MODEL):
                try:
                    _throttle.wait(model)
                    chat = self._client.chats.create(
                        model=model, config=config, history=history
                    )
                    reply = (chat.send_message(message).text or "").strip()
                    if reply:
                        return reply
                    log.warning("Model %s returned an empty reply", model)
                except Exception as err:
                    delay = _retry_after(err)
                    if delay is not None and attempt + 1 < MAX_ATTEMPTS_PER_MODEL:
                        log.warning("Rate limited on %s; waiting %.0fs", model, delay)
                        time.sleep(delay)
                        continue
                    log.warning("Model %s failed: %s", model, str(err)[:200])
                    break

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
        last_error: Exception | None = None
        for model in self._analytics_models:
            for attempt in range(MAX_ATTEMPTS_PER_MODEL):
                try:
                    _throttle.wait(model)
                    response = self._client.models.generate_content(
                        model=model,
                        contents=f"{instruction}\n\n<transcript>\n{transcript}\n</transcript>",
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=schema,
                            thinking_config=thinking_for(model),
                            temperature=0.0,
                        ),
                    )
                    if response.parsed is not None:
                        return response.parsed
                except Exception as err:
                    last_error = err
                    delay = _retry_after(err)
                    if delay is not None and attempt + 1 < MAX_ATTEMPTS_PER_MODEL:
                        log.warning("Rate limited on %s; waiting %.0fs", model, delay)
                        time.sleep(delay)
                        continue
                    log.warning("Extraction failed on %s: %s", model, str(err)[:200])
                    break

        log.error("Extraction failed on every model: %s", last_error)
        raise ExtractionError(str(last_error) if last_error else "no model returned a record")
