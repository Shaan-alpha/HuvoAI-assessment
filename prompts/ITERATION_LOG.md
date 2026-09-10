# Prompt iteration log

How the prompt in [`system_prompt.md`](system_prompt.md) got to its current state. Each revision
records the **failure actually observed** against the live model, not a change made on a hunch.

Everything here was found by running [`tests/scenarios.py`](../tests/scenarios.py) against
`gemini-3.8-flash` and reading the transcripts.

---

## v1 — first draft

Written from the assignment brief plus what Huvo's own product page says its agents handle:
price, configuration, carpet area, location, possession, brochure, offers, callbacks, site visits,
investment vs end-use, payment plans.

Structure chosen up front:

- A fenced `<facts>` block declared the only source of truth, with an explicit list of what is
  *not* known. The assignment supplies five facts and forbids inventing anything else, so most
  realistic buyer questions fall outside them — see the note on this in [`../docs/DESIGN.md`](../docs/DESIGN.md).
- Language policy separating three cases, not two: English, Hindi in Devanagari, and **romanized
  Hinglish**. Answering romanized Hindi *in Devanagari* is the standard model failure.
- Eleven named protocols, one per required behaviour.
- All behaviour in the core; channel files change only rendering.

**What already worked on first contact.** Voice channel, cold, no priming:

> Hello sir, I am Priya from Northstar Homes, calling regarding your enquiry for Northstar One in
> Sector 79, Gurugram. Is this a good time to speak for a moment?

Two sentences, no markdown, greets → identifies → asks permission. And the unknown-question
protocol fired correctly in Hinglish on the first attempt:

> **Customer:** carpet area kitna hai aur possession kab milega?
> **Priya:** Yeh dono bohot zaroori baatein hain, par exact carpet area aur possession date mere
> paas abhi confirmed nahi hai. Main hamari sales team se bolkar aapko yeh details share karwa
> sakti hoon, kya aapka shubh naam jaan sakti hoon?

Acknowledged, declined to guess, offered a route, kept moving. Nothing invented.

---

## v2 — three failures from the first full scenario run

### Failure 1 — greeting instead of answering

Scenario 02 opened with a direct question and got an introduction with no answer in it:

> **Customer:** What's the price for a 2 BHK?
> **Priya:** Hi there! I'm Priya, a pre-sales consultant at Northstar Homes. I'm here to help you
> with Northstar One.

The price is one of five facts the agent definitely knows, and it still made the customer ask
twice. The conversation-flow section said "greet, then understand what they're looking for", and
the model followed that order literally even when the customer had already told it.

**Change:**

> **Answer the question you were asked, first.** If the customer opens with a direct question,
> answer it in your first sentence and introduce yourself around that answer — never make them ask
> twice. A greeting is not a substitute for a reply.

### Failure 2 — turns that advanced nothing

Scenario 01, mid-qualification:

> **Customer:** To live in. Planning to buy in the next 2 months
> **Priya:** That is a great timeline, and Northstar One in Sector 79, Gurugram would be a
> wonderful choice for your home.

Warm, agreeable, and completely inert. It asked nothing, proposed nothing, and burned a turn — the
single most common way a sales conversation dies. "One question per turn" had been read as
permission to sometimes ask none.

**Change:**

> **Every turn must move forward.** End with a question, a proposal, or a clear next step. Never
> send a turn that only agrees or compliments. "That's a great timeline" is not a reply; "That's a
> great timeline — shall we get you a site visit this week?" is.

### Failure 3 — confident, wrong dates

Scenario 01, booking:

> **Priya:** Great! This Saturday, September 7th, works perfectly.

Today was Saturday 5 September 2026. The 7th was a **Monday**. The agent had today's date in its
context and still produced a weekday and a date that contradicted each other — then carried the
wrong date into the booking confirmation.

This is not a prompt-wording problem. Models are bad at calendar arithmetic and good at reading a
table, so the fix was to stop asking it to calculate.

**Change** — `runtime_context()` in [`../app/prompt.py`](../app/prompt.py) now injects a lookup
table instead of a single date:

