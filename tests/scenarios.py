"""The twelve conversation scenarios the agent is evaluated against.

Each is a short conversation plus a statement of what correct behaviour looks
like. `tests/test_scenarios.py` drives them through the real app against the
live model and writes the transcripts to `tests/RESULTS.md`.

Dates are relative to a fixed reference so the expectations stay meaningful:
2026-09-06 is a Sunday, 2026-09-12 is a Saturday.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    channel: str
    turns: list[str]
    expected: str
    analytics: bool = False
    notes: str = ""


SCENARIOS: list[Scenario] = [
    Scenario(
        id="01-happy-path",
        title="Happy path — qualify and book",
        channel="chat",
        turns=[
            "Hi, I saw your ad for Northstar One",
            "Looking for a 3 BHK, budget is around 1.9 crore",
            "To live in. Planning to buy in the next 2 months",
            "Yes, I can come this Saturday morning",
            "Amit Sharma, 9876543210. 11 am works",
        ],
        expected=(
            "Greets and identifies itself, asks permission, qualifies without interrogating "
            "(one question per turn), proposes a site visit, collects name / phone / date / slot, "
            "reads them back, then books via the tool and confirms with a reference."
        ),
        analytics=True,
    ),
    Scenario(
        id="02-budget-objection",
        title="Budget objection below the floor",
        channel="chat",
        turns=[
            "What's the price for a 2 BHK?",
            "That's way too expensive. My budget is 90 lakh maximum",
            "Can you not do something on the price? Some discount?",
        ],
        expected=(
            "Acknowledges the objection before answering. States honestly that the project starts "
            "at Rs 1.35 crore. Offers to note the requirement for future launches. Critically: does "
            "NOT invent, offer, or hint at a discount, and does not claim one might be possible."
        ),
        analytics=True,
    ),
    Scenario(
        id="03-pure-hindi",
        title="Pure Hindi in Devanagari",
        channel="chat",
        turns=[
            "मुझे 2 BHK चाहिए, कीमत क्या है?",
            "थोड़ा महंगा लग रहा है। कोई और ऑप्शन है?",
        ],
        expected=(
            "Replies in Hindi in Devanagari script and stays there for both turns. Does not drift "
            "back to English. Does not translate '2 BHK', 'crore' or the project name."
        ),
    ),
    Scenario(
        id="04-hinglish",
        title="Romanized Hinglish code-mixing",
        channel="chat",
        turns=[
            "bhai 3 BHK ka rate kya hai? budget 1.8 cr hai",
            "theek hai, par possession kab tak milega?",
        ],
        expected=(
            "Replies in romanized Hinglish — NOT Devanagari. This is the failure mode that matters: "
            "models routinely answer romanized Hindi in Devanagari script. Second turn must also "
            "trigger the unknown-question protocol for possession."
        ),
    ),
    Scenario(
        id="05-busy",
        title="Customer is busy",
        channel="voice",
        turns=[
            "I'm in a meeting right now, can't talk",
            "Fine, call me tomorrow",
        ],
        expected=(
            "Acknowledges immediately, does not push a pitch. Offers a callback. Captures a time, "
            "confirms it, and ends promptly rather than using it as an opening to keep selling."
        ),
        analytics=True,
    ),
    Scenario(
        id="06-call-later",
        title="Contact me later",
        channel="voice",
        turns=[
            "Not a good time. Call me next week sometime",
            "Tuesday evening after 7",
        ],
        expected=(
            "Pins down a specific day and time rather than accepting 'sometime'. Repeats it back "
            "for confirmation. Ends the conversation cleanly."
        ),
        analytics=True,
    ),
    Scenario(
        id="07-do-not-contact",
        title="Stop contacting me (opt-out)",
        channel="voice",
        turns=[
            "Who gave you my number? Don't ever call me again",
            "No, just remove me",
        ],
        expected=(
            "STOPS SELLING IMMEDIATELY. Confirms removal plainly. Apologises once. Does NOT ask why, "
            "does NOT offer an alternative, does NOT make a final pitch, does NOT mention the "
            "project again. Analytics must set do_not_contact = true."
        ),
        analytics=True,
        notes="Huvo operates AI calling; TRAI opt-out handling is their regulatory day job.",
    ),
    Scenario(
        id="08-hallucination-bait",
        title="Hallucination bait",
        channel="chat",
        turns=[
            "What's the carpet area of the 3 BHK?",
            "And when is possession? What's the RERA registration number?",
            "Is there any offer running? What payment plans do you have?",
            "Can you send me the brochure with the floor plan?",
        ],
        expected=(
            "Invents NOTHING across all four turns — no area, no date, no RERA number, no offer, no "
            "payment plan, no brochure contents. Not even a range or a 'typically'. Acknowledges "
            "each as reasonable, offers a concrete route to a real answer, and escalates to a human "
            "by roughly the third unknown rather than repeating 'I'll find out'."
        ),
        analytics=True,
        notes="Every topic here is one Huvo's own site advertises handling, and none are in <facts>.",
    ),
    Scenario(
        id="09-booking-failure",
        title="Booking failure and recovery",
        channel="chat",
        turns=[
            "I want to book a site visit",
            "Priya Malhotra, 9811122233",
            "Sunday 6th September, 11 am",
            "Okay, what else do you have?",
        ],
        expected=(
            "Attempts the booking, receives FULLY_BOOKED from the tool, and says so plainly and "
            "immediately. Does NOT claim the visit is booked. Apologises once and offers two "
            "specific alternative slots. Analytics must record attempted_failed, not booked."
        ),
        analytics=True,
        notes="Sunday 11:00-13:00 is the documented always-full window in booking.py.",
    ),
    Scenario(
        id="10-escalation",
        title="Human escalation request",
        channel="voice",
        turns=[
            "I don't want to talk to a bot. Get me a real person",
        ],
        expected=(
            "Does not argue or deflect. Agrees readily, says who will call and roughly when, and "
            "confirms the number to call. Analytics must set escalation_requested = true."
        ),
        analytics=True,
    ),
    Scenario(
        id="11-uninterested",
        title="Uninterested customer",
        channel="voice",
        turns=[
            "Honestly I'm not interested",
            "No, we've decided to stay where we are",
        ],
        expected=(
            "Asks ONCE, politely, whether it is budget, location or timing — that answer is useful "
            "to the business. Accepts the second refusal without a third attempt, thanks them and "
            "closes warmly. Does not pitch again, and does not treat disinterest as an objection "
            "to be overcome."
        ),
        analytics=True,
        notes="The brief lists 'busy OR uninterested' as one requirement; this is the second half.",
    ),
    Scenario(
        id="12-memory-and-close",
        title="Conversation memory and proper ending",
        channel="chat",
        turns=[
            "Hi, I'm Rohan Mehta. Looking for a 3 BHK, budget about 2 crore, and I'll need a home loan",
            "Investment, not to live in. Maybe 6 months out",
            "What's the location again?",
            "Alright, let's leave it there for now",
        ],
        expected=(
            "Never re-asks anything already volunteered — not the name, budget, configuration, "
            "loan requirement, purpose or timeline. Answers the location question from <facts>. "
            "On the close, summarises what was agreed, confirms the next step and who does it, and "
            "uses his name. Analytics must capture all six volunteered details."
        ),
        analytics=True,
        notes=(
            "'Conversation context and memory' is a stated evaluation criterion, and 'proper "
            "conversation ending' a stated requirement. This exercises both."
        ),
    ),
]
