# Northstar Homes AI Sales Agent — Design

**Date:** 2026-09-05
**Author:** Shaan Satsangi
**Context:** Huvo AI — Forward Deployed Engineer assignment
**Deadline:** 2026-09-06 10:00 IST

---

## 1. Objective

Build an AI sales agent for a fictional real-estate developer, Northstar Homes, that qualifies
inbound leads and books site visits. It must hold a natural conversation in English, Hindi and
Hinglish, and the **same system prompt** must work for both text chat and voice/telephony.

The assignment states its own priority plainly: *"The main focus of this assignment is prompt
engineering and agent behaviour"* and *"Keep the implementation simple."* Six of the seven
evaluation criteria concern the prompt and the conversation; one concerns whether the bot runs.

**This design therefore treats the prompt as the product and the application as its harness.**

## 2. What is being graded

| Criterion | Where this design answers it |
|---|---|
| Prompt quality | §5 — layered prompt, fenced fact sheet, channel deltas |
| Agent behaviour | §5.4 — eleven explicit protocols |
| Handling customer situations | §8 — twelve scenario tests |
| Conversation context and memory | §6.3 — full-history session store |
| Whether the bot works | §6 — FastAPI + single-page UI |
| Code clarity | §6.1 — eight small modules, one job each |
| Understanding of the solution | §5.6 iteration log, §10 non-goals, README |

## 3. Constraints

**Hard**

- Backend **must** be FastAPI (Python). Explicitly stated; other frameworks are rejected outright.
- Zero spend. No credit card, no trial that can auto-bill.
- Public GitHub repo, no committed secrets. Demo video.

**Chosen stack** (all verified free, no card)

- **LLM:** Gemini API free tier via Google AI Studio. Model is an environment variable, defaulting
  to `gemini-3.8-flash` (GA 2026-09-02) with `gemini-2.5-flash` as the documented fallback. Flash
  tier is also the right latency profile for a prompt that must be voice-capable — Huvo advertise
  a 12-second response time, so latency is a value they hold.
- **SDK:** `google-genai` — the current package. `google-generativeai` is superseded; do not use it.
- **Runtime:** Python 3.13, `uv` for dependency management.
- **Frontend:** one static `index.html`. No build step, no framework.

**Rejected**

- Vertex AI — requires billing enabled on the GCP project, i.e. a card.
- Azure OpenAI — student subscriptions need separate model-access approval; too slow to obtain.
- GitHub Models — viable, but Gemini is stronger on Hindi and code-mixed Hinglish.
- Gemini 2.5 **Pro** — reported removed from the free tier in April 2026. Not targetable.
- A consumer Gemini Pro subscription grants **no** API quota; it is unrelated to an AI Studio key.

> Quota note: Google's official rate-limit page now defers to the per-project dashboard in AI
> Studio rather than publishing a table, so the per-model numbers above come from secondary
> reporting and should be confirmed against the account's own dashboard. The design does not
> depend on the exact figures — Flash is the right model here on latency grounds regardless, and
> §7 defines the fallback if quota is hit.

## 4. The central design tension

The assignment supplies exactly **five facts**:

```
Company        Northstar Homes
Project        Northstar One
Location       Sector 79, Gurugram
Configurations 2 BHK, 3 BHK
Price          2 BHK from Rs 1.35 crore  |  3 BHK from Rs 1.75 crore
```

It then requires that the agent *"should not invent prices, discounts, availability, or other
information that has not been provided."*

A real buyer asks about carpet area, possession date, floor plans, RERA registration, amenities,
the builder's track record, payment plans, and discounts. **The agent will be outside its
knowledge on most turns.** So the quality of this agent is decided less by what it knows than by
how gracefully it handles not knowing.

The unknown-question protocol (§5.4) is therefore the most important behaviour in the prompt, not
an edge case. A weak submission stonewalls; a strong one acknowledges the question as reasonable,
declines to guess, commits to getting a real answer, and keeps the conversation moving toward the
site visit.

## 5. Prompt design

### 5.1 Layering

```
  system_prompt.md        (core — channel-agnostic)
+ channel_{voice|chat}.md (delta — output shaping only)
= system instruction sent to the model
```

The delta files contain **no behavioural rules** — only output formatting. This is what makes the
claim "one prompt works for both channels" true rather than asserted: behaviour is defined once,
and only rendering changes.

