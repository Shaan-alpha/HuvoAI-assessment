from app.session import InMemoryStore, Session, Turn


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
