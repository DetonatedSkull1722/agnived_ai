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
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            description TEXT NOT NULL,
            labels TEXT NOT NULL  -- comma-separated labels
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
        desc = request.form["description"].strip()
        # Get all selected checkboxes: name="labels"
        selected_labels = request.form.getlist("labels")
        labels_str = ",".join(selected_labels)  # e.g. "home,food"

        if lat and lng and desc:
            cur.execute(
                "INSERT INTO locations (lat, lng, description, labels) VALUES (?, ?, ?, ?)",
                (lat, lng, desc, labels_str)
            )
            conn.commit()

        conn.close()
        return redirect("/")

    cur.execute("SELECT lat, lng, description, labels FROM locations")
    locations = cur.fetchall()
    conn.close()

    # Pass to template: list of tuples -> Jinja will JSON it later
    return render_template("index.html", locations=locations)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
