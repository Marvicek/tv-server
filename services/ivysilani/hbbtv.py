# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import time
import urllib.request
from typing import Dict, Any, List, Optional

ONLINE_JSON_URL = "https://hbbtv.ceskatelevize.cz/online/services/data/online.json"
_UA = "Mozilla/5.0 (tv-server/ivysilani)"

_cache: Dict[str, Any] = {"ts": 0.0, "data": None}

def fetch_online_json(ttl_seconds: int = 10) -> List[dict]:
    now = time.time()
    if _cache["data"] is not None and (now - float(_cache["ts"])) < ttl_seconds:
        return _cache["data"]

    req = urllib.request.Request(ONLINE_JSON_URL, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    if not isinstance(data, list):
        data = []
    _cache["ts"] = now
    _cache["data"] = data
    return data

def current_program_title_for_encoder(encoder_id: str) -> Optional[str]:
    try:
        items = fetch_online_json()
    except Exception:
        return None

    for it in items:
        try:
            if str(it.get("encoder")) == encoder_id and int(it.get("isOnline", 0)) == 1 and int(it.get("isLive", 0)) == 1:
                title = (it.get("programTitle") or "").strip()
                return title or None
        except Exception:
            continue

    for it in items:
        try:
            if str(it.get("encoder")) == encoder_id:
                title = (it.get("programTitle") or "").strip()
                return title or None
        except Exception:
            continue

    return None
