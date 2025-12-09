import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
DB_PATH = "uploads.db"

# Mapillary API token - replace with your actual token
MAPILLARY_TOKEN = os.environ.get('MAPILLARY_TOKEN', 'MLY|YOUR_MAPILLARY_CLIENT_TOKEN_HERE')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create users table first
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT
        )
        """
    )
    
    # Create uploads table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content_type TEXT,
            image BLOB,
            latitude REAL,
            longitude REAL,
            created_at TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    
    # Check if user_id column exists in uploads table, if not add it
    cur.execute("PRAGMA table_info(uploads)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'user_id' not in columns:
        try:
            cur.execute("ALTER TABLE uploads ADD COLUMN user_id INTEGER")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    conn.commit()
    conn.close()


# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "user")  # Default to user role
        
        if not username or not password:
            flash("Username and password are required")
            return redirect(url_for('register'))
        
        if role not in ['user', 'admin']:
            role = 'user'
        
        password_hash = generate_password_hash(password)
        created_at = datetime.utcnow().isoformat()
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, created_at)
            )
            conn.commit()
            conn.close()
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists")
            return redirect(url_for('register'))
    
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash, role FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[2]
            flash(f"Welcome back, {username}!")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password")
            return redirect(url_for('login'))
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out")
    return redirect(url_for('login'))


@app.route("/", methods=["GET"])
@login_required
def index():
    # This will render templates/index.html
    return render_template("index.html")


@app.route("/analysis", methods=["GET"])
@login_required
def analysis():
    # Default center coordinates (can be changed based on user's first upload)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get the most recent upload location for this user as default center
    user_id = session.get('user_id')
    cur.execute("""
        SELECT latitude, longitude 
        FROM uploads 
        WHERE user_id = ? AND latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY created_at DESC 
        LIMIT 1
    """, (user_id,))
    
    result = cur.fetchone()
    conn.close()
    
    # Default to a general location if no uploads exist
    start_lat = result[0] if result else 20.5937
    start_lng = result[1] if result else 78.9629
    
    return render_template(
        "analysis.html",
        mapillary_token=MAPILLARY_TOKEN,
        start_lat=start_lat,
        start_lng=start_lng
    )


@app.route("/api/uploads/all", methods=["GET"])
@login_required
def get_all_uploads_locations():
    """Get all upload locations for the map"""
    user_id = session.get('user_id')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all uploads with location data for the current user
    cur.execute("""
        SELECT id, filename, created_at, latitude, longitude
        FROM uploads
        WHERE user_id = ? AND latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY created_at DESC
    """, (user_id,))
    
    uploads = cur.fetchall()
    conn.close()
    
    upload_list = []
    for upload in uploads:
        upload_list.append({
            "id": upload[0],
            "filename": upload[1],
            "created_at": upload[2],
            "latitude": upload[3],
            "longitude": upload[4]
        })
    
    return jsonify({"uploads": upload_list})


@app.route("/api/uploads/search", methods=["POST"])
@login_required
def search_uploads_by_area():
    """Search uploads within a specific area of interest"""
    data = request.get_json()
    center_lat = data.get('latitude')
    center_lon = data.get('longitude')
    radius_km = data.get('radius', 10)  # Default 10km radius
    
    if center_lat is None or center_lon is None:
        return jsonify({"error": "Latitude and longitude required"}), 400
    
    try:
        center_lat = float(center_lat)
        center_lon = float(center_lon)
        radius_km = float(radius_km)
    except ValueError:
        return jsonify({"error": "Invalid numeric values"}), 400
    
    user_id = session.get('user_id')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all uploads with location data for the current user
    cur.execute("""
        SELECT id, filename, created_at, latitude, longitude
        FROM uploads
        WHERE user_id = ? AND latitude IS NOT NULL AND longitude IS NOT NULL
    """, (user_id,))
    
    uploads = cur.fetchall()
    conn.close()
    
    # Filter uploads within the radius using Haversine formula
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in kilometers"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    filtered_uploads = []
    for upload in uploads:
        distance = haversine_distance(center_lat, center_lon, upload[3], upload[4])
        if distance <= radius_km:
            filtered_uploads.append({
                "id": upload[0],
                "filename": upload[1],
                "created_at": upload[2],
                "latitude": upload[3],
                "longitude": upload[4],
                "distance": round(distance, 2)
            })
    
    # Sort by distance
    filtered_uploads.sort(key=lambda x: x['distance'])
    
    return jsonify({
        "uploads": filtered_uploads,
        "count": len(filtered_uploads),
        "search_params": {
            "latitude": center_lat,
            "longitude": center_lon,
            "radius_km": radius_km
        }
    })


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if "image" not in request.files:
        return jsonify({"error": "No image part in the request"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No image selected"}), 400

    lat = request.form.get("latitude")
    lon = request.form.get("longitude")

    try:
        latitude = float(lat) if lat else None
        longitude = float(lon) if lon else None
    except ValueError:
        return jsonify({"error": "Invalid latitude/longitude"}), 400

    image_bytes = file.read()
    filename = file.filename
    content_type = file.mimetype
    created_at = datetime.utcnow().isoformat()
    user_id = session.get('user_id')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO uploads (filename, content_type, image, latitude, longitude, created_at, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (filename, content_type, image_bytes, latitude, longitude, created_at, user_id),
    )
    conn.commit()
    upload_id = cur.lastrowid
    conn.close()

    return jsonify(
        {
            "message": "Upload successful",
            "id": upload_id,
            "filename": filename,
            "latitude": latitude,
            "longitude": longitude,
        }
    )


@app.route("/user/uploads", methods=["GET"])
@login_required
def get_user_uploads():
    user_id = session.get('user_id')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, filename, created_at, latitude, longitude, content_type
        FROM uploads
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    
    uploads = cur.fetchall()
    conn.close()
    
    upload_list = []
    for upload in uploads:
        upload_list.append({
            "id": upload[0],
            "filename": upload[1],
            "created_at": upload[2],
            "latitude": upload[3],
            "longitude": upload[4],
            "content_type": upload[5]
        })
    
    return jsonify({"uploads": upload_list})


@app.route("/image/<int:image_id>", methods=["GET"])
@login_required
def get_image(image_id):
    user_id = session.get('user_id')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Allow users to see only their own images, admins can see all
    if session.get('role') == 'admin':
        cur.execute("SELECT image, content_type FROM uploads WHERE id = ?", (image_id,))
    else:
        cur.execute("SELECT image, content_type FROM uploads WHERE id = ? AND user_id = ?", (image_id, user_id))
    
    result = cur.fetchone()
    conn.close()
    
    if result:
        from flask import Response
        return Response(result[0], mimetype=result[1])
    else:
        return jsonify({"error": "Image not found"}), 404


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all uploads with user info
    cur.execute("""
        SELECT uploads.id, uploads.filename, uploads.created_at, 
               uploads.latitude, uploads.longitude, users.username
        FROM uploads
        LEFT JOIN users ON uploads.user_id = users.id
        ORDER BY uploads.created_at DESC
    """)
    uploads = cur.fetchall()
    
    # Get all users
    cur.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC")
    users = cur.fetchall()
    
    conn.close()
    
    return render_template("admin_dashboard.html", uploads=uploads, users=users)


@app.route("/admin/delete_upload/<int:upload_id>", methods=["POST"])
@admin_required
def delete_upload(upload_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM uploads WHERE id = ?", (upload_id,))
    conn.commit()
    conn.close()
    flash("Upload deleted successfully")
    return redirect(url_for('admin_dashboard'))


@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        flash("You cannot delete your own account")
        return redirect(url_for('admin_dashboard'))
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully")
    return redirect(url_for('admin_dashboard'))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
