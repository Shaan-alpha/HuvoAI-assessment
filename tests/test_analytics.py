from app.analytics import EXTRACTION_INSTRUCTION, LeadAnalytics, extract_analytics
from app.session import Session, Turn


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
    client = FakeClient({"configuration_interest": "3 BHK", "interest_level": "warm"})
    result = extract_analytics(client, session)
    assert result.configuration_interest == "3 BHK"
    assert result.interest_level == "warm"


def test_extract_is_given_the_rendered_transcript():
    session = Session(id="s2", turns=[
        Turn(role="user", content="hello"),
        Turn(role="model", content="Hello sir"),
    ])
    client = FakeClient()
    extract_analytics(client, session)
    assert "Customer: hello" in client.seen_transcript
    assert "Priya: Hello sir" in client.seen_transcript


def test_instruction_carries_the_rubric():
    assert "qualification_score" in EXTRACTION_INSTRUCTION
    assert "do_not_contact" in EXTRACTION_INSTRUCTION


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


def test_ground_truth_reports_no_booking_attempt():
    from app.analytics import booking_ground_truth

    assert "never called" in booking_ground_truth(Session(id="g0"))


def test_ground_truth_distinguishes_success_from_failure():
    from app.analytics import booking_ground_truth

    ok = Session(id="g1", bookings=["NS-20260912-3210"])
    assert "SUCCEEDED" in booking_ground_truth(ok)
    assert "NS-20260912-3210" in booking_ground_truth(ok)

    bad = Session(id="g2", bookings=["FAILED: 2026-09-13 11:00-12:00"])
    truth = booking_ground_truth(bad)
    assert "FAILED" in truth
    assert "2026-09-13 11:00-12:00" in truth
    assert "SUCCEEDED" not in truth


def test_extraction_prompt_carries_booking_ground_truth():
    """The tool knows the outcome; the model must not have to guess it."""
    session = Session(
        id="g3",
        turns=[Turn(role="model", content="Your visit is confirmed!")],
        bookings=["FAILED: 2026-09-13 11:00-12:00"],
    )
    client = FakeClient()
    extract_analytics(client, session)
    assert "authoritative" in client.seen_instruction
    assert "FAILED" in client.seen_instruction
