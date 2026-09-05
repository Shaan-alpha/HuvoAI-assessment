import re
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime

OPEN_HOUR = 10
CLOSE_HOUR = 18

# Deterministic failure window. Documented in the README so a reviewer can
# reproduce the failure path on demand instead of hoping to trip it.
FULL_WEEKDAY = 6  # Sunday
FULL_FROM_HOUR = 11
FULL_TO_HOUR = 13

_PHONE = re.compile(r"^[6-9]\d{9}$")
_SLOT = re.compile(r"^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$")


@dataclass(frozen=True)
class BookingResult:
    ok: bool
    message: str
    reference: str | None = None


def _reference(phone: str, on: Date) -> str:
    return f"NS-{on:%Y%m%d}-{phone[-4:]}"


def attempt(name: str, phone: str, date: str, time_slot: str) -> BookingResult:
    """Try to reserve a site-visit slot.

    Deliberately fallible: Sunday 11:00-13:00 is always full, so the failure
    recovery conversation exercises a real code path rather than the model
    acting out a failure it was told to imagine.
    """
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

    slot = _SLOT.match(time_slot.strip())
    if not slot:
        return BookingResult(False, "I couldn't read that time slot. I need it as HH:MM-HH:MM.")

    start_hour, end_hour = int(slot.group(1)), int(slot.group(3))
    if start_hour < OPEN_HOUR or end_hour > CLOSE_HOUR:
        return BookingResult(
            False,
            "Site visits run between 10:00 and 18:00 only. "
            "Please offer the customer a slot inside that window.",
        )

    if on.weekday() == FULL_WEEKDAY and FULL_FROM_HOUR <= start_hour < FULL_TO_HOUR:
        return BookingResult(
            False,
            "That slot is fully booked — Sunday late mornings fill up fastest. "
            "Tell the customer plainly and offer two alternative slots.",
        )

    return BookingResult(
        True,
        f"Site visit confirmed for {name.strip()} on {on:%A %d %B %Y} at {time_slot.strip()}.",
        _reference(phone.strip(), on),
    )
