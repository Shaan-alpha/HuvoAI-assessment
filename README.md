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
uv run pytest tests/ -q                     # 48 deterministic tests, no API key needed
uv run pytest tests/test_scenarios.py -s    # 10 live scenarios, regenerates RESULTS.md
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

---

## Analytics

Ending a conversation runs one schema-constrained extraction pass over the transcript. The field
list mirrors what a real pre-sales CRM captures — name, contact, source, budget, location,
configuration, timeline, intent, site-visit interest, callback time, objections, score, summary,
next action — plus `do_not_contact` and `unknown_questions_asked`.

Three decisions worth explaining:

**`budget_was_stated` is separate from `budget_min`/`budget_max`.** A budget the customer never
gave must be distinguishable from one the model inferred. Without the flag, "not mentioned" and
"guessed" look identical downstream — which is exactly how invented data reaches a CRM and a
salesperson acts on it.

**`qualification_score` comes from a written rubric**, not from asking the model for a number out
of ten. The rubric is in [`app/analytics.py`](app/analytics.py): specific points for a stated
budget at or above the floor, a stated configuration, a timeline inside six months, a booked visit,
a stated purpose, and a shared phone number. Rubric scores are reproducible and auditable; vibe
scores are neither.

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
- **Free-tier quota is tight, and the daily cap binds hardest.** 5 requests per minute per model,
  but also as few as 20 per *day* on the stronger models — one scenario run exhausts that twice
  over. Three separate models are used (chat, fallback, analytics) precisely because quota is
  metered per model, and calls are serialised behind a 13-second floor so heavy use queues rather
  than failing. A full scenario run takes about six minutes.
- Analytics is a single pass at conversation end, not incremental slot-filling per turn.
- **Tool calls are not replayed into history.** Only the customer's text and the agent's text are
  stored per turn; the function-call and function-response parts are not. In practice the agent's
  own reply carries the outcome forward — scenario 09 recovers correctly from a failed booking on
  a later turn — and `session.bookings` holds the authoritative record, which is fed to analytics.
  But an agent making many tool calls across a long conversation would want them persisted.
- **Sessions are never evicted.** The in-memory store grows for the life of the process. Fine for
  a demo; a TTL is the first thing to add alongside a real session backend.
- No database, authentication, or CRM integration. Out of scope by design.

## AI tools used

Claude (Claude Code) was used throughout — for researching the free-tier and SDK constraints,
drafting the design, writing the implementation, and iterating on the prompt against the scenario
transcripts. Every design decision, the prompt architecture, and the choices documented above were
reviewed and directed by me. Two bugs the live runs exposed — the fallback model being
misconfigured, and the throttle being set for the wrong rate limit — are written up in the commit
history.
