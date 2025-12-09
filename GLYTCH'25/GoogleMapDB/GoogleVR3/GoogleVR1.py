import os
import math
from typing import Optional, Dict, Any
from pathlib import Path

from flask import Flask, render_template, request, url_for
from dotenv import load_dotenv
import requests
import cv2
import numpy as np

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
MAPILLARY_IMAGE_DETAIL_URL = "https://graph.mapillary.com"

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PANOS_DIR = STATIC_DIR / "panos"
VIEWS_DIR = STATIC_DIR / "views"
PANOS_DIR.mkdir(parents=True, exist_ok=True)
VIEWS_DIR.mkdir(parents=True, exist_ok=True)

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
def find_nearest_vr_images(
    lat: float,
    lon: float,
    n: int = 5,
    radius_m: float = 100.0,
    token: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """
    Query Mapillary v4 for up to N closest images to (lat, lon) within radius_m.

    Returns a list of dicts:
      [
        {
          "id": <image_id>,
          "lat": <image_lat>,
          "lon": <image_lon>,
          "distance_m": <distance>,
          "viewer_url": "...",
          "is_pano": <bool>,
          "thumb_2048_url": <str | None>
        },
        ...
      ]
    Sorted by distance_m ascending.
    """
    if token is None:
        token = MAPILLARY_TOKEN

    bbox = bbox_from_point(lat, lon, radius_m=radius_m)
    params = {
        # ask for everything we need in one go
        "fields": "id,geometry,is_pano,thumb_2048_url",
        "bbox": f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}",
        "limit": 2000,  # upper bound
    }
    headers = {"Authorization": f"OAuth {token}"}

    resp = requests.get(MAPILLARY_IMAGES_URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    images = data.get("data") or []
    if not images:
        return []

    results: list[Dict[str, Any]] = []
    for img in images:
        geom = img.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords or len(coords) < 2:
            continue

        img_lon, img_lat = coords[0], coords[1]
        dist = haversine_distance_m(lat, lon, img_lat, img_lon)

        results.append(
            {
                "id": img["id"],
                "lat": img_lat,
                "lon": img_lon,
                "distance_m": dist,
                "viewer_url": f"https://www.mapillary.com/app/?focus=photo&pKey={img['id']}",
                "is_pano": bool(img.get("is_pano", False)),
                "thumb_2048_url": img.get("thumb_2048_url"),
            }
        )

    # sort by distance and return only N
    results.sort(key=lambda r: r["distance_m"])
    return results[:n]



def get_image_metadata(image_id: str) -> Optional[Dict[str, Any]]:
    """
    Get URL + pano info for a given image_id.
    We ask for a 2048px thumbnail and some metadata.
    """
    headers = {"Authorization": f"OAuth {MAPILLARY_TOKEN}"}
    fields = "thumb_2048_url,width,height,is_pano"
    url = f"{MAPILLARY_IMAGE_DETAIL_URL}/{image_id}?fields={fields}"
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data


# ---------------------------------------------------------------------
# 360 (equirectangular) → multiple normal views helpers
# ---------------------------------------------------------------------
def perspective_from_equirect(pano: np.ndarray,
                              yaw_deg: float,
                              pitch_deg: float,
                              fov_deg: float,
                              out_w: int,
                              out_h: int) -> np.ndarray:
    """
    Convert equirectangular pano to a single perspective view.

    pano: H x W x 3 BGR
    yaw_deg: yaw angle in degrees
    pitch_deg: pitch angle in degrees (positive = look up)
    fov_deg: horizontal field of view in degrees
    out_w, out_h: output resolution
    """
    h_in, w_in = pano.shape[:2]
    yaw = np.deg2rad(yaw_deg)
    pitch = np.deg2rad(pitch_deg)
    fov = np.deg2rad(fov_deg)

    # focal length in pixels
    f = 0.5 * out_w / math.tan(fov / 2.0)

    xs = np.linspace(-out_w / 2.0, out_w / 2.0, out_w)
    ys = np.linspace(-out_h / 2.0, out_h / 2.0, out_h)
    x_grid, y_grid = np.meshgrid(xs, ys)

    z = f * np.ones_like(x_grid)
    x = x_grid
    y = -y_grid  # flip Y to match image coordinates

    # normalize rays
    norm = np.sqrt(x * x + y * y + z * z)
    x /= norm
    y /= norm
    z /= norm

    # pitch around X
    sin_pitch, cos_pitch = np.sin(pitch), np.cos(pitch)
    y_p = y * cos_pitch - z * sin_pitch
    z_p = y * sin_pitch + z * cos_pitch
    x_p = x

    # yaw around Y
    sin_yaw, cos_yaw = np.sin(yaw), np.cos(yaw)
    x_y = x_p * cos_yaw + z_p * sin_yaw
    y_y = y_p
    z_y = -x_p * sin_yaw + z_p * cos_yaw

    # directions to spherical
    lon = np.arctan2(x_y, z_y)  # [-pi, pi]
    lat = np.arcsin(y_y)        # [-pi/2, pi/2]

    # spherical → pano coordinates
    x_pano = (lon / (2 * np.pi) + 0.5) * w_in
    y_pano = (0.5 - lat / np.pi) * h_in

    map_x = x_pano.astype(np.float32)
    map_y = y_pano.astype(np.float32)

    perspective = cv2.remap(
        pano, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP
    )
    return perspective


def generate_normal_views_for_pano(image_id: str, image_url: str) -> Dict[str, str]:
    """
    Download the pano, generate 4 non-overlapping perspective views
    (front/right/back/left), save them under static/views, and return
    a dict name -> relative URL.
    """
    # Download pano
    pano_path = PANOS_DIR / f"{image_id}.jpg"
    if not pano_path.exists():
        r = requests.get(image_url, stream=True, timeout=15)
        r.raise_for_status()
        with open(pano_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    pano = cv2.imread(str(pano_path))
    if pano is None:
        return {}

    out_w, out_h = 800, 600
    fov_deg = 90
    pitch_deg = 0
    yaw_list = [0, 90, 180, 270]
    names = {0: "front", 90: "right", 180: "back", 270: "left"}

    results: Dict[str, str] = {}

    for yaw in yaw_list:
        view = perspective_from_equirect(
            pano,
            yaw_deg=yaw,
            pitch_deg=pitch_deg,
            fov_deg=fov_deg,
            out_w=out_w,
            out_h=out_h,
        )
        name = names.get(yaw, str(yaw))
        out_path = VIEWS_DIR / f"{image_id}_{name}.jpg"
        cv2.imwrite(str(out_path), view)

        # URL to serve via Flask static
        rel_path = f"views/{image_id}_{name}.jpg"
        results[name] = url_for("static", filename=rel_path)

    return results


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    result_list = []   # list of images
    error = None
    lat_value = ""
    lon_value = ""
    count_value = "3"  # default N

    if request.method == "POST":
        lat_str = request.form.get("lat", "").strip()
        lon_str = request.form.get("lon", "").strip()
        count_str = request.form.get("count", "").strip() or "3"

        lat_value = lat_str
        lon_value = lon_str
        count_value = count_str

        if not lat_str or not lon_str:
            error = "Please enter both latitude and longitude."
        else:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                n = int(count_str)
                if n <= 0:
                    n = 1

                images = find_nearest_vr_images(lat, lon, n=n, radius_m=100.0)

                if not images:
                    error = f"No imagery found within 100m of this location."
                else:
                    # enrich with input lat/lon so template can use it
                    for img in images:
                        img["input_lat"] = lat
                        img["input_lon"] = lon
                    result_list = images

            except ValueError:
                error = "Latitude, longitude and count must be valid numbers."
            except requests.RequestException as e:
                error = f"Error talking to Mapillary API: {e}"

    # You can still keep your normal_views logic if you like,
    # but for simplicity let's just pass result_list now.
    return render_template(
        "index.html",
        mapillary_token=MAPILLARY_TOKEN,
        results=result_list,   # note plural
        error=error,
        lat_value=lat_value,
        lon_value=lon_value,
        count_value=count_value,
    )


if __name__ == "__main__":
    # Dev only
    app.run(host="0.0.0.0", port=5000, debug=True)
