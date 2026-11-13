import importlib

import main
from utils import config

FRONTEND = "https://sagarvani-frontend-production.up.railway.app"


def test_app_starts_and_modules_load():
    assert main.MODULES_OK, main.MODULES_ERROR
    assert main.conversation_engine is not None


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    assert client.get("/api/health").status_code == 200


def test_ready(client):
    r = client.get("/ready")
    body = r.json()
    assert r.status_code == 200 and body["status"] == "ready"
    assert body["checks"]["sessions"]["backend"] in ("memory", "redis")
    assert body["checks"]["voice"]["stt_mode"] == "mock"      # no key in tests
    assert body["checks"]["voice"]["tts_mode"] == "browser"


def test_ready_reports_503_when_engine_missing(client, monkeypatch):
    monkeypatch.setattr(main, "conversation_engine", None)
    assert client.get("/ready").status_code == 503


def test_status_never_leaks_secrets(client, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "super-secret-sarvam-key")
    monkeypatch.setenv("GEMINI_API_KEY_1", "super-secret-gemini-key")
    r = client.get("/api/status")
    assert r.status_code == 200
    assert "super-secret" not in r.text
    assert r.json()["sarvam_key_configured"] is True


def test_request_id_generated_and_echoed(client):
    r = client.get("/health")
    assert len(r.headers["x-request-id"]) >= 8
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["x-request-id"] == "abc123"


def test_cors_allows_deployed_frontend_and_localhost(client):
    for origin in (FRONTEND, "http://localhost:3000"):
        r = client.options("/api/orca/chat", headers={
            "Origin": origin, "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"})
        assert r.status_code == 200, origin
        assert r.headers["access-control-allow-origin"] == origin


def test_cors_blocks_unknown_origin(client):
    r = client.options("/api/orca/chat", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert r.status_code == 400


def test_cors_env_adds_to_defaults_not_replaces(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://custom.example.com/")
    s = config.load_settings()
    assert "https://custom.example.com" in s.cors_origins
    assert FRONTEND in s.cors_origins and not s.cors_allow_all


def test_cors_wildcard(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")
    assert config.load_settings().cors_allow_all is True


def test_missing_and_invalid_env_variables(monkeypatch):
    for k in ("STT_MODE", "TTS_MODE", "DATA_MODE", "REDIS_URL", "SARVAM_API_KEY", "MAX_AUDIO_BYTES"):
        monkeypatch.delenv(k, raising=False)
    s = config.load_settings()
    assert (s.effective_stt_mode, s.effective_tts_mode, s.data_mode) == ("mock", "browser", "live")
    assert s.redis_url is None and s.warnings == []

    monkeypatch.setenv("STT_MODE", "banana")
    monkeypatch.setenv("MAX_AUDIO_BYTES", "-5")
    monkeypatch.setenv("STT_MODE", "real")
    s = config.load_settings()
    assert any("MAX_AUDIO_BYTES" in w for w in s.warnings)
    assert any("SARVAM_API_KEY" in w for w in s.warnings)     # real STT without a key is flagged
    assert s.max_audio_bytes == 10 * 1024 * 1024               # bad value ignored


def test_provider_modes_follow_key(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    s = config.load_settings()
    assert (s.effective_stt_mode, s.effective_tts_mode) == ("real", "provider")


def test_invalid_requests_get_structured_errors(client):
    r = client.post("/api/orca/chat", json={})
    assert r.status_code == 422 and r.json()["code"] == "validation_error" and r.json()["request_id"]
    r = client.post("/api/orca/chat", json={"query": ""})
    assert r.status_code == 422
    r = client.post("/api/orca/chat", json={"query": "x" * 5000})
    assert r.status_code == 422
    r = client.post("/api/orca/chat", content="not json", headers={"content-type": "application/json"})
    assert r.status_code == 422
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404 and "request_id" in r.json()


def test_unhandled_exception_returns_500_without_traceback(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("secret internal detail")
    monkeypatch.setattr(main.conversation_engine, "respond", boom)
    r = client.post("/api/orca/chat", json={"query": "hello"})
    assert r.status_code == 500
    assert "secret internal detail" not in r.text and r.json()["request_id"]
