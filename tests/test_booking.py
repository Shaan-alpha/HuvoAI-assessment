from app.booking import attempt

# 2026-09-12 is a Saturday. 2026-09-13 is a Sunday.


def test_valid_weekday_slot_succeeds():
    r = attempt("Amit Sharma", "9876543210", "2026-09-12", "11:00-12:00")
    assert r.ok
    assert r.reference and r.reference.startswith("NS-")


def test_sunday_midday_slot_is_always_full():
    """The documented failure window, so the recovery path is reproducible."""
    r = attempt("Amit Sharma", "9876543210", "2026-09-13", "11:00-12:00")
    assert not r.ok
    assert "fully booked" in r.message.lower()
    assert r.reference is None


def test_sunday_outside_the_blocked_window_succeeds():
    r = attempt("Amit Sharma", "9876543210", "2026-09-13", "15:00-16:00")
    assert r.ok


def test_slot_outside_working_hours_is_rejected():
    r = attempt("Amit Sharma", "9876543210", "2026-09-12", "21:00-22:00")
    assert not r.ok
    assert "10:00" in r.message


def test_malformed_phone_is_rejected():
    r = attempt("Amit Sharma", "12345", "2026-09-12", "11:00-12:00")
    assert not r.ok
    assert "mobile number" in r.message.lower()


def test_malformed_date_is_rejected():
    r = attempt("Amit Sharma", "9876543210", "next tuesday", "11:00-12:00")
    assert not r.ok


def test_blank_name_is_rejected():
    r = attempt("   ", "9876543210", "2026-09-12", "11:00-12:00")
    assert not r.ok


def test_reference_is_stable_for_same_inputs():
    a = attempt("Amit Sharma", "9876543210", "2026-09-12", "11:00-12:00")
    b = attempt("Amit Sharma", "9876543210", "2026-09-12", "11:00-12:00")
    assert a.reference == b.reference
