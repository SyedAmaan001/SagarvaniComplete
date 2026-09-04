"""
SAR Coastal Product Parser
Parses MOSDAC Indian Mainland Coastal Product .nc files (SARAL/AltiKa SAR data).
Files: SRL_033_XXXX_YYYYMMDD_HHMMSS_INDIANCOAST_SIGDR_VER1.1.nc
"""

import os
import glob
import numpy as np
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import xarray as xr
    XARRAY_OK = True
except ImportError:
    XARRAY_OK = False


# Path to MOSDAC Indian Mainland Coastal Product folder
COASTAL_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "MOSDAC", "Indian Mainland Coastal Product"
)


def _find_all_coastal_nc_files(base_dir: str) -> List[str]:
    """Recursively find all SRL_*.nc files."""
    pattern = os.path.join(base_dir, "**", "SRL_*.nc")
    return sorted(glob.glob(pattern, recursive=True))


def parse_sar_file(filepath: str) -> Dict[str, Any]:
    """
    Parse a MOSDAC SAR coastal product NetCDF file.
    Extracts significant wave height, drift, lat/lon track.
    """
    if not XARRAY_OK:
        raise ImportError("xarray is not installed.")

    ds = xr.open_dataset(filepath, engine="netcdf4")
    result = {
        "source_file": os.path.basename(filepath),
        "variables": list(ds.data_vars),
        "dimensions": dict(ds.dims),
        "global_attrs": {k: str(v) for k, v in ds.attrs.items() if len(str(v)) < 200},
    }

    # Standard SAR altimetry variables
    sig_wave_var = _find_var(ds, ["swh", "sig_wave_height", "swh_ku", "wave_height", "Swh"])
    lat_var = _find_var(ds, ["lat", "latitude", "Latitude"])
    lon_var = _find_var(ds, ["lon", "longitude", "Longitude"])
    time_var = _find_var(ds, ["time", "Time", "time_01"])
    wind_var = _find_var(ds, ["wind_speed", "wind_speed_model_u", "wind"])
    backscatter_var = _find_var(ds, ["sig0", "backscatter", "sigma0", "sigma0_ku"])

    # Extract lat/lon track
    if lat_var and lon_var:
        lats = ds[lat_var].values.flatten()
        lons = ds[lon_var].values.flatten()
        valid = ~(np.isnan(lats) | np.isnan(lons))
        lats, lons = lats[valid], lons[valid]
        result["track"] = {
            "lat_range": [float(np.nanmin(lats)), float(np.nanmax(lats))],
            "lon_range": [float(np.nanmin(lons)), float(np.nanmax(lons))],
            "point_count": int(len(lats)),
        }
        # Sampled track for GeoJSON
        step = max(1, len(lats) // 200)
        result["track_points"] = [
            {"lat": round(float(lats[i]), 5), "lon": round(float(lons[i]), 5)}
            for i in range(0, len(lats), step)
        ]

    # Significant wave height
    if sig_wave_var:
        swh = ds[sig_wave_var].values.flatten()
        swh = swh[~np.isnan(swh)]
        if len(swh) > 0:
            result["significant_wave_height"] = {
                "mean_m": round(float(np.nanmean(swh)), 3),
                "max_m": round(float(np.nanmax(swh)), 3),
                "min_m": round(float(np.nanmin(swh)), 3),
                "unit": "meters",
                "count": int(len(swh)),
            }

    # Wind speed
    if wind_var:
        ws = ds[wind_var].values.flatten()
        ws = ws[~np.isnan(ws)]
        if len(ws) > 0:
            result["wind_speed"] = {
                "mean_ms": round(float(np.nanmean(ws)), 3),
                "max_ms": round(float(np.nanmax(ws)), 3),
                "unit": "m/s",
            }

    # Backscatter
    if backscatter_var:
        bs = ds[backscatter_var].values.flatten()
        bs = bs[~np.isnan(bs)]
        if len(bs) > 0:
            result["backscatter_sigma0"] = {
                "mean_dB": round(float(np.nanmean(bs)), 3),
                "max_dB": round(float(np.nanmax(bs)), 3),
                "unit": "dB",
            }

    # Time info
    if time_var:
        try:
            t = ds[time_var].values
            result["time_range"] = {
                "start": str(np.nanmin(t)),
                "end": str(np.nanmax(t)),
            }
        except Exception:
            pass

    ds.close()
    result["parsed_at"] = datetime.utcnow().isoformat() + "Z"
    return result


def _find_var(ds: Any, candidates: List[str]) -> Optional[str]:
    """Find first matching variable or coordinate name."""
    all_names = list(ds.data_vars) + list(ds.coords)
    for name in candidates:
        if name in all_names:
            return name
    all_lower = {k.lower(): k for k in all_names}
    for name in candidates:
        if name.lower() in all_lower:
            return all_lower[name.lower()]
    return None


def get_coastal_summary() -> Dict[str, Any]:
    """
    Summarise all available SAR coastal .nc files.
    Groups by cyclone/track ID.
    """
    base = os.path.abspath(COASTAL_DIR)
    files = _find_all_coastal_nc_files(base)

    if not files:
        return {"error": "No SAR coastal .nc files found", "searched_dir": base}

    summaries = []
    total_swh_values = []

    for f in files[:10]:  # limit to 10 for speed (56 files available)
        try:
            data = parse_sar_file(f)
            swh = data.get("significant_wave_height", {})
            summaries.append({
                "file": os.path.basename(f),
                "swh_mean_m": swh.get("mean_m"),
                "swh_max_m": swh.get("max_m"),
                "track": data.get("track"),
                "wind_speed": data.get("wind_speed"),
            })
            if swh.get("mean_m"):
                total_swh_values.append(swh["mean_m"])
        except Exception as e:
            summaries.append({"file": os.path.basename(f), "error": str(e)})

    overall_swh_mean = round(float(np.mean(total_swh_values)), 3) if total_swh_values else None

    return {
        "total_files": len(files),
        "parsed_count": len(summaries),
        "overall_swh_mean_m": overall_swh_mean,
        "files": summaries,
        "coastal_dir": base,
    }


def get_latest_coastal_pass() -> Dict[str, Any]:
    """Parse the latest SAR coastal pass file."""
    base = os.path.abspath(COASTAL_DIR)
    files = _find_all_coastal_nc_files(base)
    if not files:
        return {"error": "No SAR coastal .nc files found"}
    try:
        return parse_sar_file(files[-1])
    except Exception as e:
        return {"error": str(e), "file": files[-1]}
