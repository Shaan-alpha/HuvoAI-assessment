from typing import Literal

from pydantic import BaseModel, Field

from app.session import Session

InterestLevel = Literal["hot", "warm", "cold", "unknown"]
SiteVisitStatus = Literal[
    "booked", "attempted_failed", "declined", "discussed_not_booked", "not_discussed"
]

# The project's entry price. A budget below this cannot buy here, so it scores
# nothing however confidently it was stated.
BUDGET_FLOOR_CRORE = 1.35

POINTS = {
    "budget_at_or_above_floor": 25,
    "configuration_stated": 15,
    "timeline_within_six_months": 20,
    "site_visit_booked": 25,
    "purpose_stated": 10,
    "contact_number_shared": 5,
}

HOT_AT = 70
WARM_AT = 40


class LeadAnalytics(BaseModel):
    """Structured lead record extracted from a finished conversation.

    Every field is optional or defaulted. A conversation that ended after two
    turns must still produce a valid record — absence is data, not an error.

    The field list mirrors what a real-estate pre-sales CRM captures: name,
    contact, source, budget, location, configuration, timeline, intent,
    site-visit interest, callback time, objections, score, summary and next
    action. do_not_contact and unknown_questions_asked are additions.

    qualification_score and interest_level are NOT filled by the model. It
    judges the facts; the arithmetic happens in `score`, below.
    """

    name: str | None = None
    phone: str | None = None
    source: str | None = None
    language_preference: str | None = None

    budget_min: float | None = Field(default=None, description="In INR crore")
    budget_max: float | None = Field(default=None, description="In INR crore")
    budget_was_stated: bool = False

    configuration_interest: str | None = None
    purpose: str | None = None
    timeline: str | None = None
    timeline_within_six_months: bool = False
    possession_preference: str | None = None
    loan_required: bool | None = None
    preferred_location: str | None = None

    interest_level: InterestLevel = "unknown"
    qualification_score: int = 0

    site_visit_status: SiteVisitStatus = "not_discussed"
    booking_datetime: str | None = None

    follow_up_required: bool = False
    follow_up_reason: str | None = None
    callback_time: str | None = None

    objections_raised: list[str] = Field(default_factory=list)
    unknown_questions_asked: list[str] = Field(default_factory=list)

    do_not_contact: bool = False
    escalation_requested: bool = False

    summary: str | None = None
    next_action: str | None = None


EXTRACTION_INSTRUCTION = """\
You are a CRM analyst. Read the transcript of a real-estate sales conversation and record \
what actually happened.

Record only what the customer stated or clearly implied. If something was not discussed, \
leave it empty. Never infer a budget, a timeline or a configuration that was not mentioned. \
An invented value here becomes a wrong number in a CRM that a salesperson will act on. \
Set budget_was_stated to true only if the customer named a budget themselves.

Budgets are in INR crore, so ninety lakh is 0.9 and one point four crore is 1.4.

Set timeline_within_six_months to true only if the customer gave a purchase timeline and it \
falls inside the next six months. Two months from now is true, maybe next year is false, and \
saying nothing about timing is false.

Set do_not_contact to true ONLY if the customer explicitly asked to stop being contacted, to \
be removed, or never to be called again. Losing interest is not an opt-out: not interested, \
decided to stay where we are, and not buying right now are all cold leads who may be \
contacted again. Setting this flag wrongly suppresses a real lead permanently.

Set escalation_requested to true only if the CUSTOMER asked for a human or for the sales team \
to call. The agent offering a callback unprompted is not a request.

List every question the agent could not answer in unknown_questions_asked.

Do not fill in qualification_score or interest_level. They are computed from the fields above \
by the system, so anything you put there is discarded.

next_action is the single concrete thing a salesperson should do next, in under ten words.\
"""


