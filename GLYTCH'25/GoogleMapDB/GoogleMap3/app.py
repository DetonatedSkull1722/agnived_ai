from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path
import math

app = Flask(__name__)
DB = Path("locations.db")


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            description TEXT NOT NULL,
            labels TEXT NOT NULL  -- comma-separated labels
        )
    """)
    conn.commit()
    conn.close()


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points (in km)."""
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@app.route("/", methods=["GET", "POST"])
def index():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    if request.method == "POST":
        lat = request.form["lat"]
        lng = request.form["lng"]
        desc = request.form["description"].strip()
        selected_labels = request.form.getlist("labels")
        labels_str = ",".join(selected_labels)

        if lat and lng and desc:
            cur.execute(
                "INSERT INTO locations (lat, lng, description, labels) VALUES (?, ?, ?, ?)",
                (lat, lng, desc, labels_str)
            )
            conn.commit()

        conn.close()
        return redirect(url_for("index"))

    cur.execute("SELECT lat, lng, description, labels FROM locations")
    locations = cur.fetchall()
    conn.close()

    return render_template("index.html", locations=locations)


@app.route("/search", methods=["GET", "POST"])
def search():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT lat, lng, description, labels FROM locations")
    all_locations = cur.fetchall()
    conn.close()

    matches = []
    query_lat = None
    query_lng = None
    radius_km = None

    if request.method == "POST":
        lat_str = request.form.get("lat")
        lng_str = request.form.get("lng")
        radius_str = request.form.get("radius_km")

        try:
            query_lat = float(lat_str)
            query_lng = float(lng_str)
            radius_km = float(radius_str)
        except (TypeError, ValueError):
            query_lat = query_lng = radius_km = None

        if query_lat is not None and query_lng is not None and radius_km is not None:
            for lat, lng, desc, labels_str in all_locations:
                dist = haversine_km(query_lat, query_lng, lat, lng)
                if dist <= radius_km:
                    matches.append({
                        "lat": lat,
                        "lng": lng,
                        "description": desc,
                        "labels": labels_str,
                        "distance_km": round(dist, 3),
                    })

    return render_template(
        "search.html",
        matches=matches,
        query_lat=query_lat,
        query_lng=query_lng,
        radius_km=radius_km,
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
