import os
import math
from typing import Optional, Dict, Any

from flask import Flask, render_template, request
from dotenv import load_dotenv
import requests

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
load_dotenv()

MAPILLARY_TOKEN = os.getenv("MAPILLARY_TOKEN")
if not MAPILLARY_TOKEN:
    raise RuntimeError(
        "MAPILLARY_TOKEN is not set. "
        "Create a .env file with MAPILLARY_TOKEN=MLY|your_token_here"
    )

MAPILLARY_IMAGES_URL = "https://graph.mapillary.com/images"

app = Flask(__name__)


# ---------------------------------------------------------------------
# Geo helpers
# ---------------------------------------------------------------------
def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Distance between two (lat, lon) points in meters using haversine formula.
    """
    R = 6371000.0  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def bbox_from_point(
    lat: float, lon: float, radius_m: float = 100.0
) -> Dict[str, float]:
    """
    Approximate bounding box around a point for a given radius (in meters).
    Returns dict with min_lat, max_lat, min_lon, max_lon.
    """
    # 1 degree latitude ≈ 111.32 km
    delta_lat = radius_m / 111_320.0

    # 1 degree longitude ≈ 111.32 km * cos(latitude)
    lat_rad = math.radians(lat)
    meters_per_deg_lon = 111_320.0 * max(math.cos(lat_rad), 1e-6)
    delta_lon = radius_m / meters_per_deg_lon

    return {
        "min_lat": lat - delta_lat,
        "max_lat": lat + delta_lat,
        "min_lon": lon - delta_lon,
        "max_lon": lon + delta_lon,
    }


# ---------------------------------------------------------------------
# Mapillary logic
# ---------------------------------------------------------------------
def find_nearest_vr_image(
    lat: float,
    lon: float,
    radius_m: float = 100.0,
    token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Query Mapillary v4 for the image closest to (lat, lon) within radius_m.

    Returns:
      {
        "id": <image_id>,
        "lat": <image_lat>,
        "lon": <image_lon>,
        "distance_m": <distance>,
        "viewer_url": "https://www.mapillary.com/app/?focus=photo&pKey=<id>"
      }
    or None if nothing found.
    """
    if token is None:
        token = MAPILLARY_TOKEN

    bbox = bbox_from_point(lat, lon, radius_m=radius_m)
    params = {
        "fields": "id,geometry",
        "bbox": f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}",
        "limit": 2000,
    }
    headers = {"Authorization": f"OAuth {token}"}

    resp = requests.get(MAPILLARY_IMAGES_URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    images = data.get("data") or []
    if not images:
        return None

    best = None
    best_dist = float("inf")

    for img in images:
        geom = img.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords or len(coords) < 2:
            continue

        img_lon, img_lat = coords[0], coords[1]
        dist = haversine_distance_m(lat, lon, img_lat, img_lon)

        if dist < best_dist:
            best_dist = dist
            best = {
                "id": img["id"],
                "lat": img_lat,
                "lon": img_lon,
                "distance_m": dist,
                "viewer_url": f"https://www.mapillary.com/app/?focus=photo&pKey={img['id']}",
            }

    return best


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    lat_value = ""
    lon_value = ""

    if request.method == "POST":
        lat_str = request.form.get("lat", "").strip()
        lon_str = request.form.get("lon", "").strip()
        lat_value = lat_str
        lon_value = lon_str

        if not lat_str or not lon_str:
            error = "Please enter both latitude and longitude."
        else:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                nearest = find_nearest_vr_image(lat, lon, radius_m=100.0)
                if nearest is None:
                    error = "No imagery found within 100m of this location."
                else:
                    result = {
                        "input_lat": lat,
                        "input_lon": lon,
                        "image_id": nearest["id"],
                        "image_lat": nearest["lat"],
                        "image_lon": nearest["lon"],
                        "distance_m": nearest["distance_m"],
                        "viewer_url": nearest["viewer_url"],
                    }
            except ValueError:
                error = "Latitude and longitude must be valid numbers."
            except requests.RequestException as e:
                error = f"Error talking to Mapillary API: {e}"

    return render_template(
        "index.html",
        mapillary_token=MAPILLARY_TOKEN,
        result=result,
        error=error,
        lat_value=lat_value,
        lon_value=lon_value,
    )


if __name__ == "__main__":
    # Dev only
    app.run(host="0.0.0.0", port=5000, debug=True)
