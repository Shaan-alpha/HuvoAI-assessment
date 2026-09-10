from datetime import date

from app.booking import FULL_FROM_HOUR, FULL_TO_HOUR, attempt

# A fixed "today" keeps these tests meaningful for the life of the repository.
# Without it the past-date rule silently starts rejecting the fixtures the day
# the calendar catches up with them.
TODAY = date(2026, 9, 10)  # a Thursday
SATURDAY = "2026-09-12"
SUNDAY = "2026-09-13"


def book(date_str, slot, name="Amit Sharma", phone="9876543210", today=TODAY):
    return attempt(name, phone, date_str, slot, today=today)


def test_valid_weekday_slot_succeeds():
    r = book(SATURDAY, "11:00-12:00")
    assert r.ok
    assert r.reference and r.reference.startswith("NS-")


def test_booking_today_is_allowed():
    r = book(f"{TODAY:%Y-%m-%d}", "11:00-12:00")
    assert r.ok


def test_sunday_midday_slot_is_always_full():
    """The documented failure window, so the recovery path is reproducible."""
    r = book(SUNDAY, "11:00-12:00")
    assert not r.ok
    assert "fully booked" in r.message.lower()
    assert r.reference is None


def test_the_failure_names_slots_that_are_actually_free():
    """Told only to 'offer two alternatives', the agent offered 12:00-13:00.

    That slot is inside this same blocked window, so the recovery would have
    failed a second time. The message has to carry the constraint, not just
    the refusal.
    """
    message = book(SUNDAY, "11:00-12:00").message
    assert f"{FULL_TO_HOUR:02d}:00" in message
    for blocked_hour in range(FULL_FROM_HOUR, FULL_TO_HOUR):
        assert book(SUNDAY, f"{blocked_hour:02d}:00-{blocked_hour + 1:02d}:00").ok is False


def test_sunday_outside_the_blocked_window_succeeds():
    assert book(SUNDAY, "15:00-16:00").ok
    assert book(SUNDAY, "10:00-11:00").ok
    assert book(SUNDAY, "13:00-14:00").ok


def test_slot_outside_working_hours_is_rejected():
    r = book(SATURDAY, "21:00-22:00")
    assert not r.ok
    assert "10:00" in r.message


def test_the_closing_slot_is_bookable():
    """17:00-18:00 ends exactly on close and must not be off by one."""
    assert book(SATURDAY, "17:00-18:00").ok
    assert not book(SATURDAY, "18:00-19:00").ok


def test_a_date_in_the_past_is_rejected():
    """The prompt says never book in the past; the tool is what enforces it."""
    r = book("2020-01-15", "11:00-12:00")
    assert not r.ok
    assert "passed" in r.message.lower()
    assert r.reference is None


def test_a_slot_longer_than_an_hour_is_rejected():
    r = book(SATURDAY, "10:00-18:00")
    assert not r.ok
    assert "one-hour" in r.message


def test_a_reversed_slot_is_rejected():
    assert not book(SATURDAY, "16:00-11:00").ok


def test_a_zero_length_slot_is_rejected():
    assert not book(SATURDAY, "11:00-11:00").ok


def test_a_slot_off_the_hour_is_rejected():
    assert not book(SATURDAY, "11:30-12:30").ok


def test_impossible_clock_values_are_unreadable():
    r = book(SATURDAY, "10:99-11:99")
    assert not r.ok
    assert "couldn't read" in r.message.lower()
    assert not book(SATURDAY, "25:00-26:00").ok


def test_malformed_phone_is_rejected():
    r = book(SATURDAY, "11:00-12:00", phone="12345")
    assert not r.ok
    assert "mobile number" in r.message.lower()


def test_a_landline_prefix_is_rejected():
    """Indian mobiles start 6-9; the tool is where that rule is real."""
    assert not book(SATURDAY, "11:00-12:00", phone="1234567890").ok


def test_malformed_date_is_rejected():
    assert not book("next tuesday", "11:00-12:00").ok


def test_blank_name_is_rejected():
    assert not book(SATURDAY, "11:00-12:00", name="   ").ok


def test_reference_is_stable_for_same_inputs():
    a = book(SATURDAY, "11:00-12:00")
    b = book(SATURDAY, "11:00-12:00")
    assert a.reference == b.reference
