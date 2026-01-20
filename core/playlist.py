# -*- coding: utf-8 -*-
from bottle import Bottle, response, redirect
from core.utils import project_root, load_json

playlist_app = Bottle()

def _cfg():
    return load_json(project_root() / "config.json", default={}) or {}

@playlist_app.get("/")
def index():
    response.content_type = "application/json; charset=utf-8"
    cfg = _cfg()
    return {
        "name": "IPTV Web Server (Bottle)",
        "endpoints": {
            "playlist": "/playlist.m3u",
            "play": "/play/<provider>/<channel_id>",
            "picon": "/picon/<channel>.png",
            "logs": "/logs",
        },
        "providers": list((cfg.get("providers") or {}).keys()),
        "channels": list((cfg.get("channels") or {}).keys()),
    }

@playlist_app.get("/playlist.m3u")
def playlist():
    cfg = _cfg()
    host = cfg.get("public_base_url", "http://127.0.0.1:8080").rstrip("/")

    response.content_type = "audio/x-mpegurl; charset=utf-8"
    lines = ["#EXTM3U"]

    channels = cfg.get("channels") or {}
    for ch_id, ch in channels.items():
        name = ch.get("name", ch_id)
        group = ch.get("group", "TV")
        tvg_id = ch.get("tvg_id", ch_id)
        src = ch.get("source", "demo")
        q = ch.get("quality", "")

        logo = f"{host}/picon/{ch_id}.png?src={src}&q={q}".rstrip("&q=")
        play_url = f"{host}/play/{src}/{ch_id}"

        extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}'
        lines.append(extinf)
        lines.append(play_url)

    return "\n".join(lines) + "\n"

@playlist_app.get("/play/<provider>/<channel_id>")
def play(provider, channel_id):
    cfg = _cfg()
    ch = (cfg.get("channels") or {}).get(channel_id) or {}

    url = None
    urls = ch.get("urls") or {}
    if isinstance(urls, dict):
        url = urls.get(provider)
    if not url:
        url = ch.get("url")
    if not url:
        return redirect("/")
    return redirect(url)
