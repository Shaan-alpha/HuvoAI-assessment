from app.llm import make_booking_tool
from app.session import Session


def test_booking_tool_records_success_on_session():
    s = Session(id="t1")
    tool = make_booking_tool(s)
    out = tool("Amit Sharma", "9876543210", "2026-09-12", "11:00-12:00")
    assert "confirmed" in out.lower()
    assert len(s.bookings) == 1
    assert s.bookings[0].startswith("NS-")


def test_booking_tool_records_failure_without_reference():
    s = Session(id="t2")
    tool = make_booking_tool(s)
    out = tool("Amit Sharma", "9876543210", "2026-09-13", "11:00-12:00")
    assert "fully booked" in out.lower()
    assert s.bookings == ["FAILED: 2026-09-13 11:00-12:00"]


def test_booking_tool_has_a_docstring_for_schema_derivation():
    """The SDK derives the tool schema from signature + docstring.

    An undocumented tool silently loses its parameter descriptions, so the
    model stops knowing what format `date` wants. Guard it.
    """
    tool = make_booking_tool(Session(id="t3"))
    assert tool.__doc__
    for arg in ("name", "phone", "date", "time_slot"):
        assert arg in tool.__doc__


def test_history_is_converted_to_sdk_contents():
    from app.llm import to_contents
    from app.session import Turn

    s = Session(id="t4", turns=[
        Turn(role="user", content="hi"),
        Turn(role="model", content="hello"),
    ])
    contents = to_contents(s)
    assert [c.role for c in contents] == ["user", "model"]
    assert contents[0].parts[0].text == "hi"


def test_thinking_param_differs_by_model_generation():
    """thinking_level is Gemini 3.x only; 2.x rejects it with a 400.

    Getting this wrong silently breaks the fallback path — the primary hits a
    429, the fallback 400s, and the user sees a connection error.
    """
    from app.llm import thinking_for

    three = thinking_for("gemini-3.8-flash")
    assert three.thinking_level == "LOW"
    assert three.thinking_budget is None

    two = thinking_for("gemini-2.5-flash")
    assert two.thinking_budget == 0
    assert two.thinking_level is None


def test_retry_delay_is_read_from_a_429():
    from app.llm import _retry_after

    err = Exception("429 RESOURCE_EXHAUSTED {'retryDelay': '54s'}")
    assert _retry_after(err) == 54.0


def test_non_rate_limit_errors_are_not_retried():
    from app.llm import _retry_after

    assert _retry_after(Exception("400 INVALID_ARGUMENT")) is None


def test_throttle_is_tracked_per_model():
    """A fallback model must not inherit the primary's cooldown."""
    from app.llm import _Throttle

    t = _Throttle(min_interval=99.0)
    t.wait("model-a")
    t.wait("model-b")  # different bucket, must not block
