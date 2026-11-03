"""
Tests for the live data layer and everything built on it. The HTTP layer is faked with
Open-Meteo-shaped responses, so these check OUR logic (units, fronts, gate, no fabricated
values) - not the real provider.
"""
from datetime import datetime, timedelta, timezone

import pytest

from processors import live_data
from gateway.marine_data_gateway import MarineDataGateway, VESSEL_PROFILES
from engine.evidence_engine import compute_confidence
from engine.safety_gate import HardSafetyGate
from engine.orca_pipeline import OrcaPipeline
from engine.live_map import build_live_map

MALPE = (13.35, 74.70)   # a land cell in the fake grid, like a real harbour


# ── live_data ────────────────────────────────────────────────────────────────

def test_current_speed_converted_from_kmh_to_ms(fake_api):
    fake_api.current_kmh = 7.2
    snap = live_data.get_snapshot(*MALPE, 40)
    p, _ = live_data.nearest_ocean_point(snap, *MALPE)
    assert p["current_ms"] == pytest.approx(2.0, abs=0.01)


def test_land_cells_are_not_ocean_and_coastal_point_snaps_to_nearest_ocean(fake_api):
    snap = live_data.get_snapshot(*MALPE, 40)
    assert any(not p["is_ocean"] for p in snap["points"])
    p, dist = live_data.nearest_ocean_point(snap, *MALPE)
    assert p["is_ocean"] and p["lon"] <= 74.65 and dist < 30


def test_snapshot_is_cached(fake_api):
    live_data.get_snapshot(*MALPE, 40)
    n = fake_api.calls
    live_data.get_snapshot(*MALPE, 40)
    assert fake_api.calls == n


def test_failed_fetch_yields_no_fabricated_points(fake_api):
    fake_api.fail = True
    snap = live_data.get_snapshot(*MALPE, 40)
    assert snap["ocean_point_count"] == 0 and snap["errors"]
    assert all(p["wave_height_m"] is None for p in snap["points"])


def test_front_detected_where_sst_steps_and_none_when_flat(fake_api):
    fake_api.sst = lambda lat, lon: 27.0 if lon < 74.3 else 29.0   # 2 C step across ~0.1 deg
    snap = live_data.get_snapshot(*MALPE, 60)
    fronts = live_data.detect_sst_fronts(snap["points"])
    assert fronts and all(abs(f["lon"] - 74.3) < 0.25 for f in fronts)
    assert fronts[0]["chlorophyll_mg_m3"] is None and fronts[0]["score_basis"] == "SST_FRONT_STRENGTH"

    live_data.clear_cache()
    fake_api.sst = lambda lat, lon: 28.0
    assert live_data.detect_sst_fronts(live_data.get_snapshot(*MALPE, 60)["points"]) == []


def test_safe_windows_respects_limits():
    base = datetime(2026, 11, 3, 0, tzinfo=timezone.utc)
    hours = [{"time_utc": (base + timedelta(hours=i)).isoformat(),
              "wave_height_m": 2.5 if i in (3, 4) else 1.0, "wind_kmh": 10.0} for i in range(8)]
    wins = live_data.safe_windows(hours, 1.8, 35.0)
    assert [w["hours"] for w in wins] == [3, 3]      # hours 0-2 and 5-7; the rough hours split them


# ── gateway ──────────────────────────────────────────────────────────────────

def test_gateway_reports_missing_data_instead_of_defaults(fake_api):
    fake_api.fail = True
    rec = MarineDataGateway().fetch_normalized_marine_record(*MALPE)
    assert rec["normalized_records"] == []
    assert set(rec["critical_missing"]) == {"SIGNIFICANT_WAVE_HEIGHT", "WIND_SPEED_10M"}


def test_gateway_never_invents_chlorophyll_or_lightning(fake_api):
    rec = MarineDataGateway().fetch_normalized_marine_record(*MALPE)
    params = {r["parameter"] for r in rec["normalized_records"]}
    assert "CHLOROPHYLL_A_CONCENTRATION" not in params and "LIGHTNING_FLASH_DENSITY" not in params
    assert rec["data_location"]["distance_from_query_km"] > 0
    assert all(r["valid_time"] for r in rec["normalized_records"])


# ── evidence ─────────────────────────────────────────────────────────────────