```
The next few days, for booking:
  Saturday 05 September 2026 = 2026-09-05   (today)
  Sunday 06 September 2026 = 2026-09-06
  Monday 07 September 2026 = 2026-09-07
  ...
Read the exact date off this table. Do not calculate it yourself, and do not state a
weekday and a date that disagree with the table.
```

### Also fixed alongside

Not prompt changes, but found by the same run and worth recording:

- **The fallback model had never worked.** `thinking_level` is a Gemini 3.x parameter;
  `gemini-2.5-flash` rejects it with `400 INVALID_ARGUMENT`. So whenever the primary hit a rate
  limit, the fallback 400'd immediately and the customer saw a connection error. `thinking_for()`
  now selects the parameter by model generation.
- **The throttle was set for the wrong limit.** The free tier allows **5 requests per minute per
  model**; the original 4-second floor permitted 15. Raised to 13s, and made per-model so a
  fallback does not inherit the primary's cooldown.
- **Thinking tokens were eating replies.** `gemini-3.8-flash` spent 88 thinking tokens to produce
  a 1-token answer, and returned a completely empty reply under a small output budget. Pinned to
  `thinking_level=LOW` — `MINIMAL` is rejected by this model.

---

## v3 — booking on an assumption

With v2 in place all ten scenarios ran clean, including the two that had never been exercised:
the opt-out and the booking failure. The date table worked — scenario 09 correctly offered
"Monday, 7th September", and scenario 01 noticed that "this Saturday" was genuinely ambiguous
because the conversation was *happening* on a Saturday:

> **Priya:** Wonderful — did you mean today, or next Saturday on 12 September, and what time slot
> between 10:00 and 18:00 would you prefer?

Good question. Then:

> **Customer:** Amit Sharma, 9876543210. 11 am works
> **Priya:** Got it, Amit! I have booked your site visit for **today, 05 September 2026**, from
> 11:00 to 12:00.

The customer never answered which Saturday. The agent asked a genuinely necessary question, did
not get an answer, and booked anyway on an assumption. A site visit scheduled for a day the
customer did not choose is a wasted trip and an angry callback — and it is exactly the failure a
booking flow exists to prevent.

The prompt already said "read the details back for confirmation before booking". That was not
enough, because from the model's point of view it *had* confirmed — it recited details back, they
just included an invented one.

**Change:**

> If you asked a clarifying question about the booking and the customer did not answer it, ask
> again before booking. Never resolve an ambiguity by assuming. If you asked "today or next
> Saturday?" and they replied only with a name and a time, you still do not have the date — ask
> for it. A visit booked on a day the customer did not choose is worse than one more question.

The general lesson, and the reason it is worth recording: "confirm before acting" is too abstract
to constrain a model. Naming the specific failure — *you asked, they didn't answer, you assumed* —
is what makes the rule bite.

**Honest note on verification.** The v3 run did not reproduce the original path, so the new rule
was never exercised. Generation runs at temperature 0.7, and this time the agent skipped the
clarifying question entirely and booked directly:

> **Priya:** Your site visit for Northstar One is confirmed for **today, Saturday, 05 September
> 2026**, from 11:00 to 12:00.

That is defensible — "this Saturday" said *on* a Saturday most naturally means today, and stating
the weekday and full date back makes any error immediately catchable by the customer. But it is
not proof the v3 rule works; it is a different path through the same scenario. Confirming the rule
properly needs either a fixed seed or a scenario written specifically to force the ambiguity.
Recorded as unverified rather than claimed as fixed.

---

## v4 — a rule from v2 turned out to block the ending

A full audit against the brief found two requirements with prompt protocols but no scenario
testing them: *"busy **or uninterested** customers"* — I had tested busy and never uninterested —
and *"proper conversation ending"*. Adding both immediately exposed a regression **I had
introduced in v2**.

Scenario 12, on the customer's closing line:

> **Customer:** Alright, let's leave it there for now
> **Priya:** No problem at all, Rohan. Before we leave it there, **is it the timing or something
> else that made you want to wait?**

