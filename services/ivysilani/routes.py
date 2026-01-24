# -*- coding: utf-8 -*-
from bottle import Bottle, response, redirect, request
import threading
import time

from services.ivysilani.provider import get_dash_url, get_hls_url, IvysilaniError
from services.ivysilani.streamhub import StreamHub
from services.ivysilani.hbbtv import current_program_title_for_encoder

ivysilani_app = Bottle()

LINEAR_CHANNELS = [
    ("CH_1",  "Česká Televize 1",      "cekatelevize1.png"),
    ("CH_2",  "Česká Televize2",       "cekatelevize2.png"),
    ("CH_4",  "Česká Televize Sport",  "cekatelevizesport.png"),
    ("CH_5",  "Česká Televize Déčko",  "cekatelevizedecko.png"),
    ("CH_6",  "Česká Televize Art",    "cekatelevizeart.png"),
    ("CH_24", "Česká Televize 24",     "cekatelevize24.png"),
]
LINEAR_IDS = {cid for cid, _, _ in LINEAR_CHANNELS}
LINEAR_NAME_BY_ID = {cid: name for cid, name, _ in LINEAR_CHANNELS}

NONLINEAR_CHANNELS = [
    ("CH_25",     "CT iVysilani+ 1"),
    ("CH_26",     "CT iVysilani+ 2"),
    ("CH_27",     "CT iVysilani+ 3"),
    ("CH_28",     "CT iVysilani+ 4"),
    ("CH_29",     "CT iVysilani+ 5"),
    ("CH_30",     "CT iVysilani+ 6"),
    ("CH_31",     "CT iVysilani+ 7"),
    ("CH_32",     "CT iVysilani+ 8"),
    ("CH_MOB_01", "CT iVysilani+ 9"),
    ("CH_MP_01",  "CT iVysilani+ 10"),
    ("CH_MP_02",  "CT iVysilani+ 11"),
    ("CH_MP_03",  "CT iVysilani+ 12"),
    ("CH_MP_04",  "CT iVysilani+ 13"),
    ("CH_MP_05",  "CT iVysilani+ 14"),
    ("CH_MP_06",  "CT iVysilani+ 15"),
    ("CH_MP_07",  "CT iVysilani+ 16"),
    ("CH_MP_08",  "CT iVysilani+ 17"),
]
NONLINEAR_IDS = {cid for cid, _ in NONLINEAR_CHANNELS}
NONLINEAR_BASE_NAME_BY_ID = {cid: name for cid, name in NONLINEAR_CHANNELS}
NONLINEAR_LOGO = "ctivysilani.png"

def _base_url() -> str:
    return request.urlparts.scheme + "://" + request.urlparts.netloc

def _logo_url(host: str, filename: str) -> str:
    return f"{host}/picon/ivysilani/{filename}"

# --- Linear autoswitch hub ---
_active_lock = threading.Lock()
_active_linear_id: str | None = None
_active_linear_hub: StreamHub | None = None

def _switch_linear_to(channel_id: str) -> StreamHub:
    global _active_linear_id, _active_linear_hub
    with _active_lock:
        if _active_linear_id == channel_id and _active_linear_hub is not None:
            return _active_linear_hub

        if _active_linear_hub is not None:
            try:
                _active_linear_hub.stop()
            except Exception:
                pass

        display_name = LINEAR_NAME_BY_ID.get(channel_id, channel_id)
        hls = get_hls_url(channel_id)
        hub = StreamHub(channel_id=channel_id, hls_url=hls, service_name=display_name, provider="ivysilani")
        hub.start()

        _active_linear_id = channel_id
        _active_linear_hub = hub
        return hub

# --- Nonlinear multi-active hubs ---
_nonlin_lock = threading.Lock()
_nonlin_hubs: dict[str, StreamHub] = {}
_nonlin_last_used: dict[str, float] = {}
NONLINEAR_IDLE_TIMEOUT = 60
MAX_NONLINEAR_ACTIVE = 12

def _cleanup_nonlin() -> None:
    now = time.time()
    with _nonlin_lock:
        for cid in list(_nonlin_hubs.keys()):
            hub = _nonlin_hubs.get(cid)
            last = _nonlin_last_used.get(cid, now)
            if hub is None:
                _nonlin_hubs.pop(cid, None)
                _nonlin_last_used.pop(cid, None)
                continue
            if hub.subscriber_count() == 0 and (now - last) > NONLINEAR_IDLE_TIMEOUT:
                try:
                    hub.stop()
                except Exception:
                    pass
                _nonlin_hubs.pop(cid, None)
                _nonlin_last_used.pop(cid, None)

