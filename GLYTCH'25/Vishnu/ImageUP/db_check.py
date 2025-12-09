import sqlite3

conn = sqlite3.connect("uploads.db")
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

# Print the results in CMD
for row in uploads:
    print(row)

conn.close()