### 5.2 Core sections

1. **Identity** — Priya, pre-sales consultant at Northstar Homes. A named human persona; "AI
   Assistant" is unnatural on a phone call.
2. **Fact sheet** — the five facts above, fenced, declared the *only* source of truth.
3. **Language policy** — §5.3.
4. **Conversation flow** — greet → seek permission to continue → discover → qualify → propose
   site visit → confirm → close.
5. **Qualification slots** — budget, configuration, timeline, purpose (end-use vs investment),
   **possession preference (ready-to-move vs under-construction)**, home-loan requirement,
   preferred location. Gathered conversationally, never as an interrogation; at most one question
   per turn. This list mirrors the qualification questions Huvo's own product advertises asking.
6. **Objection playbook** — eight common objections with a stance for each, not a script.
7. **Protocols** — §5.4.
8. **Closing** — how to end well in each of: booked, follow-up, declined, opted-out.

### 5.3 Language policy

Mirror the customer's language **and script**. Three distinct cases, commonly collapsed into two:

| Customer writes | Agent replies |
|---|---|
| English | English |
| Hindi in Devanagari | Hindi in Devanagari |
| Romanized Hindi / Hinglish | Romanized Hinglish |

The third case is where models fail — they answer romanized Hindi in Devanagari, which reads
wrong to the customer and, on a voice channel, changes what the TTS engine pronounces.

Never translate: project names, "2 BHK"/"3 BHK", "crore"/"lakh", "carpet area", "site visit".
These are English-as-spoken-in-India and translating them sounds absurd.

### 5.4 Protocols

Eleven named behaviours, each with a trigger and a required response shape:

| Protocol | Required behaviour |
|---|---|
| Busy customer | Acknowledge, offer to be brief or to call back. Do not push. |
| Contact later | Capture a specific time, confirm it, end promptly. |
| **Stop contacting** | Confirm removal, no further selling, no rebuttal. Sets `do_not_contact`. |
| Unknown question | Acknowledge, decline to guess, offer human follow-up, log it. §4. |
| Objection | Acknowledge before answering. Never dismiss. |
| Site-visit booking | Collect name, phone, date, slot. Confirm before calling the tool. |
| **Booking failure** | State the failure plainly, apologise once, offer two alternatives. |
| Human escalation | On request, on frustration, or on repeated unknowns. |
| Uninterested | One polite check for a reason, then close gracefully. |
| Out of scope | Redirect to the project, or escalate. |
| Conversation end | Summarise what was agreed. Confirm next step. |

The stop-contacting protocol is treated as a first-class requirement, not a nicety: Huvo AI
operates AI calling, so TRAI opt-out handling is their regulatory day job and they will test it.

### 5.5 Channel deltas

| | voice | chat |
|---|---|---|
| Length | ≤ 2 sentences per turn | short paragraphs allowed |
| Markdown | forbidden | light formatting allowed |
| Money | "one crore thirty-five lakh" | "Rs 1.35 crore" |
| Lists | spoken as prose, max 3 items | bullets allowed |
| Phone numbers | digit by digit | as written |
| Garbled input | assume mis-transcription, ask to repeat | treat as typo |

Two deltas ship. The point of the architecture, though, is that a third costs one file: Huvo runs
**WhatsApp, Voice, Email, SMS and CRM** off one agent, and WhatsApp in particular needs its own
rendering rules (message length, no markdown tables, emoji tolerance). The README will say this
explicitly — it is the difference between a prompt that happens to work on two channels and one
designed for a channel-agnostic product.

### 5.6 Iteration log

`prompts/ITERATION_LOG.md` records v1 → v2 → v3, and for each revision the **specific observed
failure** that motivated the change. For a prompt-engineering assignment this is the most direct
possible evidence of method, and costs nothing but honesty during development.

## 6. Application design

### 6.1 Modules

| Module | Responsibility | Depends on |
|---|---|---|
| `main.py` | FastAPI app, three routes, static mount | all |
| `config.py` | pydantic-settings, reads `.env` | — |
| `prompt.py` | load and compose core + channel delta | filesystem |
| `llm.py` | Gemini client: chat turn, structured extraction | config |
| `session.py` | `SessionStore` protocol + `InMemoryStore` | — |
| `booking.py` | availability check, deterministic failure | — |
| `analytics.py` | `LeadAnalytics` model, extraction call | llm |
| `static/index.html` | chat UI, voice toggle | — |

