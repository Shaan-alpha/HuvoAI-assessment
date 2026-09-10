import re
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime

OPEN_HOUR = 10
CLOSE_HOUR = 18
SLOT_MINUTES = 60

# Deterministic failure window. Documented in the README so a reviewer can
# reproduce the failure path on demand instead of hoping to trip it.
FULL_WEEKDAY = 6  # Sunday
FULL_FROM_HOUR = 11
FULL_TO_HOUR = 13

_PHONE = re.compile(r"^[6-9]\d{9}$")
# Hours and minutes are bounded here rather than checked later, so "10:99" is
# rejected as unreadable instead of being silently accepted as a valid slot.
_SLOT = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)-([01]?\d|2[0-3]):([0-5]\d)$")


@dataclass(frozen=True)
class BookingResult:
    ok: bool
    message: str
    reference: str | None = None


def _reference(phone: str, on: Date) -> str:
    return f"NS-{on:%Y%m%d}-{phone[-4:]}"


def _free_sunday_slots() -> str:
    return (
        f"{OPEN_HOUR:02d}:00-{FULL_FROM_HOUR:02d}:00, "
        f"or any one-hour slot from {FULL_TO_HOUR:02d}:00 up to {CLOSE_HOUR:02d}:00"
    )


def attempt(
    name: str,
    phone: str,
    date: str,
    time_slot: str,
    *,
    today: Date | None = None,
) -> BookingResult:
    """Try to reserve a site-visit slot.

    Deliberately fallible: Sunday 11:00-13:00 is always full, so the failure
    recovery conversation exercises a real code path rather than the model
    acting out a failure it was told to imagine.

    Every rule the prompt states about booking is enforced here as well. A rule
    that lives only in the prompt is a suggestion; the tool is what makes it a
    constraint, and the tool is the thing this design claims is real.
    """
    today = today or Date.today()

    if not name.strip():
        return BookingResult(False, "I need a name for the booking.")

    if not _PHONE.match(phone.strip()):
        return BookingResult(
            False,
            "That mobile number doesn't look right — I need 10 digits starting with 6 to 9.",
        )

    try:
        on = datetime.strptime(date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return BookingResult(False, "I couldn't read that date. I need it as YYYY-MM-DD.")

    if on < today:
        return BookingResult(
            False,
            f"{on:%d %B %Y} has already passed. "
            "Ask the customer for a date from today onwards.",
        )

    slot = _SLOT.match(time_slot.strip())
    if not slot:
        return BookingResult(
            False,
            "I couldn't read that time slot. I need it as HH:MM-HH:MM on the 24-hour clock.",
        )

    start_hour, start_min, end_hour, end_min = (int(g) for g in slot.groups())
    start, end = start_hour * 60 + start_min, end_hour * 60 + end_min

    if end - start != SLOT_MINUTES or start_min:
        return BookingResult(
            False,
            "Site visits are one-hour slots starting on the hour, like 11:00-12:00.",
        )

    if start_hour < OPEN_HOUR or end_hour > CLOSE_HOUR:
        return BookingResult(
            False,
            f"Site visits run between {OPEN_HOUR}:00 and {CLOSE_HOUR}:00 only. "
            "Please offer the customer a slot inside that window.",
        )

    if on.weekday() == FULL_WEEKDAY and FULL_FROM_HOUR <= start_hour < FULL_TO_HOUR:
        # Naming the slots that are actually free matters: told only "offer two
        # alternatives", the agent offered 12:00-13:00 — inside this same
        # blocked window — and would have failed a second time.
        return BookingResult(
            False,
            f"That slot is fully booked — Sunday {FULL_FROM_HOUR}:00 to {FULL_TO_HOUR}:00 "
            "fills up fastest. Tell the customer plainly, apologise once, and offer two "
            f"slots that are genuinely free that day: {_free_sunday_slots()}.",
        )

    return BookingResult(
        True,
        f"Site visit confirmed for {name.strip()} on {on:%A %d %B %Y} at {time_slot.strip()}.",
        _reference(phone.strip(), on),
    )