The ENDING protocol says summarise what was agreed and confirm the next step. Instead the agent
asked another question — because v2's *"Every turn must move forward. End with a question, a
proposal, or a clear next step"* was doing exactly what it said, on a turn where it should not
have applied. A fix for inert turns had made the agent unable to gracefully stop.

This is the failure mode of prompt rules that read as universal: they apply universally, including
where they do harm. The fix is not to weaken the v2 rule — inert turns are still bad — but to name
its exception.

**Change:**

> **Except when the customer is closing.** "Let's leave it there", "I'll think about it and get
> back", "that's all for now", "thanks, bye" — these end the conversation. Do not ask another
> question. Follow the ENDING protocol instead: summarise, confirm the next step, thank them by
> name. Squeezing in one more question after someone has said goodbye is the single most
> irritating thing a salesperson does.

Worth noting what v4's scenarios showed working. Memory is solid — given six details in one
opening line, the agent used his name immediately and again at the close, and never re-asked the
budget, configuration, loan requirement, purpose or timeline. And the uninterested path was right
first time:

> **Customer:** Honestly I'm not interested
> **Priya:** I completely understand. Is it the location, the budget, or the timing that didn't
> quite fit for you?
> **Customer:** No, we've decided to stay where we are
> **Priya:** That makes complete sense, and staying put is often the best choice. Thank you for
> your time today, and have a wonderful weekend!

Asked once, accepted the second refusal, validated the decision rather than fighting it, closed
warmly. No third attempt.

---

## What survived every round

Worth noting what never needed changing, because it says which parts of the design were right
from the start:

- **The fenced `<facts>` block.** Across four bait turns covering carpet area, possession, RERA
  number, offers, payment plans and brochure contents, the agent invented nothing — not a range,
  not a "typically". Every one was captured in `unknown_questions_asked`.
- **Script mirroring.** Devanagari in, Devanagari out. Romanized Hinglish in, romanized Hinglish
  out. Never once crossed over, which was the failure mode most expected.
- **The core/delta split.** No behavioural rule ever needed to be duplicated into a channel file.
- **The opt-out protocol.** Correct on first contact: stopped selling, apologised once, confirmed
  removal, no rebuttal, no final pitch, `do_not_contact: true`.

---

## v5 — two failures the transcripts had been showing all along

Both of these were sitting in the committed `RESULTS.md` from the v4 run. Neither was caught by
reading the prompt, and neither would have been caught by a scenario expectation — the scenarios
assert what the agent should *do*, and these are failures in how it *says* it.

### Failure 1 — the language rule only worked in one direction

Scenario 09, opening turn, chat channel:

> **Customer:** I want to book a site visit
> **Priya:** Bilkul sir, main aapki site visit book karwa deti hoon. Northstar One ke liye aap kis
> date aur time slot mein aana chahenge?

Plain English in, Hinglish out. The language section had three cases and a worked example, but the
example only demonstrated the crossover everyone expects — romanized Hindi answered in Devanagari.
Nothing named the opposite drift, so the model treated Hinglish as the register of the *domain*
rather than a mirror of the customer, and code-mixed at someone who never had.

This is the more embarrassing failure of the two. A customer writing English to a Gurugram
developer is often doing it deliberately.

**Change:**

> Drift in the other direction is just as wrong. If they write plain English, reply in plain
> English — do not slide into Hinglish because the subject is Indian real estate. "I want to book
> a site visit" gets "Of course, let me get that set up for you", not "Bilkul sir, main aapki site
> visit book karwa deti hoon".

Plus a clause on the persistence rule: *do not start code-mixing a customer who never did.*

Same scenario, same opening turn, after:

> **Priya:** Of course! I am Priya from Northstar Homes. To get your site visit for Northstar One
> scheduled, could you please let me know your preferred date and time slot between 10:00 and
> 18:00?

### Failure 2 — an invented operating hour, used to overrule the customer

Scenario 06:

> **Customer:** Tuesday evening after 7
> **Priya:** Understood sir, I will have our team call you on Tuesday the eighth around five PM
> **since we wrap up by six**. Have a wonderful weekend!