Each is small enough to read in one sitting. No module knows about more than it needs.

### 6.2 Routes

```
POST /api/chat              {session_id?, message, channel} -> {session_id, reply}
POST /api/analytics/{sid}                                   -> LeadAnalytics
POST /api/reset/{sid}                                       -> {ok}
GET  /                                                      -> static/index.html
```

### 6.3 Memory

Full turn history per session, in an in-process dict behind a `SessionStore` Protocol.

A sales conversation is short, so the history *is* the memory — no summarisation, no vector store,
no slot-tracking state machine. This is the honest simple answer and the README will defend it
rather than apologise for it. The Protocol marks the seam where Redis or Postgres would go for a
multi-worker deployment; naming the seam without building it is the point.

### 6.4 Booking

Gemini **function calling**, not prompt roleplay:

```python
book_site_visit(name: str, phone: str, date: str, time_slot: str) -> BookingResult
```

`booking.py` genuinely accepts or rejects. Rejection rule, documented in the README so a reviewer
can reproduce it on demand:

> **Sunday 11:00–13:00 is always `FULLY_BOOKED`.**

This makes *"handle a failed booking correctly"* a real code path with a real recovery
conversation, rather than the model acting out a failure it was told to imagine.

### 6.5 Analytics

One extraction pass over the finished transcript, using a Pydantic model as the Gemini response
schema. Fields:

```
name · phone · source · language_preference
budget_min · budget_max · budget_was_stated
configuration_interest · purpose · timeline · possession_preference
loan_required · preferred_location
interest_level (hot|warm|cold) · qualification_score (0-100)
site_visit_status (booked|attempted_failed|declined|not_discussed) · booking_datetime
follow_up_required · follow_up_reason · callback_time
objections_raised[] · unknown_questions_asked[]
do_not_contact · escalation_requested
summary · next_action
```

The field list deliberately mirrors what Huvo's own product states it captures — *"name, contact,
source, budget, location, configuration, timeline, intent, site-visit interest, callback time,
objections, score, summary, and next action"* — plus `do_not_contact` and
`unknown_questions_asked[]`, which are ours.

`unknown_questions_asked[]` is worth its own line of defence: every question the agent could not
answer is a gap in the fact sheet. Logging them turns a limitation into a product feedback loop,
which is the difference between a bot and a deployed system.

Two further deliberate choices:

- **`budget_was_stated` is separate from `budget_min/max`.** A null budget must be distinguishable
  from an inferred one. Without this flag, "not mentioned" and "model guessed" look identical
  downstream — which is exactly how invented data enters a CRM.
- **`qualification_score` comes from a written rubric** in the extraction prompt, not from asking
  the model for a number. Rubric scores are reproducible and auditable; vibe scores are neither.

### 6.6 Voice mode

Browser Web Speech API: `SpeechRecognition` for input, `speechSynthesis` for output.

The toggle does more than enable the microphone — it sets `channel="voice"` on every request,
which swaps the prompt delta. The same core prompt then visibly produces shorter, markdown-free,
"one crore thirty-five lakh" replies. This demonstrates the dual-channel claim on camera instead
of asserting it in a README.

TTS voice selection uses a client-side heuristic: Devanagari characters present → `hi-IN`,
otherwise `en-IN`. Deliberately not a model call — it must not add latency to every turn.

Supported in Chrome, Edge and Safari (all behind the `webkitSpeechRecognition` prefix); Firefox
keeps it behind a flag. The UI feature-detects and hides the toggle where unsupported rather than
naming a required browser.

## 7. Error handling

| Failure | Behaviour |
|---|---|
| Gemini timeout / 5xx | One retry, then a graceful in-character message |
| Rate limit (429) | Fall back to `flash-lite`, surface a clear banner |
| Missing API key | Fail fast at startup with an actionable message |
| Unknown `session_id` | Create a new session rather than erroring |
| Malformed analytics JSON | Schema-constrained, so structurally impossible; still caught |
| Booking tool failure | Not an error — a designed conversational path (§6.4) |
| Speech API unsupported | Hide the toggle, chat still works |

## 8. Testing

Two layers, because the assignment's literal ask and good engineering practice want different things.

