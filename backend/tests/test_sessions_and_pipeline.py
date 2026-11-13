import pytest

from gateway.marine_data_gateway import MarineDataGateway
from services.session_store import SessionStore
import gateway.marine_data_gateway as gw
from tests.conftest import fake_forecast


# ── session store / Redis ─────────────────────────────────────────────────────

def test_memory_store_roundtrip_and_ttl(monkeypatch):
    s = SessionStore(ttl_seconds=60)
    assert s.backend == "memory" and s.get("x") is None
    s.save("x", {"a": 1})
    assert s.get("x") == {"a": 1}
    s.delete("x")
    assert s.get("x") is None
    s.save("y", {"a": 1})
    monkeypatch.setattr("services.session_store.time.time", lambda: 10**10)
    assert s.get("y") is None                              # expired


def test_redis_unavailable_falls_back_to_memory():
    s = SessionStore(redis_url="redis://127.0.0.1:1/0")    # nothing listens on port 1
    assert s.backend == "memory" and s.last_error
    s.save("c", {"ok": True})
    assert s.get("c") == {"ok": True}


def test_redis_runtime_failure_degrades_without_losing_service():
    class Flaky:
        def __init__(self): self.fail = False; self.d = {}
        def get(self, k):
            if self.fail: raise ConnectionError("redis died")
            return self.d.get(k)
        def set(self, k, v, ex=None):
            if self.fail: raise ConnectionError("redis died")
            self.d[k] = v
        def delete(self, k): self.d.pop(k, None)

    flaky = Flaky()
    s = SessionStore(redis_client=flaky)
    assert s.backend == "redis"
    s.save("c", {"n": 1})
    assert s.get("c") == {"n": 1}
    flaky.fail = True
    s.save("c", {"n": 2})                                  # must not raise
    assert s.backend == "memory" and "ConnectionError" in s.last_error
    assert s.get("c") == {"n": 2}


def test_chat_works_when_redis_is_down(client, monkeypatch, fake_conditions):
    import main
    monkeypatch.setattr(main.conversation_engine, "store", SessionStore(redis_url="redis://127.0.0.1:1/0"))
    r = client.post("/api/orca/chat", json={"query": "Weather at Malpe?", "session_id": "r1"})
    assert r.status_code == 200 and r.json()["status"] == "ok"


# ── gateway / pipeline honesty ────────────────────────────────────────────────

@pytest.fixture
def gateway(monkeypatch):
    monkeypatch.setattr(gw, "get_point_ocean_current", lambda a, b: {"speed_ms": 0.3})
    monkeypatch.setattr(gw, "get_latest_coastal_pass", lambda: {})
    return MarineDataGateway()


def _records(rec):
    return {r["parameter"]: r for r in rec["normalized_records"]}


def test_gateway_live_values_pass_through(gateway, monkeypatch):
    monkeypatch.setattr(gw, "get_combined_forecast", fake_forecast(wave=1.7, wind=21.0))
    rec = gateway.fetch_normalized_marine_record(13.35, 74.7)
    r = _records(rec)
    assert r["SIGNIFICANT_WAVE_HEIGHT"]["value"] == 1.7 and r["WIND_SPEED_10M"]["value"] == 21.0
    assert rec["data_integrity"]["conditions_live"] is True


def test_gateway_never_invents_values_when_feed_fails(gateway, monkeypatch):
    monkeypatch.setattr(gw, "get_combined_forecast", fake_forecast(marine_error="timeout", weather_error="timeout"))
    rec = gateway.fetch_normalized_marine_record(13.35, 74.7)
    r = _records(rec)
    assert r["SIGNIFICANT_WAVE_HEIGHT"]["value"] is None and r["WIND_SPEED_10M"]["value"] is None
    assert r["SIGNIFICANT_WAVE_HEIGHT"]["quality"] == "UNAVAILABLE"
    assert rec["data_integrity"]["conditions_live"] is False


def test_gateway_labels_static_parameters_as_not_live(gateway, monkeypatch):
    monkeypatch.setattr(gw, "get_combined_forecast", fake_forecast())
    rec = gateway.fetch_normalized_marine_record(13.35, 74.7)
    r = _records(rec)
    for p in rec["data_integrity"]["static_parameters"]:
        assert r[p]["mode"] == "STATIC_REFERENCE" and r[p]["quality"] == "NOT_LIVE"
    assert rec["data_integrity"]["uses_mock_data"] is True


def test_pipeline_fails_closed_without_live_data(monkeypatch, patch_gateway):
    from engine.orca_pipeline import OrcaPipeline
    patch_gateway(weather_error="down")
    out = OrcaPipeline().run(lat=13.35, lon=74.7, vessel_type="motorized_craft", language="en")
    pkg = out["decision_package"]
    assert pkg["verdict"] == "REASSESS" and pkg["safety_score"] is None
    assert out["hard_safety_gate"]["is_safe"] is False
    assert out["situation_metrics"]["marine_safety"] == "UNKNOWN"
    assert "safe" not in out["multilingual_advisory"]["english"].lower().replace("cannot judge whether it is safe", "")
    assert not out["safe_ranked_pfzs"]


def test_pipeline_evidence_does_not_fabricate_freshness(patch_gateway):
    from engine.orca_pipeline import OrcaPipeline
    out = OrcaPipeline().run(lat=13.35, lon=74.7, vessel_type="motorized_craft", language="en")
    ev = out["evidence_trail"]["evidence_trail"]
    assert not any("FRESH (Age" in e["status"] for e in ev)
    assert any("STATIC" in e["status"] for e in ev)
    assert out["evidence_trail"]["provenance_summary"]["uses_static_reference_data"] is True


def test_open_meteo_wind_unit_is_requested_in_ms(monkeypatch):
    """Regression: wind was multiplied by 3.6 although Open-Meteo already returns km/h."""
    from processors import weather_processor as wp
    captured = {}

    class R:
        def raise_for_status(self): pass
        def json(self): return {"current": {"wind_speed_10m": 10.0}, "hourly": {}}

    def fake_get(url, params=None, timeout=None):
        captured.update(params)
        return R()

    monkeypatch.setattr(wp.requests, "get", fake_get)
    out = wp.get_weather_forecast(13.35, 74.7)
    assert captured["wind_speed_unit"] == "ms" and out["current"]["wind_speed_kmh"] == 36.0
