from flask import Flask, render_template, request, redirect
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB = Path("locations.db")

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lng REAL,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    if request.method == "POST":
        lat = request.form["lat"]
        lng = request.form["lng"]
        desc = request.form["description"]

        cur.execute(
            "INSERT INTO locations (lat, lng, description) VALUES (?, ?, ?)",
            (lat, lng, desc)
        )
        conn.commit()
        return redirect("/")

    cur.execute("SELECT lat, lng, description FROM locations")
    locations = cur.fetchall()
    conn.close()

    return render_template("index.html", locations=locations)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
