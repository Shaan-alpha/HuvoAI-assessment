from app.analytics import (
    EXTRACTION_INSTRUCTION,
    LeadAnalytics,
    extract_analytics,
    interest_for,
    score,
)
from app.session import BookingRecord, Session, Turn

BOOKED = BookingRecord(ok=True, date="2026-09-12", time_slot="11:00-12:00", reference="NS-20260912-3210")
FAILED = BookingRecord(ok=False, date="2026-09-13", time_slot="11:00-12:00")


class FakeClient:
    def __init__(self, payload=None):
        self.payload = payload or {}
        self.seen_transcript = None
        self.seen_instruction = None

    def extract(self, transcript, schema, instruction):
        self.seen_transcript = transcript
        self.seen_instruction = instruction
        return schema(**self.payload)


def test_a_sparse_conversation_still_produces_a_valid_record():
    """Absence is data. A two-turn conversation must not fail extraction."""
    a = LeadAnalytics()
    assert a.budget_min is None
    assert a.budget_was_stated is False
    assert a.do_not_contact is False
    assert a.objections_raised == []
    assert a.site_visit_status == "not_discussed"
    assert a.interest_level == "unknown"


def test_extract_returns_populated_model():
    session = Session(id="s1", turns=[Turn(role="user", content="3 BHK chahiye")])
    client = FakeClient({"configuration_interest": "3 BHK"})
    result = extract_analytics(client, session)
    assert result.configuration_interest == "3 BHK"


def test_extract_is_given_the_rendered_transcript():
    session = Session(id="s2", turns=[
        Turn(role="user", content="hello"),
        Turn(role="model", content="Hello sir"),
    ])
    client = FakeClient()
    extract_analytics(client, session)
    assert "Customer: hello" in client.seen_transcript
    assert "Priya: Hello sir" in client.seen_transcript


def test_instruction_carries_the_rubric_inputs():
    assert "timeline_within_six_months" in EXTRACTION_INSTRUCTION
    assert "do_not_contact" in EXTRACTION_INSTRUCTION


def test_instruction_tells_the_model_not_to_score():
    """The rubric is arithmetic, and the model is bad at arithmetic."""
    assert "Do not fill in qualification_score" in EXTRACTION_INSTRUCTION


def test_instruction_does_not_restate_the_json_schema():
    """The SDK docs warn that duplicating the schema degrades output quality."""
    assert "{" not in EXTRACTION_INSTRUCTION
    assert "}" not in EXTRACTION_INSTRUCTION


def test_budget_stated_flag_is_independent_of_budget_values():
    """A null budget must be distinguishable from an inferred one."""
    inferred = LeadAnalytics(budget_min=1.35, budget_was_stated=False)
    stated = LeadAnalytics(budget_min=1.35, budget_was_stated=True)
    assert inferred.budget_min == stated.budget_min
    assert inferred.budget_was_stated != stated.budget_was_stated


# --- the rubric, applied in code -------------------------------------------


def test_score_is_the_sum_of_the_written_rubric():
    """Every criterion at once: 25 + 15 + 20 + 25 + 10 + 5."""
    full = LeadAnalytics(
        budget_min=1.9, budget_max=1.9, budget_was_stated=True,
        configuration_interest="3 BHK",
        timeline_within_six_months=True,
        site_visit_status="booked",
        purpose="To live in",
        phone="9876543210",
    )
    assert score(full) == 100


def test_score_of_an_empty_record_is_zero():
    assert score(LeadAnalytics()) == 0


def test_budget_below_the_floor_scores_nothing():
    """Rs 90 lakh cannot buy here, however plainly it was stated."""
    below = LeadAnalytics(budget_max=0.9, budget_was_stated=True)
    assert score(below) == 0


def test_an_inferred_budget_scores_nothing():
    """Only a budget the customer actually gave earns the points."""
    guessed = LeadAnalytics(budget_min=1.9, budget_max=1.9, budget_was_stated=False)
    assert score(guessed) == 0


def test_a_range_qualifies_on_its_upper_bound():
    spanning = LeadAnalytics(budget_min=1.2, budget_max=1.6, budget_was_stated=True)
    assert score(spanning) == 25


