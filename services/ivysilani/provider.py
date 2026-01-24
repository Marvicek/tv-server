# -*- coding: utf-8 -*-
from __future__ import annotations
import json, time, urllib.request
from typing import Dict, Tuple

_API_TMPL = "https://api.ceskatelevize.cz/video/v1/playlist-live/v1/stream-data/channel/{channel}?canPlayDrm=false&streamType={streamType}"
_UA = "Mozilla/5.0 (tv-server/ivysilani)"

_CACHE: Dict[Tuple[str, str], Tuple[str, float]] = {}
_TTL = 20

class IvysilaniError(RuntimeError):
    pass

def get_stream_url(channel: str, stream_type: str = "hls") -> str:
    stream_type = (stream_type or "hls").lower()
    if stream_type not in ("hls", "dash"):
        raise IvysilaniError(f"Unsupported stream_type: {stream_type}")

    now = time.time()
    key = (channel, stream_type)
    cached = _CACHE.get(key)
    if cached and cached[1] > now and cached[0]:
        return cached[0]

    req = urllib.request.Request(_API_TMPL.format(channel=channel, streamType=stream_type),
                                 headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise IvysilaniError(f"CT API fetch failed: {e}") from e

    try:
        j = json.loads(data)
    except Exception as e:
        raise IvysilaniError("CT API returned invalid JSON") from e

    url = (((j or {}).get("streamUrls") or {}).get("main")) or ""
    if not url:
        raise IvysilaniError("No streamUrls.main in response")

    _CACHE[key] = (url, now + _TTL)
    return url

def get_hls_url(channel: str) -> str:
    return get_stream_url(channel, "hls")

def get_dash_url(channel: str) -> str:
    return get_stream_url(channel, "dash")
