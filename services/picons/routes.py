# -*- coding: utf-8 -*-
from bottle import Bottle, request, response, static_file
from core.utils import project_root, load_json
from services.picons.render import render_master_png, render_png_size

picons_app = Bottle()

def _cfg():
    return load_json(project_root() / "config.json", default={}) or {}

@picons_app.get("/<channel>.png")
def picon(channel):
    cfg = _cfg()
    ch = (cfg.get("channels") or {}).get(channel) or {}

    src = request.query.get("src") or ch.get("source") or ""
    q = request.query.get("q") or ch.get("quality") or ""
    size = request.query.get("size") or ""

    bg = ch.get("bg", "#444444")
    mark = ch.get("mark_png", "ct_mark_cropped.png")
    badge = None
    badges = (cfg.get("badges") or {})
    if src and isinstance(badges, dict):
        badge = badges.get(src) or badges.get(src.lower())

    master = render_master_png(
        channel_id=channel,
        bg_hex=bg,
        mark_png_name=mark,
        quality=q,
        badge_svg_name=badge,
        watermark=cfg.get("watermark", "MarvicekLogo"),
    )

    out = master
    if size:
        out = render_png_size(master, int(size))

    response.set_header("Cache-Control", "public, max-age=86400")
    return static_file(out.name, root=str(out.parent), mimetype="image/png")