def test_interest_level_thresholds():
    assert interest_for(70, False) == "hot"
    assert interest_for(69, False) == "warm"
    assert interest_for(40, False) == "warm"
    assert interest_for(39, False) == "cold"


def test_an_opted_out_lead_is_cold_whatever_the_score():
    assert interest_for(100, True) == "cold"


def test_the_scored_record_is_reproducible_end_to_end():
    """Regression: the model returned 65 for this lead; the rubric says 70.

    65 and 70 fall on opposite sides of the hot threshold, so the arithmetic
    slip changed how a salesperson would have prioritised the lead.
    """
    session = Session(id="s3", turns=[Turn(role="user", content="hi")])
    client = FakeClient({
        "budget_min": 2.0, "budget_max": 2.0, "budget_was_stated": True,
        "configuration_interest": "3 BHK",
        "timeline_within_six_months": True,
        "purpose": "Investment",
        "qualification_score": 65,
        "interest_level": "warm",
    })
    result = extract_analytics(client, session)
    assert result.qualification_score == 70
    assert result.interest_level == "hot"


# --- booking ground truth ---------------------------------------------------


def test_ground_truth_reports_no_booking_attempt():
    from app.analytics import booking_ground_truth

    assert "NEVER CALLED" in booking_ground_truth(Session(id="g0"))


def test_ground_truth_distinguishes_success_from_failure():
    from app.analytics import booking_ground_truth

    ok = Session(id="g1", bookings=[BOOKED])
    assert "SUCCEEDED" in booking_ground_truth(ok)
    assert "NS-20260912-3210" in booking_ground_truth(ok)

    bad = Session(id="g2", bookings=[FAILED])
    truth = booking_ground_truth(bad)
    assert "FAILED" in truth
    assert "2026-09-13 11:00-12:00" in truth
    assert "SUCCEEDED" not in truth


def test_extraction_prompt_carries_booking_ground_truth():
    """The tool knows the outcome; the model must not have to guess it."""
    session = Session(
        id="g3",
        turns=[Turn(role="model", content="Your visit is confirmed!")],
        bookings=[FAILED],
    )
    client = FakeClient()
    extract_analytics(client, session)
    assert "authoritative" in client.seen_instruction
    assert "FAILED" in client.seen_instruction


def test_a_claimed_booking_is_overruled_when_the_tool_never_ran():
    """The regression this whole path exists for.

    On the happy-path scenario the agent talked as though a visit were settled,
    never called the tool, and the extraction recorded `booked` with a date —
    plus the 25 rubric points that go with it. A lead wrongly marked booked is
    a missed appointment nobody chases.
    """
    session = Session(id="g4", turns=[Turn(role="model", content="Booked for Saturday!")])
    client = FakeClient({
        "site_visit_status": "booked",
        "booking_datetime": "Saturday the 5th at 11 am",
    })
    result = extract_analytics(client, session)
    assert result.site_visit_status == "discussed_not_booked"
    assert result.booking_datetime is None
    assert result.qualification_score == 0


def test_a_failed_booking_is_never_reported_as_booked():
    session = Session(
        id="g5",
        turns=[Turn(role="model", content="All confirmed!")],
        bookings=[FAILED],
    )
    result = extract_analytics(FakeClient({"site_visit_status": "booked"}), session)
    assert result.site_visit_status == "attempted_failed"
    assert result.booking_datetime == "2026-09-13 11:00-12:00"


def test_a_real_booking_sets_the_datetime_from_the_tool_record():
    session = Session(
        id="g6",
        turns=[Turn(role="user", content="book it")],
        bookings=[FAILED, BOOKED],
    )
    result = extract_analytics(FakeClient({"phone": "9876543210"}), session)
    assert result.site_visit_status == "booked"
    assert result.booking_datetime == "2026-09-12 11:00-12:00"
    # 25 for the booking + 5 for the number
    assert result.qualification_score == 30


def test_opting_out_is_narrower_than_losing_interest():
    """A cold lead is not an opt-out, and must not be suppressed like one."""
    assert "not an opt-out" in EXTRACTION_INSTRUCTION
    assert "suppresses a real lead permanently" in EXTRACTION_INSTRUCTION
