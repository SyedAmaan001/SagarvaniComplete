import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# utils/key_rotation.py raises at import time without a Gemini key. A dummy is enough here:
# no test calls Gemini (the google SDK isn't even needed).
os.environ.setdefault("GEMINI_API_KEY_1", "test-key-not-real")

from processors import live_data  # noqa: E402


class FakeOpenMeteo:
    """
    Stands in for the Open-Meteo HTTP API with responses shaped like the documented ones
    (a list of location objects when several coordinates are requested).
    Land = longitude > 74.65 (no marine data there, like a real land cell).
    """

    def __init__(self):
        self.wave = 1.0
        self.wind_kmh = 15.0
        self.current_kmh = 3.6          # Open-Meteo marine default unit is km/h
        self.sst = lambda lat, lon: 28.0
        self.fail = False
        self.marine_time = None         # override valid time, naive GMT string
        self.calls = 0

    def _now(self):
        n = datetime.now(timezone.utc)
        return n.replace(minute=(n.minute // 15) * 15, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")

    @staticmethod
    def _coords(v):
        return [float(x) for x in str(v).split(",")]

    def __call__(self, url, params):
        self.calls += 1
        if self.fail:
            raise RuntimeError("network down")
        lats, lons = self._coords(params["latitude"]), self._coords(params["longitude"])
        marine = "marine" in url
        out = []
        for lat, lon in zip(lats, lons):
            if "hourly" in params:
                hours = [f"{datetime.now(timezone.utc):%Y-%m-%d}T{h:02d}:00" for h in range(24)]
                hours += [f"{(datetime.now(timezone.utc).replace(day=28)):%Y-%m-%d}T{h:02d}:00" for h in range(24)]
                if marine:
                    out.append({"hourly": {"time": hours, "wave_height": [self.wave] * len(hours)}})
                else:
                    out.append({"hourly": {"time": hours, "wind_speed_10m": [self.wind_kmh] * len(hours)},
                                "hourly_units": {"wind_speed_10m": "km/h"}})
            elif marine:
                land = lon > 74.65
                t = self.marine_time or self._now()
                out.append({
                    "current_units": {"ocean_current_velocity": "km/h"},
                    "current": {
                        "time": t,
                        "wave_height": None if land else self.wave,
                        "wave_period": None if land else 7.0,
                        "wave_direction": None if land else 250.0,
                        "swell_wave_height": None if land else 0.6,
                        "sea_surface_temperature": None if land else self.sst(lat, lon),
                        "ocean_current_velocity": None if land else self.current_kmh,
                        "ocean_current_direction": None if land else 180.0,
                        "sea_level_height_msl": None if land else 0.4,
                    },
                })
            else:
                out.append({
                    "current_units": {"wind_speed_10m": "km/h", "wind_gusts_10m": "km/h"},
                    "current": {"time": self._now(), "wind_speed_10m": self.wind_kmh,
                                "wind_gusts_10m": self.wind_kmh * 1.3, "wind_direction_10m": 270},
                })
        return out if len(out) > 1 or "latitude" in params and "," in str(params["latitude"]) else out[0]


@pytest.fixture
def fake_api(monkeypatch):
    live_data.clear_cache()
    api = FakeOpenMeteo()
    monkeypatch.setattr(live_data, "_http_get_json", api)
    yield api
    live_data.clear_cache()
