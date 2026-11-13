"""Shared fixtures. Tests never hit the network or need API keys: weather/marine
providers, the data gateway and STT/TTS providers are replaced with fakes."""

import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Keep real keys out of tests regardless of the developer's .env
for _k in list(os.environ):
    if _k.startswith(("SARVAM_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")):
        os.environ.pop(_k)

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from services.conversation_engine import Conditions  # noqa: E402


class FakeConditions:
    """Deterministic stand-in for the Open-Meteo provider."""

    def __init__(self, ok=True, wave=1.1, wind=14.0, weather_error=None, marine_error=None):
        self.ok, self.wave, self.wind = ok, wave, wind
        self.weather_error, self.marine_error = weather_error, marine_error
        self.calls = []

    def current(self, lat, lon):
        self.calls.append((lat, lon))
        if not self.ok:
            return Conditions(ok=False, weather_error="boom", marine_error="boom", fetched_at="T")
        return Conditions(
            ok=True,
            weather={"temperature_c": 29.5, "wind_speed_kmh": self.wind, "wind_gusts_kmh": 20.0,
                     "precipitation_mm": 0.0, "weather_description": "Partly cloudy"},
            marine={"wave_height_m": self.wave, "wave_period_s": 8.0, "swell_wave_height_m": 0.7,
                    "sea_state": "Slight", "ocean_current_velocity_ms": 0.3},
            weather_error=self.weather_error, marine_error=self.marine_error,
            fetched_at="2026-11-12T10:00:00+00:00",
        )


def fake_forecast(wave=1.0, wind=15.0, marine_error=None, weather_error=None):
    def _f(lat, lon):
        return {
            "lat": lat, "lon": lon,
            "weather": {"wind_speed_kmh": None if weather_error else wind},
            "marine": {"wave_height_m": None if marine_error else wave},
            "weather_error": weather_error, "marine_error": marine_error,
            "fetched_at": "2026-11-12T10:00:00+00:00",
        }
    return _f


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def cid():
    return "test_" + uuid.uuid4().hex[:8]


@pytest.fixture
def fake_conditions(monkeypatch):
    fake = FakeConditions()
    monkeypatch.setattr(main.conversation_engine, "conditions", fake)
    return fake


@pytest.fixture
def patch_gateway(monkeypatch):
    """Control what the pipeline's gateway sees (live / failing wave+wind)."""
    import gateway.marine_data_gateway as gw

    def apply(**kw):
        monkeypatch.setattr(gw, "get_combined_forecast", fake_forecast(**kw))
        monkeypatch.setattr(gw, "get_point_ocean_current", lambda lat, lon: {"speed_ms": 0.3})
        monkeypatch.setattr(gw, "get_latest_coastal_pass", lambda: {})

    apply()
    return apply


@pytest.fixture(autouse=True)
def _restore_settings(monkeypatch):
    """Every test starts with default voice/data modes and no provider keys
    (importing main loads backend/.env, so keys must be cleared per test)."""
    for k in list(os.environ):
        if k.startswith(("SARVAM_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "STT_MODE", "TTS_MODE", "DATA_MODE", "CORS_ORIGINS", "REDIS_URL")):
            monkeypatch.delenv(k)
    for attr, val in (("stt_mode", "auto"), ("tts_mode", "auto"), ("data_mode", "live"), ("stt_fallback_to_mock", True)):
        monkeypatch.setattr(main.settings, attr, val)
    yield


WEBM = b"\x1aE\xdf\xa3" + bytes(range(256)) * 8   # >256 bytes, webm magic header
