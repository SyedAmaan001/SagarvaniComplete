import main


def chat(client, text, cid, **extra):
    r = client.post("/api/orca/chat", json={"query": text, "session_id": cid, **extra})
    assert r.status_code == 200, r.text
    return r.json()


def test_response_schema(client, cid, fake_conditions):
    d = chat(client, "Hello Sagarvani.", cid)
    for key in ("request_id", "conversation_id", "user_text", "assistant_text", "intent", "status",
                "uses_mock_data", "data_sources", "errors"):
        assert key in d, key
    assert d["conversation_id"] == cid and d["user_text"] == "Hello Sagarvani."


def test_session_id_generated_when_missing(client, fake_conditions):
    d = client.post("/api/orca/chat", json={"query": "hello"}).json()
    assert d["conversation_id"].startswith("conv_")


def test_greeting(client, cid):
    d = chat(client, "Hello Sagarvani.", cid)
    assert d["intent"] == "greeting"
    assert "I am Sagarvani" in d["assistant_text"] and d["pipeline_result"] is None
    assert "Sagarwani" not in d["assistant_text"]


def test_capabilities(client, cid):
    d = chat(client, "What can you do?", cid)
    assert d["intent"] == "capabilities"
    assert "marine conditions" in d["assistant_text"] and d["pipeline_result"] is None


def test_weather_without_location_asks_for_it(client, cid, fake_conditions):
    d = chat(client, "What is the weather like at a particular location?", cid)
    assert d["intent"] == "weather" and d["status"] == "needs_info"
    assert "location" in d["assistant_text"].lower()
    assert fake_conditions.calls == []          # never queried a guessed location


def test_fishing_without_location_asks_and_gives_no_recommendation(client, cid, fake_conditions):
    d = chat(client, "Should fishermen go to sea today?", cid)
    assert d["intent"] == "fishing_decision" and d["status"] == "needs_info"
    assert "need the location" in d["assistant_text"]
    assert d["pipeline_result"] is None and fake_conditions.calls == []


def test_different_intents_give_different_answers(client, cid, fake_conditions):
    answers = {
        chat(client, "Hello", cid)["assistant_text"],
        chat(client, "What can you do?", cid)["assistant_text"],
        chat(client, "What is the weather at Malpe?", cid)["assistant_text"],
        chat(client, "What are the wave conditions near Karwar?", cid)["assistant_text"],
        chat(client, "Thanks!", cid)["assistant_text"],
        chat(client, "Is there a cyclone warning near Chennai?", cid)["assistant_text"],
    }
    assert len(answers) == 6


def test_weather_with_location_uses_live_provider_and_labels_source(client, cid, fake_conditions):
    d = chat(client, "What is the weather at Malpe?", cid)
    assert d["intent"] == "weather" and d["status"] == "ok"
    assert "29.5" in d["assistant_text"] and "Malpe" in d["assistant_text"]
    assert "model forecast" in d["assistant_text"]
    assert d["uses_mock_data"] is False
    assert d["data_sources"][0]["type"] == "live_forecast"
    assert fake_conditions.calls == [(13.35, 74.70)]


def test_sea_conditions_by_coordinates(client, cid, fake_conditions):
    d = chat(client, "wave height at 12.5, 74.8", cid)
    assert d["intent"] == "sea_conditions" and "1.1 m" in d["assistant_text"]
    assert fake_conditions.calls == [(12.5, 74.8)]


def test_context_retention_and_followup_location(client, cid, fake_conditions):
    chat(client, "What is the weather at Malpe?", cid)
    d = chat(client, "What about Mangalore?", cid)           # same intent, new place
    assert d["intent"] == "weather" and "Mangalore" in d["assistant_text"]
    d = chat(client, "And the waves?", cid)                   # remembers Mangalore
    assert d["intent"] == "sea_conditions" and "Mangalore" in d["assistant_text"]
    assert fake_conditions.calls[-1] == (12.87, 74.84)


def test_pending_question_is_resolved_by_location_only_reply(client, cid, fake_conditions):
    d = chat(client, "What's the weather?", cid)
    assert d["status"] == "needs_info"
    d = chat(client, "Karwar", cid)
    assert d["intent"] == "weather" and d["status"] == "ok" and "Karwar" in d["assistant_text"]


def test_conversations_are_isolated(client, fake_conditions):
    chat(client, "Weather at Malpe?", "conv_a")
    d = chat(client, "What is the weather?", "conv_b")
    assert d["status"] == "needs_info"


def test_unknown_place_is_not_guessed(client, cid, fake_conditions):
    d = chat(client, "What is the weather in Paris?", cid)
    assert d["status"] == "needs_info" and "Paris" in d["assistant_text"]
    assert fake_conditions.calls == []


