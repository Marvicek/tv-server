# -*- coding: utf-8 -*-
import sqlite3
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from core.utils import project_root, ensure_dir

DB_PATH = project_root() / "cache" / "logs" / "events.sqlite3"

def init_db():
    ensure_dir(DB_PATH.parent)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            ts_utc INTEGER NOT NULL,
            iso_utc TEXT NOT NULL,
            source TEXT,
            event TEXT,
            channel_id TEXT,
            payload_json TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts_utc)")
    con.commit()
    con.close()

def insert_event(source: str, event: str, channel_id: str = "", payload=None):
    ts = int(time.time())
    iso = datetime.utcfromtimestamp(ts).isoformat() + "Z"
    ev_id = str(uuid.uuid4())
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO events (id, ts_utc, iso_utc, source, event, channel_id, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ev_id, ts, iso, source, event, channel_id, json.dumps(payload, ensure_ascii=False)))
    con.commit()
    con.close()
    return ev_id

def recent(n: int = 50):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("""
        SELECT id, ts_utc, iso_utc, source, event, channel_id, payload_json
        FROM events ORDER BY ts_utc DESC LIMIT ?
    """, (int(n),))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    for r in rows:
        try:
            r["payload"] = json.loads(r.get("payload_json") or "{}")
        except Exception:
            r["payload"] = r.get("payload_json")
        r.pop("payload_json", None)
    return rows
