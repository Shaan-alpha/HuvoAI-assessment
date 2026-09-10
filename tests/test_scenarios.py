"""Live scenario runner.

Drives every scenario through the real app against the live model and writes
`tests/RESULTS.md` in the form the assignment asks for: input, expected
behaviour, actual output.

Marked `live` and deselected by default, and skipped outright when no
GEMINI_API_KEY is present, so a fresh clone runs a green deterministic suite
either way.

Run with:  uv run pytest tests/test_scenarios.py -m live -v -s
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.scenarios import SCENARIOS

# Marked, not module-skipped. A module-level skip made this suite run whenever
# a .env happened to exist — turning the documented fast command into a
# multi-minute live run against a metered quota — while also hiding the
# deterministic helper tests in this file behind the same condition.
live = pytest.mark.live

RESULTS = Path(__file__).parent / "RESULTS.md"


def say(text: str) -> None:
    """Print without dying on a non-UTF-8 console.

    A Windows console defaults to cp1252, which cannot encode Devanagari — the
    Hindi scenario killed an entire twelve-minute run on a print statement.
    The file is always written as UTF-8; only the console echo degrades.
    """
    encoding = sys.stdout.encoding or "utf-8"
    print(text.encode(encoding, errors="replace").decode(encoding))


def _quote(label: str, text: str) -> list[str]:
    """Render one speech turn as a markdown blockquote.

    Every line needs its own `>`. Without it a reply containing a blank line —
    which the chat channel produces whenever it uses a paragraph break — ends
    the quote early, and the rest of the turn renders as body text in the
    document a reviewer actually reads.
    """
    lines = text.splitlines() or [""]
    out = [f"> **{label}:** {lines[0]}"]
    out += [f"> {line}" if line.strip() else ">" for line in lines[1:]]
    return out


def _run(client: TestClient, scenario) -> dict:
    session_id = None
    exchanges = []
    for turn in scenario.turns:
        res = client.post(
            "/api/chat",
            json={"message": turn, "session_id": session_id, "channel": scenario.channel},
        )
        res.raise_for_status()
        body = res.json()
        session_id = body["session_id"]
        exchanges.append((turn, body["reply"]))

    record = None
    if scenario.analytics and session_id:
        res = client.post(f"/api/analytics/{session_id}")
        if res.status_code == 200:
            record = res.json()

    return {"exchanges": exchanges, "analytics": record}


def _interesting(record: dict) -> dict:
    """Trim the analytics record to the fields worth reading in a report."""
    keep = [
        "name", "phone", "source", "language_preference",
        "configuration_interest", "budget_min", "budget_max", "budget_was_stated",
        "purpose", "timeline", "timeline_within_six_months",
        "possession_preference", "loan_required",
        "preferred_location",
        "interest_level", "qualification_score",
        "site_visit_status", "booking_datetime",
        "follow_up_required", "follow_up_reason", "callback_time",
        "objections_raised", "unknown_questions_asked",
        "do_not_contact", "escalation_requested",
        "summary", "next_action",
    ]
    return {k: record[k] for k in keep if k in record and record[k] is not None and record[k] != [] and record[k] != ""}


@live
@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY") and not Path(".env").exists(),
    reason="needs a live GEMINI_API_KEY",
)
def test_run_all_scenarios():
    client = TestClient(app)
    lines: list[str] = [
        "# Scenario test results",
        "",
        f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC against the live model, "
        "through the real FastAPI app.",
        "",
        "Each scenario shows the **input**, the **expected behaviour**, and the **actual output**.",
        "Analytics records are the real extraction output, trimmed to the populated fields.",
        "",
        "Reproduce with `uv run pytest tests/test_scenarios.py -m live -v -s`.",
        "",
        "---",
        "",
    ]

    failures: list[str] = []
    try:
        _drive(client, lines, failures)
    finally:
        # Always write what we have. A twelve-minute run must not be lost to a
        # failure in its last scenario.
        RESULTS.write_text("\n".join(lines), encoding="utf-8")
        say(f"\nWrote {RESULTS}")

    assert len(SCENARIOS) == 12
    assert not failures, f"{len(failures)} scenario(s) failed to run: {failures}"


def _drive(client, lines, failures):
    for scenario in SCENARIOS:
        say(f"\n=== {scenario.id}: {scenario.title} ===")
        try:
            result = _run(client, scenario)
        except Exception as err:
            # One scenario dying must not throw away nine good transcripts.
            say(f"  !! FAILED: {str(err)[:200]}")
            failures.append(f"{scenario.id}: {str(err)[:200]}")
            lines += [
                f"## {scenario.id} — {scenario.title}",
                "",
                f"**Expected behaviour:** {scenario.expected}",
                "",
                f"**Actual output:** run failed — `{str(err)[:300]}`",
                "",
                "---",
                "",
            ]
            continue

        # Input / expected behaviour / actual output, labelled separately and in
        # that order, because that is the wording the brief asks for.
        lines += [
            f"## {scenario.id} — {scenario.title}",
            "",
            f"**Channel:** `{scenario.channel}`",
            "",
            "**Input:**",
            "",
        ]
        lines += [f"{i}. {turn}" for i, turn in enumerate(scenario.turns, 1)]
        lines += [
            "",
            f"**Expected behaviour:** {scenario.expected}",
            "",
        ]
        if scenario.notes:
            lines += [f"> {scenario.notes}", ""]

        lines += ["**Actual output:**", ""]
        for user, reply in result["exchanges"]:
            say(f"  YOU  : {user}")
            say(f"  PRIYA: {reply}")
            lines += _quote("Customer", user) + [">"] + _quote("Priya", reply) + [""]

        if result["analytics"]:
            trimmed = _interesting(result["analytics"])
            say(f"  ANALYTICS: {trimmed}")
            lines += [
                "**Extracted analytics:**",
                "",
                "```json",
                json.dumps(trimmed, indent=2, ensure_ascii=False),
                "```",
                "",
            ]

        lines += ["---", ""]


def test_multi_line_replies_stay_inside_the_blockquote():
    """The chat channel uses paragraph breaks, and a bare `>` prefix on only
    the first line drops the rest of the reply out of the quote in the
    document a reviewer actually reads."""
    quoted = _quote("Priya", "Rs 1.35 crore onwards.\n\nAre you buying to live in?")
    assert quoted == [
        "> **Priya:** Rs 1.35 crore onwards.",
        ">",
        "> Are you buying to live in?",
    ]
    assert all(line.startswith(">") for line in quoted)
