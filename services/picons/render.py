# -*- coding: utf-8 -*-
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.utils import project_root, sha1_text, ensure_dir

CANVAS = 1024
SAFE = 40  # closer to edge, like your reference


def _assets_dir() -> Path:
    return project_root() / "services" / "picons" / "assets"


def _cache_dir() -> Path:
    return ensure_dir(project_root() / "cache" / "picons")


def _load_mark_png(name: str) -> Image.Image:
    p = _assets_dir() / "marks" / name
    return Image.open(p).convert("RGBA")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    candidates += [
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        try:
            if os.path.exists(c):
                return ImageFont.truetype(c, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _paste_center_by_alpha(img: Image.Image, layer: Image.Image, scale: float = 1.0):
    w, h = layer.size
    nw, nh = int(w * scale), int(h * scale)
    layer2 = layer.resize((nw, nh), Image.LANCZOS)

    alpha = layer2.split()[-1]
    bbox = alpha.getbbox()
    if not bbox:
        x = (CANVAS - nw) // 2
        y = (CANVAS - nh) // 2
        img.alpha_composite(layer2, (x, y))
        return

    l, t, r, b = bbox
    bw, bh = (r - l), (b - t)
    cx, cy = CANVAS // 2, CANVAS // 2
    x = int(cx - (l + bw / 2))
    y = int(cy - (t + bh / 2))
    img.alpha_composite(layer2, (x, y))


def _draw_ivysilani_text_bottom_right(img: Image.Image, text: str = "iVysílání"):
    draw = ImageDraw.Draw(img)
    font = _font(46, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = CANVAS - tw - SAFE
    y = CANVAS - th - SAFE
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))


def _draw_iptv_icon_bottom_left(img: Image.Image, color_hex: str = "#E31E24", scale: float = 0.8):
    w0, h0 = 180, 110
    w, h = int(w0 * scale), int(h0 * scale)
    stroke = max(4, int(6 * scale))

    icon = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(icon)

    color_hex = color_hex.lstrip("#")
    r = int(color_hex[0:2], 16)
    g = int(color_hex[2:4], 16)
    b = int(color_hex[4:6], 16)
    col = (r, g, b, 255)

    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(18 * scale), outline=col, width=stroke)

    font = _font(int(44 * scale), bold=True)
    text = "IPTV"
    tb = d.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = (w - tw) // 2
    ty = (h - th) // 2 - int(2 * scale)
    d.text((tx, ty), text, font=font, fill=col)

    x = SAFE
    y = CANVAS - h - SAFE
    img.alpha_composite(icon, (x, y))


def render_master_png(
    service: str,
    channel_id: str,
    bg_hex: str,
    mark_png_name: str,
    show_iptv_icon: bool = False,
    iptv_color_hex: str = "#E31E24",
    show_ivysilani_text: bool = False,
    ivysilani_text: str = "iVysílání",
) -> Path:
    key = sha1_text("|".join([service, channel_id, bg_hex, mark_png_name, str(show_iptv_icon), iptv_color_hex,
                              str(show_ivysilani_text), ivysilani_text]))
    out = _cache_dir() / f"{service}_{channel_id}_{key}_1024.png"
    if out.exists():
        return out

    canvas = Image.new("RGBA", (CANVAS, CANVAS), bg_hex)

    mark = _load_mark_png(mark_png_name)
    _paste_center_by_alpha(canvas, mark, scale=1.0)

    if show_iptv_icon:
        _draw_iptv_icon_bottom_left(canvas, color_hex=iptv_color_hex, scale=0.8)

    if show_ivysilani_text:
        _draw_ivysilani_text_bottom_right(canvas, text=ivysilani_text)

    canvas.save(out, "PNG")
    return out


def render_png_size(master_png: Path, size: int) -> Path:
    size = max(64, min(2048, int(size)))
    key = sha1_text(f"{master_png.name}|{master_png.stat().st_mtime}|{size}")
    out = _cache_dir() / f"{master_png.stem}_{size}_{key}.png"
    if out.exists():
        return out
    img = Image.open(master_png).convert("RGBA")
    img2 = img.resize((size, size), Image.LANCZOS)
    img2.save(out, "PNG")
    return out
