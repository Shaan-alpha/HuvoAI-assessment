# Northstar Homes — AI Sales Agent

A conversational sales agent for a fictional real-estate project, built for the Huvo AI Forward
Deployed Engineer assignment. It qualifies leads in English, Hindi and Hinglish, answers what it
genuinely knows, books site visits through a real tool call, recovers when a booking fails, and
extracts a structured lead record when the conversation ends.

**One system prompt drives both chat and voice.** That is the design's load-bearing claim, and
[a test enforces it](tests/test_prompt.py) rather than leaving it as an assertion in a README.

- **Prompt:** [`prompts/system_prompt.md`](prompts/system_prompt.md)
- **Design notes:** [`docs/DESIGN.md`](docs/DESIGN.md)
- **Scenario results:** [`tests/RESULTS.md`](tests/RESULTS.md)
- **Prompt iteration log:** [`prompts/ITERATION_LOG.md`](prompts/ITERATION_LOG.md)

---

## Run it

Needs Python 3.11+ and a free Gemini API key from
[aistudio.google.com/apikey](https://aistudio.google.com/apikey) — no card required.

```bash
git clone https://github.com/Shaan-alpha/HuvoAI-assessment
cd HuvoAI-assessment

cp .env.example .env        # then put your key in .env
uv sync
uv run uvicorn app.main:app --reload
```

Open <http://localhost:8000>.

<details>
<summary>Without <code>uv</code></summary>

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install fastapi "uvicorn[standard]" google-genai pydantic pydantic-settings
uvicorn app.main:app --reload
```
</details>

```bash
uv run pytest tests/ -q                            # 88 deterministic tests, no API key needed
uv run pytest tests/test_scenarios.py -m live -s   # 12 live scenarios, regenerates RESULTS.md
```

---

## The prompt

The prompt is split into a **channel-agnostic core** and a **channel delta** that changes only
how a reply is rendered:

```
prompts/system_prompt.md   ← all behaviour lives here
prompts/channel_chat.md    ← "Rs 1.35 crore", bullets allowed
prompts/channel_voice.md   ← "one crore thirty five lakh", max two sentences, no markdown
```

Behaviour is defined once. Only rendering varies. `test_deltas_only_change_rendering_not_behaviour`
asserts the core is byte-identical across channels, so behaviour cannot quietly leak into a delta
and split one agent into two.

The same input, both channels:

| | |
|---|---|
| **Customer** | `bhai 3 BHK ka rate kya hai? budget 1.8 cr hai` |
| **Voice** | Northstar One mein 3 BHK **one crore seventy five lakh** onwards shuru hota hai, toh yeh aapke budget mein bilkul fit baithega. Kya aap ise khud rehne ke liye dekh rahe hain ya investment ke liye? |
| **Chat** | Northstar One, Sector 79 mein 3 BHK **Rs 1.75 crore** onwards start hota hai, toh yeh aapke Rs 1.8 crore ke budget mein bilkul fit baithta hai.<br><br>Aap yeh apartment apne rehne ke liye dekh rahe hain ya investment ke purpose se? |

Adding a third channel — WhatsApp and SMS are the obvious next ones — costs one file, not a second
prompt to keep in sync.

### Not knowing things is the hard part

The assignment supplies exactly five facts, then forbids inventing anything else. A real buyer asks
about carpet area, possession, RERA registration, floor plans, offers and payment plans — **none of
which are among those five.** The agent is outside its knowledge on most realistic turns.

So the unknown-question protocol is the core behaviour here, not an edge case. It has a defined
four-step shape: acknowledge the question as fair, say plainly that the detail is not confirmed,
offer a concrete route to a real answer, and keep the conversation moving. After three unknowns the
agent stops saying "I'll find out" and offers a human, because by then it reads as evasive.

---

## Try each behaviour

| Type this | What should happen |
|---|---|
| `bhai 3 BHK ka rate kya hai?` | Replies in romanized Hinglish, **not** Devanagari |
| `मुझे 2 BHK चाहिए, कीमत क्या है?` | Replies in Devanagari and stays there |
| `I want to book a site visit` | Replies in plain English — does not slide into Hinglish |
| `carpet area kitna hai? possession kab?` | Invents nothing; offers a real route to an answer |
| `Any discount? 10% chalega?` | Declines plainly; never hints a discount is possible |
| `My budget is 90 lakh` | Says honestly the project starts at Rs 1.35 crore |
| `I'm in a meeting, call later` | Takes a specific time, confirms, stops selling |
| **`Don't ever call me again`** | Confirms removal, no rebuttal, no final pitch |
| **Book `Sunday, 11 am`** | **Booking fails** — see below |
| `Get me a real person` | Offers a human, confirms who calls and when |
| `Honestly I'm not interested` | Asks once why, accepts the second refusal, closes warmly |
| Give name + budget early, then `what's the location again?` | Never re-asks what you volunteered |

### Reproducing the booking failure

`book_site_visit` is a real tool call into [`app/booking.py`](app/booking.py), which genuinely
accepts or rejects. **Sunday 11:00–13:00 is always `FULLY_BOOKED`.**

Ask for a Sunday 11 am slot and the agent must state the failure plainly, apologise once, and offer
two alternatives — never claim success. Making the failure a real code path rather than something
the model is told to act out means the recovery conversation is genuine.

The rejection message names the slots that are actually free that day. It used to say only "offer
two alternatives", and the agent duly offered Sunday 12:00–13:00 — inside the same blocked window,
so the recovery would have failed a second time. A tool that refuses has to say enough for the
refusal to be recoverable.

Every rule the prompt states about booking is also enforced here: dates in the past, slots outside
10:00–18:00, slots that are not one hour on the hour, and impossible clock values are all
rejected. A rule that lives only in the prompt is a suggestion.

---

## Analytics

Ending a conversation runs one schema-constrained extraction pass over the transcript. The field
list mirrors what a real pre-sales CRM captures — name, contact, source, budget, location,
configuration, timeline, intent, site-visit interest, callback time, objections, score, summary,
next action — plus `do_not_contact` and `unknown_questions_asked`.

Four decisions worth explaining:

**`budget_was_stated` is separate from `budget_min`/`budget_max`.** A budget the customer never
gave must be distinguishable from one the model inferred. Without the flag, "not mentioned" and
"guessed" look identical downstream — which is exactly how invented data reaches a CRM and a
salesperson acts on it.

**`qualification_score` is computed in code, not asked of the model.** The rubric lives in
[`app/analytics.py`](app/analytics.py): points for a stated budget at or above the floor, a stated
configuration, a timeline inside six months, a booked visit, a stated purpose, and a shared phone
number.

Writing the rubric into the prompt and asking for the total was not enough. Across the scored
scenarios the model's arithmetic was wrong three times out of four — and on one lead it returned
65 where the rubric says 70, which is the hot/warm boundary, so the slip changed how a
salesperson would have prioritised the lead. The model now judges the facts, including the one
genuinely fuzzy input (`timeline_within_six_months`), and `score()` does the adding.
`interest_level` is derived from the computed total the same way. That is what makes the score
reproducible and auditable rather than merely described as such.

**The booking outcome is taken from the tool, never from the transcript.** `site_visit_status`
and `booking_datetime` are overwritten from `session.bookings` after extraction. This is not
theoretical: on an earlier run the agent talked as though a visit were settled, never actually
called the tool, and the extraction recorded `booked` with a date — awarding the 25 rubric points
that go with it. A lead wrongly marked booked is a missed appointment nobody chases. When the
tool never ran, the record now says `discussed_not_booked`, which is the true thing.

**`unknown_questions_asked` turns a limitation into a feedback loop.** Every question the agent
could not answer is a gap in the fact sheet. Logging them tells the business what to add next.

---

## Assumptions

- **Site-visit hours (10:00–18:00, one-hour slots) are an operational assumption**, not a project
  fact. The booking tool needs something to validate against. They are deliberately kept out of the
  `<facts>` block, so the agent still treats everything not supplied by the assignment as unknown.
- Sunday 11:00–13:00 is hard-coded as unavailable, to make the failure path reproducible on demand.
- The agent identifies as Northstar Homes' AI assistant if asked directly, rather than claiming to
  be human.
- Only name and mobile number are ever collected. Never PAN, Aadhaar or payment details.
- Indian mobile numbers are validated as ten digits beginning 6–9.

## Known limitations

- **Sessions are in-process** and lost on restart. Deliberate: a sales conversation is short, so
  full history *is* the memory, with no summarisation or slot-tracking state machine. The
  `SessionStore` Protocol in [`app/session.py`](app/session.py) is the seam — swapping in Redis or
  Postgres is the only change needed to run more than one worker.
- **Voice mode is browser speech, not telephony.** The Web Speech API works in Chrome, Edge and
  Safari; Firefox keeps it behind a flag, and the toggle hides itself where unsupported. The point
  of the toggle is that it flips the *channel* — real telephony would swap the transport, not the
  prompt.
- **Speech *recognition* is pinned to `en-IN`.** It handles English and romanized Hinglish, which
  is what most callers speak, but Devanagari-first speakers are transcribed badly. The reply side
  mirrors whatever script comes out of the recogniser, so the language policy itself is intact —
  the gap is input only, and a real telephony integration would bring its own ASR anyway.
- **The booking tool validates but does not hold inventory.** Two customers can book the same slot;
  there is no ledger behind it beyond the deterministic full window. A real deployment puts a
  calendar there, and that calendar is what `booking.attempt` is shaped to become.
- **Free-tier quota is tight, and the daily cap binds hardest.** 5 requests per minute per model,
  but also as few as 20 per *day* on the stronger models — one scenario run exhausts that twice
  over. Three separate models are used (chat, fallback, analytics) precisely because quota is
  metered per model, and calls are serialised behind a 13-second floor so heavy use queues rather
  than failing. A full scenario run takes about seventeen minutes, nearly all of it spent
  waiting in that throttle.
- Analytics is a single pass at conversation end, not incremental slot-filling per turn.
- **Tool calls are not replayed into history as turns.** The SDK runs the function-calling loop
  inside one `send_message`, so the call and its response are never stored alongside the text.
  This README used to claim the agent's own reply carried the outcome forward well enough. It
  does not, and the transcript showed it: told that Sunday 11:00–12:00 was full, the agent said
  so correctly and then offered 12:00–13:00 on the next turn — inside the same full window, and
  equally unbookable. Its reply carried the *outcome* forward but not the *constraint* behind it.
  `prompt.booking_context()` now replays the tool's own replies into the system instruction each
  turn, so a refusal keeps its reason. An agent making many tool calls over a long conversation
  would want the parts persisted properly rather than summarised like this.
- **Sessions are never evicted.** The in-memory store grows for the life of the process. Fine for
  a demo; a TTL is the first thing to add alongside a real session backend.
- No database, authentication, or CRM integration. Out of scope by design.

## AI tools used

Claude (Claude Code) was used throughout — for researching the free-tier and SDK constraints,
drafting the design, writing the implementation, and iterating on the prompt against the scenario
transcripts. Every design decision, the prompt architecture, and the choices documented above were
reviewed and directed by me.

The bugs the live runs exposed are written up where they were found rather than quietly fixed: the
misconfigured fallback model and the wrong throttle interval in
[`prompts/ITERATION_LOG.md`](prompts/ITERATION_LOG.md) v2, and a later audit pass — analytics
recording a booking the tool had never made, the rubric being added up by the model and added up
wrongly, a lock held across a sleep, and a microphone left open while the agent spoke — in the
commit history and in v5 and v6 of the same log.

The split is worth noting. The lock and the microphone were found by reading code. Everything
else — a booking recorded that never happened, three rubric totals that did not add up, an
invented office hour, an English question answered in Hinglish, a second slot offered from inside
a window the tool had just refused — was sitting in the committed transcripts, in scenarios that
had all been marked as passing. That is the argument for committing transcripts and not only
results.
