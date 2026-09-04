"""
NetCDF Ocean Current Parser
Parses MOSDAC Global Ocean Surface Current .nc files.
Files: ISRO_CURRENT_TOT_YYYYMMDD.nc
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

try:
    import netCDF4 as nc4
    NC4_OK = True
except ImportError:
    NC4_OK = False


# Path to the MOSDAC ocean current data folder
OCEAN_CURRENT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "MOSDAC", "Global Ocean Surface Current"
)


def _find_all_nc_files(base_dir: str) -> List[str]:
    """Recursively find all .nc files under base_dir."""
    pattern = os.path.join(base_dir, "**", "*.nc")
    return sorted(glob.glob(pattern, recursive=True))


def parse_ocean_current_xarray(filepath: str) -> Dict[str, Any]:
    """
    Parse a MOSDAC ocean current NetCDF file using xarray.
    Returns a dict with lat/lon grid and u/v current components.
    """
    if not XARRAY_OK:
        raise ImportError("xarray is not installed. Run: pip install xarray")

    ds = xr.open_dataset(filepath, engine="netcdf4")
    result = {
        "source_file": os.path.basename(filepath),
        "variables": list(ds.data_vars),
        "dimensions": dict(ds.dims),
        "coordinates": list(ds.coords),
        "global_attrs": {k: str(v) for k, v in ds.attrs.items()},
    }

    # Try to extract standard ocean current variables
    u_var = _find_var(ds, ["u", "u_curr", "ucur", "uo", "vozocrtx", "u_surface"])
    v_var = _find_var(ds, ["v", "v_curr", "vcur", "vo", "vomecrty", "v_surface"])
    lat_var = _find_var(ds, ["lat", "latitude", "Latitude", "y"])
    lon_var = _find_var(ds, ["lon", "longitude", "Longitude", "x"])

    if lat_var and lon_var:
        lats = ds[lat_var].values.tolist()
        lons = ds[lon_var].values.tolist()
        result["lat_range"] = [float(np.nanmin(lats)), float(np.nanmax(lats))]
        result["lon_range"] = [float(np.nanmin(lons)), float(np.nanmax(lons))]
        result["lat_count"] = len(lats) if isinstance(lats, list) else int(np.array(lats).size)
        result["lon_count"] = len(lons) if isinstance(lons, list) else int(np.array(lons).size)

    if u_var and v_var:
        u_data = ds[u_var].values
        v_data = ds[v_var].values
        # Compute speed magnitude
        speed = np.sqrt(u_data**2 + v_data**2)
        result["current_speed"] = {
            "mean_ms": float(np.nanmean(speed)),
            "max_ms": float(np.nanmax(speed)),
            "min_ms": float(np.nanmin(speed)),
            "unit": "m/s",
        }
        result["u_component"] = {
            "mean": float(np.nanmean(u_data)),
            "max": float(np.nanmax(u_data)),
            "min": float(np.nanmin(u_data)),
        }
        result["v_component"] = {
            "mean": float(np.nanmean(v_data)),
            "max": float(np.nanmax(v_data)),
            "min": float(np.nanmin(v_data)),
        }

        # Build a sampled grid (every 5th point for API efficiency)
        if lat_var and lon_var:
            lats_arr = np.array(ds[lat_var].values).flatten()
            lons_arr = np.array(ds[lon_var].values).flatten()
            spd_flat = speed.flatten() if speed.ndim > 1 else speed
            u_flat = u_data.flatten() if u_data.ndim > 1 else u_data
            v_flat = v_data.flatten() if v_data.ndim > 1 else v_data

            step = max(1, len(spd_flat) // 500)  # cap at ~500 points for API
            sampled = []
            for i in range(0, min(len(lats_arr), len(lons_arr), len(spd_flat)), step):
                if not (np.isnan(spd_flat[i]) or np.isnan(u_flat[i]) or np.isnan(v_flat[i])):
                    sampled.append({
                        "lat": round(float(lats_arr[i % len(lats_arr)]), 4),
                        "lon": round(float(lons_arr[i % len(lons_arr)]), 4),
                        "speed_ms": round(float(spd_flat[i]), 4),
                        "u_ms": round(float(u_flat[i]), 4),
                        "v_ms": round(float(v_flat[i]), 4),
                    })
            result["sampled_grid"] = sampled[:500]

    ds.close()
    return result


def _find_var(ds: Any, candidates: List[str]) -> Optional[str]:
    """Find the first matching variable name in a dataset."""
    for name in candidates:
        if name in ds.data_vars or name in ds.coords:
            return name
    # Case-insensitive fallback
    ds_lower = {k.lower(): k for k in list(ds.data_vars) + list(ds.coords)}
    for name in candidates:
        if name.lower() in ds_lower:
            return ds_lower[name.lower()]
    return None


def get_latest_ocean_current() -> Dict[str, Any]:
    """
    Find and parse the most recent ocean current .nc file.
    Returns parsed data dict or error dict.
    """
    base = os.path.abspath(OCEAN_CURRENT_DIR)
    files = _find_all_nc_files(base)
    if not files:
        return {"error": "No ocean current .nc files found", "searched_dir": base}

    # Latest file = last in sorted list
    latest = files[-1]
    try:
        data = parse_ocean_current_xarray(latest)
        data["parsed_at"] = datetime.utcnow().isoformat() + "Z"
        return data
    except Exception as e:
        return {"error": str(e), "file": latest}


def get_all_ocean_current_summaries() -> List[Dict[str, Any]]:
    """
    Return summary stats from ALL ocean current .nc files.
    """
    base = os.path.abspath(OCEAN_CURRENT_DIR)
    files = _find_all_nc_files(base)
    summaries = []
    for f in files:
        try:
            data = parse_ocean_current_xarray(f)
            summaries.append({
                "file": os.path.basename(f),
                "current_speed": data.get("current_speed"),
                "lat_range": data.get("lat_range"),
                "lon_range": data.get("lon_range"),
            })
        except Exception as e:
            summaries.append({"file": os.path.basename(f), "error": str(e)})
    return summaries


def get_point_ocean_current(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get the nearest ocean current data point to a given lat/lon.
    """
    data = get_latest_ocean_current()
    if "error" in data:
        return data

    grid = data.get("sampled_grid", [])
    if not grid:
        return {"error": "No grid data available"}

    # Find nearest point
    best = min(grid, key=lambda p: (p["lat"] - lat)**2 + (p["lon"] - lon)**2)
    return {
        "requested_lat": lat,
        "requested_lon": lon,
        "nearest_lat": best["lat"],
        "nearest_lon": best["lon"],
        "speed_ms": best["speed_ms"],
        "u_ms": best["u_ms"],
        "v_ms": best["v_ms"],
        "source_file": data.get("source_file"),
    }