Three things wrong in one sentence. "We wrap up by six" is a fact about the company that appears
nowhere in `<facts>` — a straight hallucination, in the one scenario nobody thinks to check for
hallucinations because it is not the hallucination test. It was then used to *overrule* a time the
customer had explicitly given. And the number it came from is the site-visit window, 10:00 to
18:00, which is about when the site is open to visitors and says nothing about when anyone makes
phone calls.

The `<facts>` block was doing its job on every question a customer asks. It was not doing it on
scheduling, because the agent was not answering a question — it was making an arrangement, and the
one operational number it had drifted into a domain it does not cover.

**Change:**

> Repeat back the time *they* gave you and accept it. Never counter-offer a different time, and
> never justify one with an office hour, a closing time or a working day — you do not know any of
> those. The 10:00 to 18:00 window in `<facts>` is when the SITE is open for visits. It says
> nothing about when the team makes phone calls, so it is never a reason to move a callback.

After:

> **Customer:** Tuesday evening after 7
> **Priya:** Got it, I will call you on Tuesday evening after seven. Have a great day!

### The general lesson

v2 and v3 were about the agent doing the wrong thing. These two are about it saying something
false or off-register while doing the right thing, which is why re-reading the prompt never found
them and reading the transcripts did. The scenario expectations encode the required *behaviour*;
they cannot encode "and do not invent a closing time while you do it". Only the transcript shows
that, and only if someone reads all of it rather than checking whether each scenario passed.

---

## v6 — a refusal that did not survive its own turn

Found by re-reading the regenerated transcripts rather than by checking whether the scenarios
passed. Scenario 09 passed. It was still wrong.

With the scenario dates made relative, the booking-failure path fired properly for the first time
in a while, and the recovery turn was exactly right:

> **Customer:** This Sunday, 11 am
> **Priya:** I am so sorry, but the 11:00 to 12:00 slot for this Sunday is fully booked. Would
> 10:00 to 11:00 or 13:00 to 14:00 work for you instead?

Both alternatives genuinely free. Then the very next turn:

> **Customer:** Okay, what else do you have?
> **Priya:** We also have 12:00 to 13:00 or 14:00 to 15:00 available this Sunday.

12:00 to 13:00 is inside the same full window. The agent had just been told the window was full,
relayed it accurately, and then offered another slot from inside it one turn later — and stated it
as *available*, which it had no way of knowing about any slot.

The cause is structural, not a wording problem. The SDK runs the function-calling loop inside a
single `send_message`, so the tool's reply is never stored as a turn. What the model sees on the
next turn is its own previous sentence — "the 11:00 to 12:00 slot is fully booked" — and from
that, 12:00 to 13:00 looks untried. The tool's actual message had named the whole window and
listed the free slots, and that message was gone.

Worth being precise about what failed. The README had claimed the agent's own reply carried the
outcome forward well enough that not persisting tool calls was a documented non-issue. It carried
the outcome and dropped the constraint, which is the half that matters for recovery.

**Change, in the prompt** — the booking-failure protocol now says where alternatives come from:

> Read the alternatives out of what the tool told you. If it named a full window, every time
> inside that window is also full — offering another one of them wastes the customer's second
> choice as well as their first. And you do not otherwise know what is free: never tell a customer
> a slot is available. Propose a time, then let the tool confirm it.

**Change, in code** — `prompt.booking_context()` replays every attempt and the tool's own reply
into the system instruction on each turn, so a refusal keeps its reason for the rest of the
conversation. `BookingRecord` gained a `message` field to hold it.

After:

> **Customer:** Okay, what else do you have?
> **Priya:** We have other slots later that afternoon, Priya. Would 14:00 to 15:00 or 15:00 to
> 16:00 work for you?

### The general lesson

This one is not a prompt-wording failure, and no amount of re-reading the prompt would have found
it — the prompt said the right thing and the model followed it with the information it had. The
information was missing. It is the second time in this log that a scenario "passed" while the
transcript showed something wrong, which is the argument for committing transcripts rather than
just test results: a green suite tells you the agent did the required thing, not that everything
it said was true.
