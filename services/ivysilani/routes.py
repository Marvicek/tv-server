# -*- coding: utf-8 -*-
import time
import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bottle import Bottle, response, redirect, HTTPError, request

from core.utils import project_root

ivysilani_app = Bottle()

ONLINE_JSON_URL = "https://hbbtv.ceskatelevize.cz/online/services/data/online.json"

# In-memory cache (sdílené mezi playlistem, /play a web stránkou)
_cache_lock = threading.Lock()
_cache: Dict[str, Any] = {"ts": 0.0, "data": None, "error": None}

# Jak často se má stahovat online.json (30 minut)
FETCH_INTERVAL_SECONDS = 30 * 60


def load_config() -> Dict[str, Any]:
    cfg_path = Path(project_root()) / "config.json"
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def _encoder_whitelist(cfg: Dict[str, Any]) -> List[str]:
    return cfg.get("encoder_whitelist") or [
        "CH_25","CH_26","CH_27","CH_28","CH_29","CH_30","CH_31","CH_32",
        "CH_MOB_01",
        "CH_MP_01","CH_MP_02","CH_MP_03","CH_MP_04","CH_MP_05","CH_MP_06","CH_MP_07","CH_MP_08"
    ]


def refresh_online_json() -> None:
    """Stáhne online.json a uloží do cache (thread-safe)."""
    try:
        r = requests.get(ONLINE_JSON_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        with _cache_lock:
            _cache["ts"] = time.time()
            _cache["data"] = data
            _cache["error"] = None
    except Exception as e:
        with _cache_lock:
            _cache["error"] = str(e)


def get_online_json_cached() -> Any:
    """Vrátí cached data (a když ještě nic není, zkusí stáhnout hned)."""
    with _cache_lock:
        data = _cache.get("data")
    if data is None:
        refresh_online_json()
        with _cache_lock:
            data = _cache.get("data")
    return data


def start_background_updater() -> None:
    """Spustí background aktualizace každých 30 minut."""
    def loop():
        # hned první refresh
        refresh_online_json()
        while True:
            time.sleep(FETCH_INTERVAL_SECONDS)
            refresh_online_json()

    t = threading.Thread(target=loop, daemon=True)
    t.start()


def _pick_logo_id(item: Dict[str, Any]) -> str:
    if str(item.get("channel") or "").upper() == "SPORT_PLUS":
        return "ctsportplus"
    at = (item.get("assignmentType") or "").lower()
    if "ctsport" in at:
        return "ctsport"
    return "ivysilani"


def _format_time(item: Dict[str, Any]) -> str:
    # v online.json bývá time_str / time_end_str
    a = (item.get("time_str") or "").strip()
    b = (item.get("time_end_str") or "").strip()
    if a and b:
        return f"{a}–{b}"
    return a or b


@ivysilani_app.get("/playlist/ivysilani.m3u")
def playlist_ivysilani():
    cfg = load_config()
    base_url = (cfg.get("public_base_url") or f"{request.urlparts.scheme}://{request.urlparts.netloc}").rstrip("/")
    wl = set(_encoder_whitelist(cfg))

    data = get_online_json_cached()
    if data is None:
        raise HTTPError(502, "online.json not available")

    items: List[Dict[str, Any]] = []
    if isinstance(data, list):
        for it in data:
            enc = it.get("encoder")
            if not enc or enc not in wl:
                continue
            if str(it.get("isOnline", 0)) != "1":
                continue
            items.append(it)

    response.content_type = "audio/x-mpegurl; charset=utf-8"
    out = ["#EXTM3U"]

    for it in items:
        enc = it.get("encoder")
        title = it.get("programTitle") or it.get("title") or "iVysílání LIVE"
        logo_id = _pick_logo_id(it)

        tvg_logo = f"{base_url}/picon/ivysilani/{logo_id}.png"
        name = f"{title} ({enc})"
        stream_url = f"{base_url}/play/ivysilani/{enc}"

        out.append(f'#EXTINF:-1 tvg-id="{enc}" tvg-logo="{tvg_logo}" group-title="iVysílání LIVE",{name}')
        out.append(stream_url)

    return "\n".join(out) + "\n"


@ivysilani_app.get("/play/ivysilani/<encoder>")
def play_ivysilani_encoder(encoder):
    cfg = load_config()
    wl = set(_encoder_whitelist(cfg))
    if encoder not in wl:
        raise HTTPError(404, "Unknown encoder")

    data = get_online_json_cached()
    if isinstance(data, list):
        for it in data:
            if it.get("encoder") == encoder and str(it.get("isOnline", 0)) == "1":
                play_url = it.get("playUrl")
                if play_url:
                    return redirect(play_url)

    raise HTTPError(404, "Encoder not currently online")


@ivysilani_app.get("/ct/online")
def web_ct_online():
    """Jednoduchá web stránka s odkazy (ČT / iVysílání)."""
    cfg = load_config()
    base_url = (cfg.get("public_base_url") or f"{request.urlparts.scheme}://{request.urlparts.netloc}").rstrip("/")
    data = get_online_json_cached()

    with _cache_lock:
        ts = _cache.get("ts", 0.0)
        err = _cache.get("error")
    ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "n/a"

    rows = []
    if isinstance(data, list):
        for it in data:
            if str(it.get("isOnline", 0)) != "1":
                continue
            enc = it.get("encoder") or ""
            title = it.get("programTitle") or it.get("title") or "LIVE"
            when = _format_time(it)
            play_url = it.get("playUrl") or ""
            logo_id = _pick_logo_id(it)
            logo = f"{base_url}/picon/ivysilani/{logo_id}.png"
            local_play = f"{base_url}/play/ivysilani/{enc}" if enc else ""

            rows.append((logo, title, when, enc, local_play, play_url))

    response.content_type = "text/html; charset=utf-8"
    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'>")
    html.append("<title>ČT online.json – LIVE</title>")
    html.append("<style>body{font-family:Arial,Helvetica,sans-serif;margin:24px} table{border-collapse:collapse;width:100%} th,td{border:1px solid #ddd;padding:8px} th{background:#f3f3f3} img{height:28px}</style>")
    html.append("</head><body>")
    html.append("<h2>ČT – LIVE (online.json)</h2>")
    html.append(f"<p>Aktualizace: <b>{ts_str}</b> (interval {FETCH_INTERVAL_SECONDS//60} min)")
    if err:
        html.append(f"<br><span style='color:#b00'>Poslední chyba: {err}</span>")
    html.append("</p>")
    html.append(f"<p><a href='{base_url}/playlist/ivysilani.m3u'>Playlist: /playlist/ivysilani.m3u</a></p>")

    html.append("<table>")
    html.append("<tr><th>Logo</th><th>Název</th><th>Čas</th><th>Encoder</th><th>Odkaz (lokální)</th><th>Odkaz (ČT HbbTV)</th></tr>")
    for logo, title, when, enc, local_play, play_url in rows:
        html.append("<tr>")
        html.append(f"<td><img src='{logo}' alt='logo'></td>")
        html.append(f"<td>{title}</td>")
        html.append(f"<td>{when}</td>")
        html.append(f"<td>{enc}</td>")
        html.append(f"<td><a href='{local_play}'>play/{enc}</a></td>" if local_play else "<td></td>")
        html.append(f"<td><a href='{play_url}'>ČT playUrl</a></td>" if play_url else "<td></td>")
        html.append("</tr>")
    html.append("</table>")

    html.append("</body></html>")
    return "".join(html)
