def test_chat_creates_session_and_returns_reply(client):
    r = client.post("/api/chat", json={"message": "Hi", "channel": "chat"})
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"]
    assert "echo: Hi" in body["reply"]


def test_chat_remembers_session_across_turns(client):
    first = client.post("/api/chat", json={"message": "Hi", "channel": "chat"}).json()
    sid = first["session_id"]
    client.post("/api/chat", json={"message": "3 BHK", "session_id": sid, "channel": "chat"})
    body = client.post(f"/api/analytics/{sid}").json()
    # two exchanges = four transcript lines
    assert body["summary"] == "turns=4"


def test_channel_is_passed_through_to_the_model(client, fake_llm):
    client.post("/api/chat", json={"message": "Hi", "channel": "voice"})
    assert fake_llm.last_channel == "voice"


def test_channel_defaults_to_chat(client, fake_llm):
    client.post("/api/chat", json={"message": "Hi"})
    assert fake_llm.last_channel == "chat"


def test_invalid_channel_is_rejected(client):
    r = client.post("/api/chat", json={"message": "Hi", "channel": "smoke-signal"})
    assert r.status_code == 422


def test_blank_message_is_rejected(client):
    r = client.post("/api/chat", json={"message": "   ", "channel": "chat"})
    assert r.status_code == 422


def test_reset_clears_history(client):
    sid = client.post("/api/chat", json={"message": "Hi", "channel": "chat"}).json()["session_id"]
    assert client.post(f"/api/analytics/{sid}").json()["summary"] == "turns=2"
    assert client.post(f"/api/reset/{sid}").status_code == 200
    # An emptied session short-circuits to an empty record without spending an
    # API call on a transcript with nothing in it.
    assert client.post(f"/api/analytics/{sid}").json()["summary"] is None


def test_analytics_on_an_unknown_session_returns_an_empty_record(client):
    """Absence is data, not an error — an empty record beats a 404."""
    r = client.post("/api/analytics/never-existed")
    assert r.status_code == 200
    assert r.json()["interest_level"] == "unknown"


def test_index_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Northstar" in r.text