def _get_or_start_nonlin(channel_id: str) -> StreamHub:
    _cleanup_nonlin()
    with _nonlin_lock:
        if channel_id in _nonlin_hubs:
            _nonlin_last_used[channel_id] = time.time()
            return _nonlin_hubs[channel_id]

        if len(_nonlin_hubs) >= MAX_NONLINEAR_ACTIVE:
            oldest = sorted(_nonlin_last_used.items(), key=lambda kv: kv[1])[0][0]
            hub = _nonlin_hubs.get(oldest)
            try:
                if hub:
                    hub.stop()
            except Exception:
                pass
            _nonlin_hubs.pop(oldest, None)
            _nonlin_last_used.pop(oldest, None)

        base_name = NONLINEAR_BASE_NAME_BY_ID.get(channel_id, channel_id)
        extra = current_program_title_for_encoder(channel_id)
        display_name = f"{base_name} - {extra}" if extra else base_name

        hls = get_hls_url(channel_id)
        hub = StreamHub(channel_id=channel_id, hls_url=hls, service_name=display_name, provider="ivysilani+")
        hub.start()

        _nonlin_hubs[channel_id] = hub
        _nonlin_last_used[channel_id] = time.time()
        return hub

@ivysilani_app.get("/")
def index():
    response.content_type = "application/json; charset=utf-8"
    with _active_lock:
        active_linear = _active_linear_id
        linear_since = _active_linear_hub.started_at if _active_linear_hub else None
    with _nonlin_lock:
        active_nonlin = sorted(list(_nonlin_hubs.keys()))
    return {
        "service": "ivysilani",
        "playlists": {
            "ts": "/ivysilani/ivysilani_ts.m3u",
            "dash": "/ivysilani/ivysilani_dash.m3u",
        },
        "linear_active": active_linear,
        "linear_since": linear_since,
        "nonlinear_active": active_nonlin,
        "note": "CH_1..CH_24 jsou lineární (1 aktivní stream, autoswitch). CH_25+ jsou iVysilani+ (multi-active).",
    }

@ivysilani_app.get("/ivysilani_ts.m3u")
def playlist_ts():
    host = _base_url()
    response.content_type = "audio/x-mpegurl; charset=utf-8"
    lines = ["#EXTM3U"]

    group_linear = "iVysílání"
    for cid, name, logo_file in LINEAR_CHANNELS:
        logo = _logo_url(host, logo_file)
        play_url = f"{host}/ivysilani/playts/{cid}"
        lines.append(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_linear}",{name}')
        lines.append(play_url)

    group_plus = "iVysilani+"
    plus_logo = _logo_url(host, NONLINEAR_LOGO)
    for cid, base_name in NONLINEAR_CHANNELS:
        extra = current_program_title_for_encoder(cid)
        name = f"{base_name} - {extra}" if extra else base_name
        play_url = f"{host}/ivysilani/playts/{cid}"
        lines.append(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{name}" tvg-logo="{plus_logo}" group-title="{group_plus}",{name}')
        lines.append(play_url)

    return "\n".join(lines) + "\n"

@ivysilani_app.get("/ivysilani_dash.m3u")
def playlist_dash():
    host = _base_url()
    response.content_type = "audio/x-mpegurl; charset=utf-8"
    lines = ["#EXTM3U"]

    group_linear = "iVysílání"
    for cid, name, logo_file in LINEAR_CHANNELS:
        logo = _logo_url(host, logo_file)
        play_url = f"{host}/ivysilani/playdash/{cid}"
        lines.append(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_linear}",{name}')
        lines.append(play_url)

    group_plus = "iVysilani+"
    plus_logo = _logo_url(host, NONLINEAR_LOGO)
    for cid, base_name in NONLINEAR_CHANNELS:
        extra = current_program_title_for_encoder(cid)
        name = f"{base_name} - {extra}" if extra else base_name
        play_url = f"{host}/ivysilani/playdash/{cid}"
        lines.append(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{name}" tvg-logo="{plus_logo}" group-title="{group_plus}",{name}')
        lines.append(play_url)

    return "\n".join(lines) + "\n"

@ivysilani_app.get("/playdash/<channel_id>")
def playdash(channel_id):
    try:
        url = get_dash_url(channel_id)
    except IvysilaniError:
        response.status = 502
        return "Stream unavailable"
    return redirect(url)

@ivysilani_app.get("/playts/<channel_id>")
def playts(channel_id):
    if channel_id in LINEAR_IDS:
        try:
            hub = _switch_linear_to(channel_id)
        except IvysilaniError:
            response.status = 502
            return "Stream unavailable"

    elif channel_id in NONLINEAR_IDS:
        try:
            hub = _get_or_start_nonlin(channel_id)
        except IvysilaniError:
            response.status = 502
            return "Stream unavailable"

    else:
        response.status = 404
        return "Unknown channel"

    q = hub.subscribe()
    response.content_type = "video/MP2T"
    response.set_header("Cache-Control", "no-store")

    def gen():
        try:
            while True:
                chunk = q.get()
                if not chunk:
                    break
                yield chunk
        finally:
            hub.unsubscribe(q)
            if channel_id in NONLINEAR_IDS:
                with _nonlin_lock:
                    _nonlin_last_used[channel_id] = time.time()
                _cleanup_nonlin()

    return gen()
