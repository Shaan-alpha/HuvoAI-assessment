from datetime import date as Date
from functools import lru_cache
from pathlib import Path
from typing import Literal

Channel = Literal["chat", "voice"]

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
SEPARATOR = "\n\n---\n\n"

_VALID: set[str] = {"chat", "voice"}


@lru_cache
def _read(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


@lru_cache
def compose(channel: Channel) -> str:
    """Return the core prompt joined to the output-rendering delta for `channel`.

    Behaviour lives entirely in the core. A delta only changes how the reply is
    rendered — never what the agent does. That split is what lets one prompt
    serve both chat and voice, and adding a third channel (WhatsApp, SMS) costs
    one file rather than a second prompt to keep in sync.
    """
    if channel not in _VALID:
        raise ValueError(f"Unknown channel {channel!r}; expected one of {sorted(_VALID)}")
    return f"{_read('system_prompt.md')}{SEPARATOR}{_read(f'channel_{channel}.md')}"


def runtime_context(today: Date) -> str:
    """Today's date, for resolving relative dates when booking.

    The model has no clock. Without this it cannot turn "this Saturday" into
    the YYYY-MM-DD the booking tool requires, and will either guess a date or
    ask the customer to supply one in a format nobody speaks.
    """
    from datetime import timedelta

    # Give the model a lookup table rather than asking it to do calendar
    # arithmetic. Asked to compute, gemini-3.8-flash produced "this Saturday,
    # September 7th" on a day when the 7th was a Monday. Models are unreliable
    # at date maths and completely reliable at reading a list.
    days = [today + timedelta(days=i) for i in range(8)]
    table = "\n".join(
        f"  {d:%A %d %B %Y} = {d:%Y-%m-%d}" + ("   (today)" if i == 0 else "")
        for i, d in enumerate(days)
    )
    return (
        "# CURRENT CONTEXT\n\n"
        f"Today is {today:%A, %d %B %Y}.\n\n"
        "The next few days, for booking:\n"
        f"{table}\n\n"
        "Read the exact date off this table when the customer says \"tomorrow\", "
        "\"this Saturday\" or similar. Do not calculate it yourself, and do not "
        "state a weekday and a date that disagree with the table. Never ask the "
        "customer to say a date in YYYY-MM-DD — convert it yourself before calling "
        "book_site_visit. Never book a date in the past."
    )


def compose_for_turn(channel: Channel, today: Date) -> str:
    """The full system instruction for one live turn."""
    return f"{compose(channel)}{SEPARATOR}{runtime_context(today)}"
