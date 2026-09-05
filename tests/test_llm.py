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
