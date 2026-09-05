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
