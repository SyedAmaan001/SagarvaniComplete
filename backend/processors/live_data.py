"""
Live marine data layer.

Single place that talks to the live data providers (Open-Meteo Marine + Weather,
free for non-commercial use, no key needed) and turns the responses into plain
dicts the rest of the backend can use.

Design rules
------------
* No invented numbers. If a value cannot be fetched it is ``None`` and the caller
  must treat it as missing (never substitute a "typical" value).
* Every point carries the provider's own ``valid_time`` plus our ``fetched_at`` so
  freshness can be computed instead of assumed.
* Many points are fetched in one batched request per provider and results are
  cached for ``LIVE_DATA_TTL_SECONDS`` (default 10 min) to stay well inside the
  provider's fair-use limits.
* Units are read from the response (``current_units``) and converted, because the
  providers' default units differ between endpoints (km/h vs m/s).
"""

import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

from utils.geo_utils import haversine_km

MARINE_URL = os.getenv("OPEN_METEO_MARINE_URL", "https://marine-api.open-meteo.com/v1/marine")
WEATHER_URL = os.getenv("OPEN_METEO_WEATHER_URL", "https://api.open-meteo.com/v1/forecast")
OPEN_METEO_API_KEY = os.getenv("OPEN_METEO_API_KEY")  # only needed for commercial use

GRID_STEP_DEG = 0.1          # ~11 km; Open-Meteo marine models are ~8 km anyway
MAX_RADIUS_KM = 100.0
CHUNK_SIZE = 40              # locations per request
CACHE_TTL_S = int(os.getenv("LIVE_DATA_TTL_SECONDS", "600"))
FAILURE_TTL_S = 30           # retry failed fetches quickly
MAX_OCEAN_SNAP_KM = 30.0     # how far we look for an ocean cell for a coastal point

MARINE_CURRENT = [
    "wave_height", "wave_direction", "wave_period", "swell_wave_height",
    "sea_surface_temperature", "ocean_current_velocity", "ocean_current_direction",
    "sea_level_height_msl",
]
WEATHER_CURRENT = ["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"]

_cache: Dict[Any, Tuple[float, Any]] = {}
_cache_lock = threading.Lock()


# ─── HTTP + cache ─────────────────────────────────────────────────────────────

def _http_get_json(url: str, params: Dict[str, Any]) -> Any:
    """GET with one retry. Tests replace this function."""
    if OPEN_METEO_API_KEY:
        params = dict(params, apikey=OPEN_METEO_API_KEY)
    last_exc: Optional[Exception] = None
    for attempt in range(2):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # network error, 4xx/5xx, bad JSON
            last_exc = exc
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"{url} failed: {last_exc}")


def _cache_get(key):
    with _cache_lock:
        hit = _cache.get(key)
        if hit and hit[0] > time.time():
            return hit[1]
    return None


def _cache_put(key, value, ttl):
    with _cache_lock:
        _cache[key] = (time.time() + ttl, value)


def clear_cache():
    with _cache_lock:
        _cache.clear()


# ─── Unit helpers ─────────────────────────────────────────────────────────────

def _speed_factor_to_ms(unit: Optional[str]) -> float:
    u = (unit or "").strip().lower()
    if u in ("m/s", "ms"):
        return 1.0
    if u in ("km/h", "kmh"):
        return 1 / 3.6
    if u in ("kn", "kt", "kts"):
        return 0.514444
    if u in ("mp/h", "mph"):
        return 0.44704
    return 1 / 3.6 if not u else 1.0  # unknown unit: assume provider default (km/h)


def _to_ms(value: Optional[float], unit: Optional[str]) -> Optional[float]:
    return None if value is None else round(value * _speed_factor_to_ms(unit), 3)


def _to_kmh(value: Optional[float], unit: Optional[str]) -> Optional[float]:
    return None if value is None else round(value * _speed_factor_to_ms(unit) * 3.6, 1)


def _iso_utc(t: Optional[str]) -> Optional[str]:
    """Open-Meteo returns naive GMT strings like '2026-11-03T01:15'."""
    if not t:
        return None
    try:
        return datetime.fromisoformat(t).replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def _snap(v: float, step: float = GRID_STEP_DEG) -> float:
    return round(round(v / step) * step, 4)


def build_grid(lat: float, lon: float, radius_km: float, step: float = GRID_STEP_DEG) -> List[Tuple[float, float]]:
    c_lat, c_lon = _snap(lat, step), _snap(lon, step)
    n = int(math.ceil((radius_km + step * 111.0) / (111.0 * step)))
    pts = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            p_lat = round(c_lat + i * step, 4)
            p_lon = round(c_lon + j * step, 4)
            if -90 <= p_lat <= 90 and haversine_km(lat, lon, p_lat, p_lon) <= radius_km + step * 111.0:
                pts.append((p_lat, p_lon))
    return pts


# ─── Fetching ─────────────────────────────────────────────────────────────────

def _as_list(payload: Any) -> List[Dict[str, Any]]:
    return payload if isinstance(payload, list) else [payload]


