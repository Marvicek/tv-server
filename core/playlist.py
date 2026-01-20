# -*- coding: utf-8 -*-
from bottle import Bottle, response, redirect
from core.utils import project_root, load_json

playlist_app = Bottle()

def _cfg():
    return load_json(project_root() / "config.json", default={}) or {}

@playlist_app.get("/")
def index():
    cfg = _cfg()
    response.content_type = "application/json; charset=utf-8"
    return {
        "name": "IPTV Web Server (simple)",
        "endpoints": {
            "playlist": "/playlist/<service>.m3u",
            "play": "/play/<service>/<channel_id>",
            "picon": "/picon/<service>/<channel>.png",
            "logs": "/logs"
        },
        "services": list((cfg.get("services") or {}).keys()),
        "channels": list((cfg.get("channels") or {}).keys()),
    }

@playlist_app.get("/playlist/<service>.m3u")
def playlist(service):
    cfg = _cfg()
    services = cfg.get("services") or {}
    if service not in services:
        response.status = 404
        return "Unknown service"

    host = cfg.get("public_base_url", "http://127.0.0.1:8080").rstrip("/")
    response.content_type = "audio/x-mpegurl; charset=utf-8"
    lines = ["#EXTM3U"]

    channels = cfg.get("channels") or {}
    for ch_id, ch in channels.items():
        name = ch.get("name", ch_id)
        group = ch.get("group", "TV")
        tvg_id = ch.get("tvg_id", ch_id)

        logo = f"{host}/picon/{service}/{ch_id}.png"
        play_url = f"{host}/play/{service}/{ch_id}"

        extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}'
        lines.append(extinf)
        lines.append(play_url)

    return "\n".join(lines) + "\n"

@playlist_app.get("/play/<service>/<channel_id>")
def play(service, channel_id):
    cfg = _cfg()
    services = cfg.get("services") or {}
    svc = services.get(service) or {}
    streams = svc.get("streams") or {}
    url = streams.get(channel_id)
    if not url:
        ch = (cfg.get("channels") or {}).get(channel_id) or {}
        url = ch.get("url")
    if not url:
        return redirect("/")
    return redirect(url)
