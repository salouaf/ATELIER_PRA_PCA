import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request

DB_PATH = os.getenv("DB_PATH", "/data/app.db")

app = Flask(__name__)

# ---------- DB helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- Routes ----------

@app.get("/")
def hello():
    init_db()
    return jsonify(status="Bonjour tout le monde !")


@app.get("/health")
def health():
    init_db()
    return jsonify(status="ok")

@app.get("/add")
def add():
    init_db()

    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"

    conn = get_conn()
    conn.execute(
        "INSERT INTO events (ts, message) VALUES (?, ?)",
        (ts, msg)
    )
    conn.commit()
    conn.close()

    return jsonify(
        status="added",
        timestamp=ts,
        message=msg
    )

@app.get("/consultation")
def consultation():
    init_db()

    conn = get_conn()
    cur = conn.execute(
        "SELECT id, ts, message FROM events ORDER BY id DESC LIMIT 50"
    )

    rows = [
        {"id": r[0], "timestamp": r[1], "message": r[2]}
        for r in cur.fetchall()
    ]

    conn.close()

    return jsonify(rows)

@app.get("/count")
def count():
    init_db()

    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()

    return jsonify(count=n)

@app.route('/status')
def get_status():
    import time
# 1. Compter les événements
    try:
        conn = get_conn()
        cur = conn.execute("SELECT COUNT(*) FROM events")
        n = cur.fetchone()[0]
        conn.close()
    except:
        n = 0

# 2. Chercher le backup
    backup_dir = "/backup"
    file_name = "Aucun"
    age = "N/A"

    if os.path.exists(backup_dir):
        files = [f for f in os.listdir(backup_dir) if os.path.isfile(os.path.join(backup_dir, f))]
        if files:
            full_paths = [os.path.join(backup_dir, f) for f in files]
            latest = max(full_paths, key=os.path.getmtime)
            file_name = os.path.basename(latest)
            age = int(time.time() - os.path.getmtime(latest))

    return jsonify(count=n, last_backup_file=file_name, backup_age_seconds=age)

# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
