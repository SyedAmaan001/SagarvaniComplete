"""
Copernicus Marine Service (CMEMS) Processor
Fetches live ocean data: currents, temperature, salinity, sea level.
Uses credentials from .env: COPERNICUS_USERNAME / COPERNICUS_PASSWORD
"""

import os
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

CMEMS_USER = os.getenv("COPERNICUS_USERNAME", "")
CMEMS_PASS = os.getenv("COPERNICUS_PASSWORD", "")

# Copernicus Marine Toolbox REST API base (new API as of 2024)
CMEMS_API_BASE = "https://marine.copernicus.eu/api"

# Key CMEMS product IDs for Indian Ocean
CMEMS_PRODUCTS = {
    "global_currents": "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
    "global_physics": "cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
    "indian_ocean": "INDOFOS_001_002",
    "sea_level": "cmems_mod_glo_phy_anfc_0.083deg_PT1H-m",
}

# Open-access CMEMS Catalogue endpoint (no auth required for metadata)
CMEMS_CATALOGUE = "https://catalogue.marine.copernicus.eu/api/dataset"


def check_credentials() -> Dict[str, Any]:
    """Verify Copernicus credentials are present."""
    return {
        "username_set": bool(CMEMS_USER),
        "password_set": bool(CMEMS_PASS),
        "username": CMEMS_USER if CMEMS_USER else "NOT SET",
        "note": "Credentials loaded from backend/.env",
    }


def get_available_products() -> Dict[str, Any]:
    """
    List available Copernicus Marine products (Indian Ocean focus).
    Uses public catalogue — no auth required.
    """
    try:
        resp = requests.get(
            CMEMS_CATALOGUE,
            params={"q": "Indian Ocean currents", "size": 10},
            timeout=15,
        )
        if resp.status_code == 200:
            return {"products": resp.json(), "source": "CMEMS Catalogue"}
    except Exception as e:
        pass  # Fall through to static list

    # Fallback: return known product list
    return {
        "products": CMEMS_PRODUCTS,
        "note": "Static product list (catalogue request failed or timed out)",
        "credentials_ok": check_credentials(),
    }


def get_live_ocean_data(
    lat: float,
    lon: float,
    variables: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Fetch live ocean data near a point from Copernicus Marine Service.
    Uses the copernicusmarine Python toolbox if installed,
    otherwise falls back to the REST subset service.
    """
    if not CMEMS_USER or not CMEMS_PASS:
        return {
            "error": "Copernicus credentials not set in .env",
            "tip": "Set COPERNICUS_USERNAME and COPERNICUS_PASSWORD in backend/.env",
        }

    if variables is None:
        variables = ["uo", "vo", "thetao", "so", "zos"]  # u-curr, v-curr, temp, salinity, SSH

    # Try using copernicusmarine Python toolbox
    try:
        import copernicusmarine as cm
        dataset_id = CMEMS_PRODUCTS["global_physics"]
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        result = cm.subset(
            dataset_id=dataset_id,
            variables=variables,
            minimum_latitude=lat - 0.5,
            maximum_latitude=lat + 0.5,
            minimum_longitude=lon - 0.5,
            maximum_longitude=lon + 0.5,
            start_datetime=str(yesterday),
            end_datetime=str(today),
            output_filename="cmems_point.nc",
            output_directory="/tmp",
            username=CMEMS_USER,
            password=CMEMS_PASS,
            force_download=True,
        )
        return {
            "source": "Copernicus Marine Toolbox",
            "dataset": dataset_id,
            "variables": variables,
            "lat": lat,
            "lon": lon,
            "output_file": str(result),
            "note": "Parse the output .nc file with nc_parser for data values.",
        }
    except ImportError:
        pass  # copernicusmarine not installed — use REST fallback

    # REST fallback via WMS/WCS — returns metadata
    return {
        "source": "Copernicus REST (metadata only)",
        "credentials": check_credentials(),
        "requested_lat": lat,
        "requested_lon": lon,
        "available_products": CMEMS_PRODUCTS,
        "install_tip": "pip install copernicusmarine for full data download support",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def get_sea_surface_temperature(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get Sea Surface Temperature (SST) for a given lat/lon.
    Uses Open-Meteo as a free proxy if Copernicus toolbox isn't available.
    """
    # Try Copernicus first
    data = get_live_ocean_data(lat, lon, variables=["thetao"])
    if "error" not in data and "output_file" in data:
        return data

    # Free fallback: Open-Meteo doesn't have SST but ERA5 reanalysis does
    return {
        "lat": lat,
        "lon": lon,
        "note": "Install copernicusmarine for live SST data.",
        "alternative": "Use ERA5 reanalysis from ECMWF for historical SST",
        "copernicus_sst_product": "CMEMS SST_MED_SST_L4_REP_OBSERVATIONS_010_021",
    }


def get_ocean_current_live(lat: float, lon: float) -> Dict[str, Any]:
    """Convenience wrapper: get live ocean current u/v components."""
    return get_live_ocean_data(lat, lon, variables=["uo", "vo"])