def test_confidence_drops_as_data_ages(fake_api):
    gw = MarineDataGateway()
    fresh = compute_confidence(gw.fetch_normalized_marine_record(*MALPE))
    live_data.clear_cache()
    old = (datetime.now(timezone.utc) - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M")
    fake_api.marine_time = old
    stale = compute_confidence(gw.fetch_normalized_marine_record(*MALPE))
    assert 0 < stale < fresh <= 0.95


# ── safety gate ──────────────────────────────────────────────────────────────

def test_gate_uses_local_zone_conditions_and_vessel_range():
    gate = HardSafetyGate()
    zones = [
        {"pfz_id": "calm", "lat": 13.0, "lon": 74.0, "distance_from_user_km": 10, "wave_height_m": 0.8, "wind_kmh": 10},
        {"pfz_id": "rough", "lat": 13.1, "lon": 74.0, "distance_from_user_km": 10, "wave_height_m": 2.6, "wind_kmh": 10},
        {"pfz_id": "far", "lat": 13.2, "lon": 74.0, "distance_from_user_km": 60, "wave_height_m": 0.8, "wind_kmh": 10},
    ]
    safe, rejected = gate.filter_candidate_pfzs(zones, "motorized_craft", wave_height_m=0.5, wind_speed_kmh=10)
    assert [z["pfz_id"] for z in safe] == ["calm"]
    rules = {z["pfz_id"]: z["safety_gate_evaluation"]["fatal_violations"][0]["rule"] for z in rejected}
    assert rules == {"rough": "VESSEL_WAVE_EXCEEDANCE", "far": "VESSEL_RANGE_EXCEEDANCE"}


# ── pipeline ─────────────────────────────────────────────────────────────────

def _frontal_sea(fake_api):
    # front ~20 km west of the harbour: inside a motorised craft's 35 km range
    fake_api.sst = lambda lat, lon: 27.0 if lon < 74.5 else 29.0


def test_pipeline_go_in_calm_water_with_computed_values(fake_api):
    _frontal_sea(fake_api)
    res = OrcaPipeline().run(*MALPE, vessel_type="motorized_craft", language="en", max_range_km=50)
    dp = res["decision_package"]
    assert res["execution_status"] == "SUCCESS" and dp["verdict"] == "GO"
    assert dp["conditions"]["wave_m"] == 1.0 and dp["conditions"]["wind_kmh"] == 15.0
    assert dp["confidence"] != 0.91 and 0 < dp["confidence"] <= 0.95
    assert dp["best_window"] != "05:30 AM – 09:30 AM IST (Optimal Morning Ebb Tide)"
    assert res["data_status"]["live"] and "CHLOROPHYLL_A_CONCENTRATION" in res["data_status"]["not_connected"]
    assert "Netrani" not in res["multilingual_advisory"]["english"]        # no route near it, so no claim
    assert all(z["chlorophyll_mg_m3"] is None for z in res["safe_ranked_pfzs"])


def test_pipeline_avoid_when_waves_exceed_limit_and_advisory_does_not_say_safe(fake_api):
    _frontal_sea(fake_api)
    fake_api.wave = 2.4
    res = OrcaPipeline().run(*MALPE, vessel_type="motorized_craft", language="en")
    dp = res["decision_package"]
    assert dp["verdict"] == "AVOID" and dp["safety_score"] <= 39
    assert "Safe for" not in res["multilingual_advisory"]["english"]


def test_pipeline_refuses_to_decide_without_live_data(fake_api):
    fake_api.fail = True
    res = OrcaPipeline().run(*MALPE, vessel_type="motorized_craft", language="en")
    dp = res["decision_package"]
    assert res["execution_status"] == "DATA_UNAVAILABLE"
    assert dp["verdict"] == "REASSESS" and dp["safety_score"] == 0 and dp["confidence"] == 0.0


def test_wind_limit_depends_on_vessel(fake_api):
    _frontal_sea(fake_api)
    fake_api.wind_kmh = 30.0
    canoe = OrcaPipeline().run(*MALPE, vessel_type="artisanal_canoe", language="en")["decision_package"]["verdict"]
    live_data.clear_cache()
    motor = OrcaPipeline().run(*MALPE, vessel_type="motorized_craft", language="en")["decision_package"]["verdict"]
    assert VESSEL_PROFILES["artisanal_canoe"]["max_safe_wind_speed_kmh"] == 25.0
    assert canoe == "AVOID" and motor == "GO"


# ── live map ─────────────────────────────────────────────────────────────────

def test_live_map_layers_and_honesty(fake_api):
    _frontal_sea(fake_api)
    fake_api.wave = 2.0
    m = build_live_map(*MALPE, 50)
    assert m["live"] and m["data_age_minutes"] is not None and m["data_age_minutes"] < 30
    assert m["layers"]["waves"]["features"] and m["layers"]["currents"]["features"]
    assert m["layers"]["wave_warnings"]["features"]                      # 2.0 m > 1.8 m motorised limit
    assert m["layers"]["pfz"]["features"] and m["layers"]["restricted"]["features"]
    assert {n["layer"] for n in m["not_connected"]} >= {"Cyclone"}


def test_live_map_when_provider_down(fake_api):
    fake_api.fail = True
    m = build_live_map(*MALPE, 50)
    assert m["live"] is False and m["layers"]["waves"]["features"] == [] and m["errors"]


def test_api_route_if_fastapi_available(fake_api):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    import main
    r = TestClient(main.app).get("/api/live/map?lat=13.35&lon=74.7&radius_km=50")
    assert r.status_code == 200 and "layers" in r.json()