def booking_ground_truth(session: Session) -> str:
    """What the booking tool actually did, as opposed to what was said about it.

    The tool records every attempt, so the outcome is known for certain. Asking
    the model to infer it from the transcript instead would put a guess in the
    one analytics field a salesperson acts on — and a lead wrongly marked
    'booked' is a missed appointment nobody chases.
    """
    if not session.bookings:
        # Stated as a prohibition, not an absence. Told only that the tool was
        # "never called", the model still reported a booked site visit on the
        # happy-path scenario, because the agent had talked as though one were
        # imminent.
        return (
            "The booking tool was NEVER CALLED during this conversation. No site visit "
            "exists. site_visit_status must not be booked and booking_datetime must be "
            "left empty, no matter how the conversation reads."
        )
    lines = []
    for record in session.bookings:
        if record.ok:
            lines.append(f"- booking SUCCEEDED for {record.when()}, reference {record.reference}")
        else:
            lines.append(f"- booking ATTEMPTED AND FAILED for {record.when()}")
    return "The booking tool recorded these outcomes:\n" + "\n".join(lines)


def score(record: LeadAnalytics) -> int:
    """Apply the rubric in code.

    Asked to add the rubric up itself, the model got it wrong on three of the
    four scored scenarios — and on one the error crossed the hot/warm boundary,
    changing how a salesperson would prioritise the lead. The model is good at
    judging whether a timeline falls inside six months and bad at arithmetic,
    so it does the judging and this does the adding. That is what makes the
    score reproducible and auditable rather than merely claimed to be.
    """
    ceiling = record.budget_max if record.budget_max is not None else record.budget_min
    total = 0
    if record.budget_was_stated and ceiling is not None and ceiling >= BUDGET_FLOOR_CRORE:
        total += POINTS["budget_at_or_above_floor"]
    if record.configuration_interest:
        total += POINTS["configuration_stated"]
    if record.timeline_within_six_months:
        total += POINTS["timeline_within_six_months"]
    if record.site_visit_status == "booked":
        total += POINTS["site_visit_booked"]
    if record.purpose:
        total += POINTS["purpose_stated"]
    if record.phone:
        total += POINTS["contact_number_shared"]
    return total


def interest_for(points: int, do_not_contact: bool) -> InterestLevel:
    """A customer who opted out is cold whatever the rubric says."""
    if do_not_contact:
        return "cold"
    if points >= HOT_AT:
        return "hot"
    if points >= WARM_AT:
        return "warm"
    return "cold"


def apply_booking_truth(record: LeadAnalytics, session: Session) -> LeadAnalytics:
    """Overwrite the site-visit fields with what the tool actually did."""
    succeeded = [b for b in session.bookings if b.ok]
    if succeeded:
        record.site_visit_status = "booked"
        record.booking_datetime = succeeded[-1].when()
    elif session.bookings:
        record.site_visit_status = "attempted_failed"
        record.booking_datetime = session.bookings[-1].when()
    else:
        record.booking_datetime = None
        if record.site_visit_status == "booked":
            # A visit was talked about and never booked. Saying exactly that is
            # the point; downgrading to 'declined' would be its own invention.
            record.site_visit_status = "discussed_not_booked"
    return record


def finalise(record: LeadAnalytics, session: Session) -> LeadAnalytics:
    """Replace every model-guessed derived field with a computed one."""
    record = apply_booking_truth(record, session)
    record.qualification_score = score(record)
    record.interest_level = interest_for(record.qualification_score, record.do_not_contact)
    return record


def extract_analytics(client, session: Session) -> LeadAnalytics:
    """Run one extraction pass over the finished transcript."""
    if not session.turns:
        return LeadAnalytics()
    instruction = (
        f"{EXTRACTION_INSTRUCTION}\n\n"
        "SYSTEM RECORD — this is authoritative and overrides anything said in the "
        "transcript. If it conflicts with what the agent claimed, trust this.\n"
        f"{booking_ground_truth(session)}"
    )
    return finalise(client.extract(session.transcript(), LeadAnalytics, instruction), session)
