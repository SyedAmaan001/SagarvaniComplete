"""
Geospatial Utility Functions
Handles distance calculations, bounding boxes, and GeoJSON building.
"""

import math
from typing import Tuple, List, Dict, Any


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points in kilometers.
    Uses the Haversine formula.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def bounding_box(lat: float, lon: float, radius_km: float) -> Dict[str, float]:
    """
    Return a bounding box dict around (lat, lon) with the given radius in km.
    """
    delta_lat = radius_km / EARTH_RADIUS_KM * (180 / math.pi)
    delta_lon = radius_km / (EARTH_RADIUS_KM * math.cos(math.radians(lat))) * (180 / math.pi)
    return {
        "min_lat": lat - delta_lat,
        "max_lat": lat + delta_lat,
        "min_lon": lon - delta_lon,
        "max_lon": lon + delta_lon,
    }


def make_point_geojson(lat: float, lon: float, properties: Dict[str, Any]) -> Dict[str, Any]:
    """Build a GeoJSON Point Feature."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": properties,
    }


def make_circle_geojson(lat: float, lon: float, radius_km: float,
                         properties: Dict[str, Any], steps: int = 64) -> Dict[str, Any]:
    """
    Approximate a circle as a GeoJSON Polygon Feature.
    """
    coords = []
    for i in range(steps + 1):
        angle = math.radians(360 * i / steps)
        d_lat = (radius_km / EARTH_RADIUS_KM) * (180 / math.pi) * math.cos(angle)
        d_lon = (radius_km / (EARTH_RADIUS_KM * math.cos(math.radians(lat)))) * \
                (180 / math.pi) * math.sin(angle)
        coords.append([lon + d_lon, lat + d_lat])
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [coords]},
        "properties": properties,
    }


def make_feature_collection(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Wrap a list of GeoJSON Features into a FeatureCollection."""
    return {"type": "FeatureCollection", "features": features}


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0–100 range."""
    if max_val == min_val:
        return 0.0
    return max(0.0, min(100.0, (value - min_val) / (max_val - min_val) * 100))


def risk_level(score: float) -> Dict[str, str]:
    """Convert a 0–100 risk score into a level label and color."""
    if score <= 25:
        return {"level": "SAFE", "color": "#22c55e", "emoji": "🟢",
                "advice": "Safe to fish. Conditions are favorable."}
    elif score <= 50:
        return {"level": "CAUTION", "color": "#eab308", "emoji": "🟡",
                "advice": "Exercise caution. Moderate sea conditions."}
    elif score <= 75:
        return {"level": "WARNING", "color": "#f97316", "emoji": "🟠",
                "advice": "Avoid deep-sea fishing. Rough conditions expected."}
    else:
        return {"level": "DANGER", "color": "#ef4444", "emoji": "🔴",
                "advice": "STAY ASHORE. Extremely dangerous sea conditions."}


def point_to_segment_distance_km(p_lat: float, p_lon: float,
                                 a_lat: float, a_lon: float,
                                 b_lat: float, b_lon: float) -> Tuple[float, float, float]:
    """
    Find distance in km from point P to line segment AB, and return the closest point coords.
    """
    # Convert to approximate local Cartesian (km) relative to A
    cos_lat = math.cos(math.radians(a_lat))
    dx_b = (b_lon - a_lon) * (math.pi / 180.0) * EARTH_RADIUS_KM * cos_lat
    dy_b = (b_lat - a_lat) * (math.pi / 180.0) * EARTH_RADIUS_KM

    dx_p = (p_lon - a_lon) * (math.pi / 180.0) * EARTH_RADIUS_KM * cos_lat
    dy_p = (p_lat - a_lat) * (math.pi / 180.0) * EARTH_RADIUS_KM

    seg_len_sq = dx_b * dx_b + dy_b * dy_b
    if seg_len_sq == 0:
        return haversine_km(p_lat, p_lon, a_lat, a_lon), a_lat, a_lon

    t = max(0.0, min(1.0, (dx_p * dx_b + dy_p * dy_b) / seg_len_sq))
    closest_x = t * dx_b
    closest_y = t * dy_b

    # Convert back to lat/lon
    c_lat = a_lat + (closest_y / EARTH_RADIUS_KM) * (180.0 / math.pi)
    c_lon = a_lon + (closest_x / (EARTH_RADIUS_KM * cos_lat)) * (180.0 / math.pi)

    dist = haversine_km(p_lat, p_lon, c_lat, c_lon)
    return dist, c_lat, c_lon


def compute_safe_detour_route(
    start_lat: float, start_lon: float,
    end_lat: float, end_lon: float,
    restricted_zones: List[Dict[str, Any]],
    safety_buffer_km: float = 3.0
) -> Dict[str, Any]:
    """
    Calculates safest route between departure and target.
    If the direct line intersects any restricted zone circle, computes tangent clearance waypoints.
    Returns GeoJSON LineString coordinates, total distance, and list of avoided restricted zones.
    """
    direct_dist = haversine_km(start_lat, start_lon, end_lat, end_lon)
    intersections = []
    detour_waypoints = []

    for zone in restricted_zones:
        c_lat = zone.get("center_lat", zone.get("lat_center"))
        c_lon = zone.get("center_lon", zone.get("lon_center"))
        radius = zone.get("radius_km", 10.0)
        if c_lat is None or c_lon is None:
            continue

        dist_to_seg, close_lat, close_lon = point_to_segment_distance_km(
            c_lat, c_lon, start_lat, start_lon, end_lat, end_lon
        )

        effective_radius = radius + safety_buffer_km
        if dist_to_seg < effective_radius:
            # Segment intersects this restricted zone!
            intersections.append({
                "zone_name": zone.get("name", "Restricted Area"),
                "restriction_level": zone.get("restriction_level", "PROHIBITED"),
                "clearance_deficit_km": round(effective_radius - dist_to_seg, 2)
            })

            # Calculate safe clearance waypoint on the seaward/offshore side (westward for Indian west coast)
            # Determine displacement vector perpendicular to segment
            d_lat = end_lat - start_lat
            d_lon = end_lon - start_lon
            # Perpendicular vector (-d_lon, d_lat) or (d_lon, -d_lat)
            perp_lat = -d_lon
            perp_lon = d_lat
            norm = math.sqrt(perp_lat * perp_lat + perp_lon * perp_lon) or 1.0
            perp_lat /= norm
            perp_lon /= norm

            # Favor seaward direction (negative lon / westward in Arabian Sea)
            if perp_lon > 0:
                perp_lat = -perp_lat
                perp_lon = -perp_lon

            # Place waypoint at center + perpendicular offset of effective_radius
            cos_c = math.cos(math.radians(c_lat))
            wp_lat = c_lat + (perp_lat * effective_radius / EARTH_RADIUS_KM) * (180.0 / math.pi)
            wp_lon = c_lon + (perp_lon * effective_radius / (EARTH_RADIUS_KM * cos_c)) * (180.0 / math.pi)
            detour_waypoints.append({"lat": round(wp_lat, 4), "lon": round(wp_lon, 4)})

    # Build final coordinates path: [ [lon, lat], ... ]
    route_coords = [[start_lon, start_lat]]
    for wp in detour_waypoints:
        route_coords.append([wp["lon"], wp["lat"]])
    route_coords.append([end_lon, end_lat])

    # Calculate actual path distance
    total_km = 0.0
    for i in range(len(route_coords) - 1):
        total_km += haversine_km(
            route_coords[i][1], route_coords[i][0],
            route_coords[i+1][1], route_coords[i+1][0]
        )

    return {
        "direct_distance_km": round(direct_dist, 1),
        "safe_route_distance_km": round(total_km, 1),
        "detour_waypoints_count": len(detour_waypoints),
        "restricted_intersections_avoided": len(intersections),
        "avoided_zones": intersections,
        "is_detour_required": len(detour_waypoints) > 0,
        "route_coordinates": route_coords,
        "direct_coordinates": [[start_lon, start_lat], [end_lon, end_lat]]
    }

