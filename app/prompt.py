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
