import pytest

from app.prompt import compose


def test_compose_chat_includes_core_and_chat_delta():
    text = compose("chat")
    assert "You are Priya" in text
    assert "CHANNEL: CHAT" in text
    assert "CHANNEL: VOICE" not in text


def test_compose_voice_includes_core_and_voice_delta():
    text = compose("voice")
    assert "You are Priya" in text
    assert "CHANNEL: VOICE" in text
    assert "CHANNEL: CHAT" not in text


def test_both_channels_share_identical_core():
    core = "# PROTOCOLS"
    assert core in compose("chat")
    assert core in compose("voice")


def test_facts_block_is_present_in_both_channels():
    for channel in ("chat", "voice"):
        assert "Rs 1.35 crore" in compose(channel)
        assert "<facts>" in compose(channel)


def test_deltas_only_change_rendering_not_behaviour():
    """The core must be byte-identical across channels.

    This is the load-bearing claim of the whole design: one prompt, two
    channels. If behaviour ever leaks into a delta, this test fails.
    """
    chat_core = compose("chat").split("\n\n---\n\n")[0]
    voice_core = compose("voice").split("\n\n---\n\n")[0]
    assert chat_core == voice_core


def test_unknown_channel_rejected():
    with pytest.raises(ValueError, match="Unknown channel"):
        compose("telepathy")


def test_runtime_context_states_todays_date_readably():
    from datetime import date

    from app.prompt import runtime_context

    text = runtime_context(date(2026, 9, 5))
    assert "Saturday, 05 September 2026" in text
    assert "YYYY-MM-DD" in text


def test_compose_for_turn_appends_context_to_the_channel_prompt():
    from datetime import date

    from app.prompt import compose_for_turn

    text = compose_for_turn("voice", date(2026, 9, 5))
    assert "You are Priya" in text
    assert "CHANNEL: VOICE" in text
    assert "CURRENT CONTEXT" in text


def test_language_rule_names_drift_in_both_directions():
    """English in must mean English out.

    The scenario suite caught the reverse of the expected failure: an English
    request for a site visit answered in Hinglish. Only the Hinglish-to-
    Devanagari crossover had a worked example, so only that one was prevented.
    """
    core = compose("chat")
    assert "Do NOT switch to" in core          # Hinglish in -> not Devanagari out
    assert "do not slide into Hinglish" in core  # English in -> not Hinglish out


def test_site_visit_hours_are_not_callback_hours():
    """Asked to call after 7pm, the agent countered with 5pm 'since we wrap up
    by six' — an operating hour that appears nowhere in <facts>. The 10-18
    window is when the site is open to visitors, and nothing else."""
    core = compose("chat")
    assert "never justify one" in core
    assert "when the SITE is open for visits" in core


def test_no_channel_delta_leaks_a_behavioural_rule():
    """A delta may shape output. It may never decide what the agent does."""
    from app.prompt import _read

    for delta in ("channel_chat.md", "channel_voice.md"):
        text = _read(delta).lower()
        for behaviour in ("book_site_visit", "<facts>", "discount", "do not contact"):
            assert behaviour not in text, f"{delta} carries behaviour: {behaviour}"


def test_no_booking_block_before_any_booking_is_attempted():
    from datetime import date

    from app.prompt import compose_for_turn

    assert "BOOKINGS ALREADY ATTEMPTED" not in compose_for_turn("chat", date(2026, 9, 10))


def test_a_refusal_carries_its_constraint_into_the_next_turn():
    """The regression: the agent offered a second slot inside the same full window.

    The SDK runs function calling inside one send_message, so the tool's reply is
    never stored as a turn. The agent saw "Sunday 11:00-12:00 is full", said so,
    and on the next turn offered 12:00-13:00 — also full, because the whole
    11:00-13:00 window is. Its own reply carried the outcome forward but not the
    constraint behind it.
    """
    from datetime import date

    from app.booking import attempt
    from app.prompt import compose_for_turn
    from app.session import BookingRecord

    result = attempt("A", "9811122233", "2026-09-13", "11:00-12:00", today=date(2026, 9, 10))
    record = BookingRecord(
        ok=result.ok, date="2026-09-13", time_slot="11:00-12:00", message=result.message
    )
    text = compose_for_turn("chat", date(2026, 9, 10), [record])

    assert "BOOKINGS ALREADY ATTEMPTED" in text
    assert "2026-09-13 11:00-12:00" in text
    # the window the tool named, so the agent can avoid all of it
    assert "11:00 to 13:00" in text
    # and the slots it said were free
    assert "10:00-11:00" in text
    assert "never offer a time inside a window it named as full" in text


def test_a_successful_booking_is_replayed_with_its_reference():
    from datetime import date

    from app.prompt import compose_for_turn
    from app.session import BookingRecord

    record = BookingRecord(
        ok=True, date="2026-09-12", time_slot="11:00-12:00",
        reference="NS-20260912-2233", message="Site visit confirmed.",
    )
    text = compose_for_turn("chat", date(2026, 9, 10), [record])
    assert "ACCEPTED, reference NS-20260912-2233" in text


def test_the_agent_is_told_it_cannot_know_availability():
    """It only ever learns that a slot is taken, never that one is free."""
    # The prompt is hard-wrapped, so match on the flattened text rather than
    # letting a line break decide whether the rule is present.
    flat = " ".join(compose("chat").split())
    assert "never tell a customer a slot is available" in flat
    assert "every time inside that window is also full" in flat