**`test_api.py`** and its siblings — deterministic, LLM mocked, no API key. Routing and session
lifecycle in `test_api.py`, availability rules in `test_booking.py`, the scoring rubric and the
booking ground-truth override in `test_analytics.py`, throttling in `test_llm.py`.

**`test_scenarios.py`** — live model, twelve scenarios, marked `live` and deselected unless asked
for, writes `tests/RESULTS.md` with
**input / expected behaviour / actual output** per the assignment's wording. Committed to the repo
so a reviewer can read the evidence without running anything or holding a key.

Scenarios: happy-path booking · budget objection · pure Hindi · Hinglish code-mix · busy customer ·
call-me-later · **stop contacting** · **hallucination bait** · **booking failure** · human
escalation · uninterested customer · memory and proper ending.

The hallucination-bait scenario uses the exact question topics Huvo's own site advertises handling
— **carpet area, possession date, brochure, current offers, payment plans** — plus "give me a 10%
discount" and "what is the RERA number". None of these are in the five-fact sheet, so every one is
a hallucination opportunity. These are the questions Huvo knows real buyers ask, which makes them
the questions a reviewer will try.

The last three carry the most evaluative weight. Hallucination bait tests §4; the stop-contacting
scenario tests the one behaviour Huvo is regulated on.

## 9. Delivery

- [ ] Public GitHub repo: prompt, source, README, `.env.example`, no secrets
- [ ] README: how to run, assumptions, known limitations, AI tools used
- [ ] `tests/RESULTS.md` committed
- [ ] Demo video (< 4 min): bot working, sample conversation, prompt approach, implementation
- [ ] Email to aditi@huvo.ai, cc nikhil@ vaibhav@ rohit@

## 10. Non-goals

Explicitly **not** built, because *"keep the implementation simple"* is a stated instruction and
violating it is evidence of poor judgement, not extra effort:

database · authentication · Docker · response streaming · RAG · real telephony integration ·
multi-tenant support · admin dashboard · conversation summarisation

## 11. Risks

| Risk | Mitigation |
|---|---|
| Free-tier quota exhausted mid-demo | `flash-lite` fallback; record video before final testing |
| Model drifts to English after 2–3 Hindi turns | Explicit persistence rule in language policy; scenario test |
| Model invents facts under pressure | Fenced fact sheet + unknown protocol + dedicated bait test |
| Web Speech flaky on camera | Chat mode is the primary demo; voice is a segment, not the spine |
| Over-building | §10 is a commitment, re-read before adding anything |


---

## 12. Amendments

This document was written before the implementation, on 2026-09-05, and is kept as the record of
what was planned. Four things went differently. They are corrected here rather than edited above,
so the design and the divergence both stay legible.

**Models (§3).** The plan led with `gemini-3.8-flash` and held `gemini-2.5-flash` in reserve. The
free tier turned out to be metered per model, with a *daily* cap that binds far harder than the
per-minute one — as few as 20 requests a day on the stronger models, which one scenario run
exhausts twice over. The shipped configuration therefore leads with `gemini-3.5-flash-lite`, falls
back *up* to `gemini-3.8-flash`, and gives the analytics pass its own third bucket
(`gemini-3.1-flash-lite`) so the end-of-conversation extraction never competes with the
conversation. `3.5-flash-lite` was also chosen on measured behaviour, not only quota: it answers
romanized Hinglish in romanized Hinglish, where `3.1-flash-lite` drops into English.

**No rate-limit banner (§7).** The plan promised a banner on 429. What shipped is a 13-second
per-model throttle that turns a burst into a queue, plus fallback to a second model, plus an
in-character message if both are exhausted. The user never sees a rate limit as a rate limit,
which is better than being told about one — so the banner was not built.

**The rubric moved out of the prompt (§6.5).** The plan put the scoring rubric in the extraction
instruction and asked the model for the total. That is not reproducible: the model's arithmetic
was wrong on three of the four scored scenarios, once across the hot/warm boundary. The rubric is
now applied in `analytics.score()`, and the model supplies only the judgements that feed it.

**Booking outcomes are enforced, not merely supplied (§6.5).** The plan fed the tool's record to
the extraction prompt as authoritative context. That held when a booking had been attempted and
failed, and did not hold when the tool had never been called at all — the model read a confident
agent and recorded a booking that did not exist. `site_visit_status` and `booking_datetime` are
now overwritten from `session.bookings` in code after extraction, so the transcript cannot outvote
the tool.
