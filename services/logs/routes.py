# -*- coding: utf-8 -*-
from bottle import Bottle, request, response
from services.logs.storage import init_db, insert_event, recent

logs_app = Bottle()
init_db()

@logs_app.get("/")
def help():
    return {
        "endpoints": {
            "POST /logs/ingest": "send JSON event",
            "GET /logs/recent?n=50": "recent events",
        }
    }

@logs_app.post("/ingest")
def ingest():
    data = request.json or {}
    source = data.get("source", "")
    event = data.get("event", "event")
    channel_id = data.get("channel_id", "")
    payload = data.get("payload", data)
    ev_id = insert_event(source, event, channel_id, payload)
    response.content_type = "application/json; charset=utf-8"
    return {"ok": True, "id": ev_id}

@logs_app.get("/recent")
def recent_route():
    n = int(request.query.get("n", 50))
    response.content_type = "application/json; charset=utf-8"
    return {"events": recent(n)}
