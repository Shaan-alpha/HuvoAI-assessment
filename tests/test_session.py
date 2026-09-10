from app.session import BookingRecord, InMemoryStore, Session, Turn


def test_get_or_create_makes_new_session_when_id_is_none():
    store = InMemoryStore()
    s = store.get_or_create(None)
    assert s.id
    assert s.turns == []


def test_get_or_create_returns_same_session_for_same_id():
    store = InMemoryStore()
    a = store.get_or_create(None)
    a.turns.append(Turn(role="user", content="hi"))
    b = store.get_or_create(a.id)
    assert b is a
    assert len(b.turns) == 1


def test_unknown_id_creates_rather_than_raising():
    store = InMemoryStore()
    s = store.get_or_create("does-not-exist")
    assert s.id == "does-not-exist"
    assert s.turns == []


def test_reset_clears_turns_but_keeps_session():
    store = InMemoryStore()
    s = store.get_or_create(None)
    s.turns.append(Turn(role="user", content="hi"))
    store.reset(s.id)
    assert store.get_or_create(s.id).turns == []


def test_transcript_labels_speakers_readably():
    s = Session(id="x", turns=[
        Turn(role="user", content="2 BHK ka rate?"),
        Turn(role="model", content="Rs 1.35 crore onwards, sir."),
    ])
    assert s.transcript() == (
        "Customer: 2 BHK ka rate?\nPriya: Rs 1.35 crore onwards, sir."
    )


def test_get_returns_none_for_an_unknown_id_without_creating_it():
    store = InMemoryStore()
    assert store.get("nope") is None
    assert store.get("nope") is None


def test_booking_records_keep_the_outcome_structured():
    """A 'FAILED:' string prefix is one typo away from reading as a success."""
    ok = BookingRecord(ok=True, date="2026-09-12", time_slot="11:00-12:00", reference="NS-1")
    bad = BookingRecord(ok=False, date="2026-09-13", time_slot="11:00-12:00")
    assert ok.when() == "2026-09-12 11:00-12:00"
    assert bad.reference is None
    assert [b.ok for b in (ok, bad)] == [True, False]
