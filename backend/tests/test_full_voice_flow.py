"""End-to-end mock voice flow: audio -> STT -> chat -> TTS, as the frontend performs it."""

from tests.conftest import WEBM


def test_full_mock_voice_conversation(client, fake_conditions):
    # 1. user speaks -> STT (mock provider, clearly labelled)
    stt = client.post("/api/orca/stt", files={"file": ("rec.webm", WEBM, "audio/webm")}).json()
    assert stt["is_mock"] is True and stt["text"]

    # 2. recognised text -> ORCA chat (same conversation across turns)
    cid = "e2e_conv"
    first = client.post("/api/orca/chat", json={"query": stt["text"], "session_id": cid}).json()
    assert first["user_text"] == stt["text"] and first["assistant_text"] and first["status"] in ("ok", "needs_info", "degraded")

    # 3. a typed follow-up in the same conversation keeps context
    client.post("/api/orca/chat", json={"query": "What is the weather at Malpe?", "session_id": cid})
    follow = client.post("/api/orca/chat", json={"query": "And the waves?", "session_id": cid}).json()
    assert follow["intent"] == "sea_conditions" and "Malpe" in follow["assistant_text"]

    # 4. answer -> TTS (no provider key => explicit browser-speech fallback)
    tts = client.post("/api/orca/tts", json={"text": follow["assistant_text"], "language": "en"}).json()
    assert tts["mode"] == "browser" and tts["chunks"] and tts["is_provider_audio"] is False


def test_voice_flow_survives_provider_outage_end_to_end(client, fake_conditions, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    monkeypatch.setattr("agents.interpreter_agent.transcribe_and_translate_audio", lambda *a: (None, {"status": "failed: 500"}))
    from services import tts_service
    monkeypatch.setattr(tts_service.requests, "post", lambda *a, **k: (_ for _ in ()).throw(ConnectionError("down")))

    stt = client.post("/api/orca/stt", files={"file": ("rec.webm", WEBM, "audio/webm")}).json()
    assert stt["status"] == "fallback_to_mock" and stt["is_mock"]
    chat = client.post("/api/orca/chat", json={"query": stt["text"]}).json()
    tts = client.post("/api/orca/tts", json={"text": chat["assistant_text"]}).json()
    assert tts["mode"] == "browser" and tts["warning"]
