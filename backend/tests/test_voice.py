import base64

import main
from services import tts_service
from tests.conftest import WEBM


def stt(client, data=WEBM, name="rec.webm", ctype="audio/webm;codecs=opus"):
    return client.post("/api/orca/stt", files={"file": (name, data, ctype)})


# ── STT ───────────────────────────────────────────────────────────────────────

def test_stt_mock_mode_is_labelled_and_deterministic(client):
    a, b = stt(client).json(), stt(client).json()
    assert a["mode"] == "mock" and a["is_mock"] is True and a["provider"] == "mock"
    assert "NOT what you said" in a["warning"]
    assert a["text"] == b["text"] and a["text"]
    assert a["bytes_received"] == len(WEBM)


def test_stt_real_mode_uses_provider(client, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    seen = {}

    def fake(data, filename, content_type):
        seen["ct"] = content_type
        return "what is the wave height near malpe", {"model": "saaras:v3", "status": "success"}

    monkeypatch.setattr("agents.interpreter_agent.transcribe_and_translate_audio", fake)
    d = stt(client).json()
    assert d["mode"] == "real" and d["is_mock"] is False and d["warning"] is None
    assert d["text"] == "what is the wave height near malpe" and d["provider"].startswith("sarvam")
    assert seen["ct"] == "audio/webm"                    # real browser type is forwarded, not forced to wav


def test_stt_provider_failure_falls_back_to_labelled_mock(client, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    monkeypatch.setattr("agents.interpreter_agent.transcribe_and_translate_audio",
                        lambda *a: (None, {"status": "failed: 503"}))
    d = stt(client).json()
    assert d["mode"] == "mock" and d["status"] == "fallback_to_mock"
    assert "failed" in d["warning"] and "DEMO" in d["warning"]


def test_stt_provider_failure_without_fallback_is_502(client, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    monkeypatch.setattr(main.settings, "stt_fallback_to_mock", False)
    monkeypatch.setattr("agents.interpreter_agent.transcribe_and_translate_audio",
                        lambda *a: (None, {"status": "failed: 503"}))
    r = stt(client)
    assert r.status_code == 502 and r.json()["code"] == "stt_failed"


def test_stt_rejects_empty_short_large_and_wrong_type(client, monkeypatch):
    assert stt(client, b"").status_code == 422
    assert stt(client, b"x" * 10).json()["code"] == "audio_too_short"
    r = stt(client, WEBM, "x.txt", "text/plain")
    assert r.status_code == 415 and r.json()["code"] == "unsupported_audio_type"
    monkeypatch.setattr(main.settings, "max_audio_bytes", 1000)
    r = stt(client, b"x" * 2000)
    assert r.status_code == 413 and r.json()["code"] == "audio_too_large"


def test_stt_octet_stream_allowed_only_with_audio_extension(client):
    assert stt(client, WEBM, "a.webm", "application/octet-stream").status_code == 200
    assert stt(client, WEBM, "a.exe", "application/octet-stream").status_code == 415


def test_stt_missing_file_field(client):
    r = client.post("/api/orca/stt")
    assert r.status_code == 422


# ── TTS ───────────────────────────────────────────────────────────────────────

def test_tts_browser_mode_without_key(client):
    d = client.post("/api/orca/tts", json={"text": "Hello! I am Sagarvani.", "language": "en"}).json()
    assert d["mode"] == "browser" and d["is_provider_audio"] is False
    assert d["chunks"] == ["Hello! I am Sagarvani."] and d["audio_base64"] == []


def test_tts_long_text_is_chunked_on_sentences(client):
    text = " ".join(f"This is sentence number {i} about sea conditions." for i in range(40))
    d = client.post("/api/orca/tts", json={"text": text}).json()
    assert len(d["chunks"]) > 1 and all(len(c) <= tts_service.MAX_CHUNK_CHARS for c in d["chunks"])
    assert " ".join(d["chunks"]).count("sentence number") == 40


def test_tts_strips_markdown_and_emoji():
    assert tts_service.clean_for_speech("**Warning** 🚨 • stay ashore") == "Warning stay ashore"


def test_tts_provider_mode_returns_audio(client, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    audio = base64.b64encode(b"RIFFfake").decode()

    class R:
        def raise_for_status(self): pass
        def json(self): return {"audios": [audio]}

    monkeypatch.setattr(tts_service.requests, "post", lambda *a, **k: R())
    d = client.post("/api/orca/tts", json={"text": "Hello there.", "language": "hi"}).json()
    assert d["mode"] == "provider" and d["is_provider_audio"] is True
    assert d["audio_base64"] == [audio] and d["mime_type"] == "audio/wav"


def test_tts_provider_failure_falls_back_to_browser(client, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")

    def down(*a, **k):
        raise ConnectionError("provider down")

    monkeypatch.setattr(tts_service.requests, "post", down)
    d = client.post("/api/orca/tts", json={"text": "Hello there."}).json()
    assert d["mode"] == "browser" and d["is_provider_audio"] is False
    assert "provider down" in d["warning"]


def test_tts_validation(client, monkeypatch):
    assert client.post("/api/orca/tts", json={"text": "   "}).status_code == 422
    assert client.post("/api/orca/tts", json={"text": "🚨🚨"}).status_code == 422
    assert client.post("/api/orca/tts", json={}).status_code == 422
    monkeypatch.setattr(main.settings, "max_tts_chars", 50)
    assert client.post("/api/orca/tts", json={"text": "a" * 60}).status_code == 413
