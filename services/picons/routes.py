# -*- coding: utf-8 -*-
from bottle import Bottle, request, response, static_file
from core.utils import project_root, load_json
from services.picons.render import render_master_png, render_png_size

picons_app = Bottle()

def _cfg():
    return load_json(project_root() / "config.json", default={}) or {}

@picons_app.get("/<service>/<channel>.png")
def picon(service, channel):
    cfg = _cfg()
    services = cfg.get("services") or {}
    channels = cfg.get("channels") or {}

    if service not in services or channel not in channels:
        response.status = 404
        return "Not found"

    svc = services.get(service) or {}
    ch = channels.get(channel) or {}

    bg = ch.get("bg", svc.get("bg", "#444444"))
    mark = ch.get("mark_png", "ct_mark_cropped.png")

    show_iptv = bool(svc.get("iptv_icon", False))
    show_ivys = bool(svc.get("ivysilani_text", False))
    ivys_text = svc.get("ivysilani_label", "iVysílání")
    iptv_color = svc.get("iptv_color", bg)

    size = request.query.get("size") or ""

    master = render_master_png(
        service=service,
        channel_id=channel,
        bg_hex=bg,
        mark_png_name=mark,
                show_iptv_icon=show_iptv,
        iptv_color_hex=iptv_color,
        show_ivysilani_text=show_ivys,
        ivysilani_text=ivys_text,
    )

    out = master
    if size:
        out = render_png_size(master, int(size))

    response.set_header("Cache-Control", "public, max-age=86400")
    return static_file(out.name, root=str(out.parent), mimetype="image/png")
