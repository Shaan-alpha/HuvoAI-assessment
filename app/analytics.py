from typing import Literal

from pydantic import BaseModel, Field

from app.session import Session

InterestLevel = Literal["hot", "warm", "cold", "unknown"]
SiteVisitStatus = Literal["booked", "attempted_failed", "declined", "not_discussed"]


class LeadAnalytics(BaseModel):
    """Structured lead record extracted from a finished conversation.

    Every field is optional or defaulted. A conversation that ended after two
    turns must still produce a valid record — absence is data, not an error.

    The field list mirrors what a real-estate pre-sales CRM captures: name,
    contact, source, budget, location, configuration, timeline, intent,
    site-visit interest, callback time, objections, score, summary and next
    action. do_not_contact and unknown_questions_asked are additions.
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

Set do_not_contact to true if the customer asked to stop being contacted, in any language.
Set escalation_requested to true if they asked for a human or a callback from the sales team.
List every question the agent could not answer in unknown_questions_asked.

Score qualification_score from 0 to 100 by adding these, and nothing else:
  budget stated and at or above 1.35 crore .... 25
  configuration stated ........................ 15
  timeline within six months .................. 20
  site visit booked ........................... 25
  purchase purpose stated ..................... 10
  contact number shared ....................... 5

Then set interest_level: hot at 70 or above, warm from 40 to 69, cold below 40. \
If the customer asked not to be contacted, interest_level is cold whatever the score.

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
        return "The booking tool was never called during this conversation."
    lines = []
    for entry in session.bookings:
        if entry.startswith("FAILED:"):
            lines.append(f"- booking ATTEMPTED AND FAILED for {entry.removeprefix('FAILED:').strip()}")
        else:
            lines.append(f"- booking SUCCEEDED, reference {entry}")
    return "The booking tool recorded these outcomes:\n" + "\n".join(lines)


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
    return client.extract(session.transcript(), LeadAnalytics, instruction)