def _fetch_chunk(points: List[Tuple[float, float]]) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, bool]]:
    lats = ",".join(str(p[0]) for p in points)
    lons = ",".join(str(p[1]) for p in points)
    errors: List[str] = []
    ok = {"marine": True, "weather": True}

    try:
        marine = _as_list(_http_get_json(MARINE_URL, {
            "latitude": lats, "longitude": lons, "current": ",".join(MARINE_CURRENT)}))
    except Exception as exc:
        marine, ok["marine"] = [], False
        errors.append(f"marine: {exc}")
    try:
        weather = _as_list(_http_get_json(WEATHER_URL, {
            "latitude": lats, "longitude": lons, "current": ",".join(WEATHER_CURRENT),
            "wind_speed_unit": "kmh"}))
    except Exception as exc:
        weather, ok["weather"] = [], False
        errors.append(f"weather: {exc}")

    out = []
    for idx, (p_lat, p_lon) in enumerate(points):
        m = marine[idx] if idx < len(marine) else {}
        w = weather[idx] if idx < len(weather) else {}
        mc, mu = (m or {}).get("current") or {}, (m or {}).get("current_units") or {}
        wc, wu = (w or {}).get("current") or {}, (w or {}).get("current_units") or {}
        out.append({
            "lat": p_lat,
            "lon": p_lon,
            "is_ocean": mc.get("wave_height") is not None,
            "wave_height_m": mc.get("wave_height"),
            "wave_period_s": mc.get("wave_period"),
            "wave_direction_deg": mc.get("wave_direction"),
            "swell_height_m": mc.get("swell_wave_height"),
            "sst_c": mc.get("sea_surface_temperature"),
            "current_ms": _to_ms(mc.get("ocean_current_velocity"), mu.get("ocean_current_velocity")),
            "current_dir_deg": mc.get("ocean_current_direction"),
            "sea_level_m": mc.get("sea_level_height_msl"),
            "wind_kmh": _to_kmh(wc.get("wind_speed_10m"), wu.get("wind_speed_10m") or "km/h"),
            "gust_kmh": _to_kmh(wc.get("wind_gusts_10m"), wu.get("wind_gusts_10m") or "km/h"),
            "wind_dir_deg": wc.get("wind_direction_10m"),
            "marine_valid_time": _iso_utc(mc.get("time")),
            "weather_valid_time": _iso_utc(wc.get("time")),
        })
    return out, errors, ok


def get_snapshot(lat: float, lon: float, radius_km: float = 50.0) -> Dict[str, Any]:
    """Live conditions for a grid of points around (lat, lon). Cached."""
    radius = min(max(radius_km, 10.0), MAX_RADIUS_KM)
    key = ("snapshot", _snap(lat), _snap(lon), int(math.ceil(radius / 10.0) * 10))
    cached = _cache_get(key)
    if cached is not None:
        return cached

    grid = build_grid(lat, lon, radius)
    chunks = [grid[i:i + CHUNK_SIZE] for i in range(0, len(grid), CHUNK_SIZE)]
    points: List[Dict[str, Any]] = []
    errors: List[str] = []
    ok_marine = ok_weather = False
    with ThreadPoolExecutor(max_workers=4) as pool:
        for pts, errs, ok in pool.map(_fetch_chunk, chunks):
            points.extend(pts)
            errors.extend(errs)
            ok_marine = ok_marine or ok["marine"]
            ok_weather = ok_weather or ok["weather"]

    ocean = [p for p in points if p["is_ocean"]]
    times = [p["marine_valid_time"] for p in ocean if p["marine_valid_time"]]
    snapshot = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius,
        "grid_step_deg": GRID_STEP_DEG,
        "points": points,
        "ocean_point_count": len(ocean),
        "data_valid_time": max(times) if times else None,
        "sources": [
            {"name": "Open-Meteo Marine API", "role": "waves, sea-surface temperature, currents, sea level",
             "ok": ok_marine and bool(ocean)},
            {"name": "Open-Meteo Weather API", "role": "10 m wind and gusts", "ok": ok_weather},
        ],
        "errors": errors[:5],
    }
    healthy = bool(ocean) and ok_weather
    _cache_put(key, snapshot, CACHE_TTL_S if healthy else FAILURE_TTL_S)
    return snapshot


def nearest_ocean_point(snapshot: Dict[str, Any], lat: float, lon: float,
                        max_km: float = MAX_OCEAN_SNAP_KM) -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
    """Nearest grid cell that has marine data. A harbour on the coast is often a land cell."""
    best, best_d = None, None
    for p in snapshot.get("points", []):
        if not p["is_ocean"]:
            continue
        d = haversine_km(lat, lon, p["lat"], p["lon"])
        if best_d is None or d < best_d:
            best, best_d = p, d
    if best is None or best_d > max_km:
        return None, None
    return best, round(best_d, 1)


# ─── SST thermal fronts (derived candidate fishing zones) ─────────────────────