def test_fallback_for_unsupported_question(client, cid):
    d = chat(client, "Write me a poem about pizza", cid)
    assert d["intent"] == "unknown" and "not sure" in d["assistant_text"]


def test_explain_followup(client, cid, fake_conditions):
    assert chat(client, "Why?", cid)["status"] == "needs_info"      # nothing to explain yet
    chat(client, "What is the weather at Malpe?", cid)
    d = chat(client, "Why?", cid)
    assert d["intent"] == "explain" and "Open-Meteo" in d["assistant_text"]


def test_hazard_never_claims_verified_alert_status(client, cid, fake_conditions):
    d = chat(client, "Is there a cyclone near Chennai?", cid)
    assert d["intent"] == "hazard"
    assert "can't confirm" in d["assistant_text"] and "IMD" in d["assistant_text"]
    assert "no cyclone" not in d["assistant_text"].lower()


# ── live data failure: never invent conditions ────────────────────────────────

def test_weather_provider_failure_is_reported_not_faked(client, cid, monkeypatch):
    from tests.conftest import FakeConditions
    monkeypatch.setattr(main.conversation_engine, "conditions", FakeConditions(ok=False))
    d = chat(client, "What is the weather at Malpe?", cid)
    assert d["status"] == "degraded" and "couldn't retrieve" in d["assistant_text"]
    assert d["errors"] and d["errors"][0]["code"] == "weather_unavailable"
    assert "29" not in d["assistant_text"]


def test_missing_wave_value_is_not_reported_as_calm(client, cid, monkeypatch):
    from tests.conftest import FakeConditions
    monkeypatch.setattr(main.conversation_engine, "conditions", FakeConditions(wave=None))
    d = chat(client, "wave height at Malpe", cid)
    assert d["status"] == "degraded" and "0 m" not in d["assistant_text"]


# ── safety decision through the real ORCA pipeline ────────────────────────────

def test_fishing_decision_runs_pipeline_when_location_known(client, cid, patch_gateway):
    chat(client, "Should fishermen go to sea today?", cid)           # asks for location
    d = chat(client, "Malpe", cid)                                    # location arrives -> pipeline
    assert d["intent"] == "fishing_decision"
    assert d["pipeline_result"]["execution_status"] == "SUCCESS"
    text = d["assistant_text"]
    assert "model forecast" in text and "IMD/INCOIS" in text
    assert d["uses_mock_data"] is True and d["mock_components"]       # static PFZ data is disclosed
    assert any(s["type"] == "static_reference" for s in d["data_sources"])
    assert d["confidence"] == 0.6


def test_fishing_decision_avoid_when_waves_too_high(client, cid, patch_gateway):
    patch_gateway(wave=3.2, wind=20.0)
    d = chat(client, "Is it safe to go fishing from Malpe in my 6 m canoe?", cid)
    assert d["pipeline_result"]["decision_package"]["verdict"] == "AVOID"
    assert "Not recommended" in d["assistant_text"] and "Stay ashore" in d["assistant_text"]


def test_fishing_decision_refuses_when_live_data_missing(client, cid, patch_gateway):
    patch_gateway(marine_error="Marine API request failed: timeout")
    d = chat(client, "Should fishermen go to sea from Malpe today?", cid)
    pkg = d["pipeline_result"]["decision_package"]
    assert pkg["verdict"] == "REASSESS" and pkg["safety_score"] is None and pkg["confidence"] == 0.0
    assert d["status"] == "degraded"
    assert "can't assess" in d["assistant_text"]
    assert "workable" not in d["assistant_text"] and "GO" not in d["assistant_text"].split()
    assert d["errors"][0]["code"] == "live_data_unavailable"


def test_mock_data_mode_labels_data_and_gives_no_recommendation(client, cid, monkeypatch):
    from services.conversation_engine import MockConditionsProvider
    monkeypatch.setattr(main.settings, "data_mode", "mock")
    monkeypatch.setattr(main.conversation_engine, "conditions", MockConditionsProvider())
    d = chat(client, "What is the weather at Malpe?", cid)
    assert d["uses_mock_data"] is True and "DEMO DATA" in d["assistant_text"]
    d = chat(client, "Should fishermen go to sea from Malpe today?", cid)
    assert d["uses_mock_data"] is True and d["status"] == "degraded"
    assert "cannot give a go/no-go" in d["assistant_text"] and d["pipeline_result"] is None


def test_pipeline_crash_returns_502_not_fake_answer(client, cid, monkeypatch):
    def boom(**k):
        raise RuntimeError("kaboom")
    monkeypatch.setattr(main.orca_pipeline_instance, "run", boom)
    r = client.post("/api/orca/chat", json={"query": "Should I go fishing from Malpe?", "session_id": cid})
    assert r.status_code == 502 and r.json()["code"] == "pipeline_failed"
    assert "kaboom" not in r.text
