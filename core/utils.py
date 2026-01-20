# -*- coding: utf-8 -*-
import json
import hashlib
from pathlib import Path

def project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def load_json(path: Path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p