def detect_sst_fronts(points: List[Dict[str, Any]], step_deg: float = GRID_STEP_DEG,
                      min_gradient_c_per_km: float = 0.02, max_zones: int = 6,
                      min_separation_km: float = 15.0) -> List[Dict[str, Any]]:
    """
    Find strong horizontal SST gradients (thermal fronts), which tend to aggregate
    baitfish. This is a *model-derived candidate*, NOT an official INCOIS PFZ advisory.
    The score is front strength only (1.0 °C per 10 km => 100).
    """
    idx = {(round(p["lat"] / step_deg), round(p["lon"] / step_deg)): p
           for p in points if p["is_ocean"] and p["sst_c"] is not None}

    def grad(i, j, di, dj, km):
        a, b = idx.get((i - di, j - dj)), idx.get((i + di, j + dj))
        c = idx[(i, j)]
        if a and b:
            return (b["sst_c"] - a["sst_c"]) / (2 * km)
        if b:
            return (b["sst_c"] - c["sst_c"]) / km
        if a:
            return (c["sst_c"] - a["sst_c"]) / km
        return 0.0

    cands = []
    for (i, j), p in idx.items():
        km_y = step_deg * 111.32
        km_x = step_deg * 111.32 * math.cos(math.radians(p["lat"]))
        g = math.hypot(grad(i, j, 0, 1, km_x), grad(i, j, 1, 0, km_y))
        if g >= min_gradient_c_per_km:
            cands.append((g, p))
    cands.sort(key=lambda x: x[0], reverse=True)

    chosen: List[Dict[str, Any]] = []
    for g, p in cands:
        if any(haversine_km(p["lat"], p["lon"], c["lat"], c["lon"]) < min_separation_km for c in chosen):
            continue
        chosen.append({
            "pfz_id": f"SSTF_{p['lat']}_{p['lon']}",
            "name": f"SST Thermal Front {p['lat']:.2f}°N {p['lon']:.2f}°E",
            "lat": p["lat"], "lon": p["lon"],
            "sst_c": p["sst_c"],
            "sst_gradient_c_per_km": round(g, 3),
            "chlorophyll_mg_m3": None,          # no live chlorophyll feed connected
            "depth_m": None,
            "species_likely": [],
            "productivity_score": min(100.0, round(g / 0.10 * 100, 1)),
            "score_basis": "SST_FRONT_STRENGTH",
            "source": "Derived from Open-Meteo SST grid (not an official INCOIS PFZ)",
            "wave_height_m": p["wave_height_m"],
            "wind_kmh": p["wind_kmh"],
            "valid_time": p["marine_valid_time"],
        })
        if len(chosen) >= max_zones:
            break
    return chosen


# ─── Hourly outlook (departure windows) ───────────────────────────────────────

def get_hourly_outlook(lat: float, lon: float, hours: int = 48) -> Dict[str, Any]:
    key = ("hourly", _snap(lat), _snap(lon))
    cached = _cache_get(key)
    if cached is not None:
        return cached
    result: Dict[str, Any] = {"fetched_at": datetime.now(timezone.utc).isoformat(), "hours": [], "error": None}
    try:
        m = _http_get_json(MARINE_URL, {"latitude": lat, "longitude": lon,
                                        "hourly": "wave_height", "forecast_days": 3})
        w = _http_get_json(WEATHER_URL, {"latitude": lat, "longitude": lon,
                                         "hourly": "wind_speed_10m", "forecast_days": 3,
                                         "wind_speed_unit": "kmh"})
        mh, wh = m.get("hourly", {}), w.get("hourly", {})
        mu = (w.get("hourly_units") or {}).get("wind_speed_10m", "km/h")
        waves = dict(zip(mh.get("time", []), mh.get("wave_height", [])))
        floor_now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for t, ws in zip(wh.get("time", []), wh.get("wind_speed_10m", [])):
            iso = _iso_utc(t)
            if iso is None or datetime.fromisoformat(iso) < floor_now:
                continue
            result["hours"].append({"time_utc": iso, "wave_height_m": waves.get(t),
                                    "wind_kmh": _to_kmh(ws, mu)})
        result["hours"] = result["hours"][:hours]
    except Exception as exc:
        result["error"] = str(exc)
    _cache_put(key, result, CACHE_TTL_S if not result["error"] else FAILURE_TTL_S)
    return result


def safe_windows(hours: List[Dict[str, Any]], max_wave_m: float, max_wind_kmh: float,
                 min_hours: int = 2) -> List[Dict[str, Any]]:
    """Contiguous runs of hours where both wave height and wind are within vessel limits."""
    windows, run = [], []

    def flush():
        if len(run) >= min_hours:
            windows.append({
                "start_utc": run[0]["time_utc"],
                "end_utc": (datetime.fromisoformat(run[-1]["time_utc"]) + timedelta(hours=1)).isoformat(),
                "hours": len(run),
                "max_wave_m": max(h["wave_height_m"] for h in run),
                "max_wind_kmh": max(h["wind_kmh"] for h in run),
            })

    for h in hours:
        ok = (h["wave_height_m"] is not None and h["wind_kmh"] is not None
              and h["wave_height_m"] <= max_wave_m and h["wind_kmh"] <= max_wind_kmh)
        if ok:
            run.append(h)
        else:
            flush()
            run = []
    flush()
    return windows
