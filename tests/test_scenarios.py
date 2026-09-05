"""Live scenario runner.

Drives every scenario through the real app against the live model and writes
`tests/RESULTS.md` in the form the assignment asks for: input, expected
behaviour, actual output.

Skipped automatically when GEMINI_API_KEY is absent, so a fresh clone with no
credentials still runs a green deterministic suite.

Run with:  uv run pytest tests/test_scenarios.py -v -s
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.scenarios import SCENARIOS

pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY") and not Path(".env").exists(),
    reason="needs a live GEMINI_API_KEY",
)

RESULTS = Path(__file__).parent / "RESULTS.md"


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
        "name", "phone", "configuration_interest", "budget_min", "budget_max",
        "budget_was_stated", "purpose", "timeline", "interest_level",
        "qualification_score", "site_visit_status", "booking_datetime",
        "follow_up_required", "callback_time", "objections_raised",
        "unknown_questions_asked", "do_not_contact", "escalation_requested",
        "next_action",
    ]
    return {k: record[k] for k in keep if k in record and record[k] not in (None, [], "")}


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
        "Reproduce with `uv run pytest tests/test_scenarios.py -v -s`.",
        "",
        "---",
        "",
    ]

    for scenario in SCENARIOS:
        print(f"\n=== {scenario.id}: {scenario.title} ===")
        result = _run(client, scenario)

        lines += [
            f"## {scenario.id} — {scenario.title}",
            "",
            f"**Channel:** `{scenario.channel}`",
            "",
            f"**Expected behaviour:** {scenario.expected}",
            "",
        ]
        if scenario.notes:
            lines += [f"> {scenario.notes}", ""]

        lines += ["**Actual output:**", ""]
        for user, reply in result["exchanges"]:
            print(f"  YOU  : {user}")
            print(f"  PRIYA: {reply}")
            lines += [f"> **Customer:** {user}", ">", f"> **Priya:** {reply}", ""]

        if result["analytics"]:
            trimmed = _interesting(result["analytics"])
            print(f"  ANALYTICS: {trimmed}")
            lines += [
                "**Extracted analytics:**",
                "",
                "```json",
                json.dumps(trimmed, indent=2, ensure_ascii=False),
                "```",
                "",
            ]

        lines += ["---", ""]

    RESULTS.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {RESULTS}")

    assert len(SCENARIOS) == 10
