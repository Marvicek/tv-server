# -*- coding: utf-8 -*-
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.utils import project_root, sha1_text, ensure_dir

CANVAS = 1024
SAFE = 40


def _assets_dir() -> Path:
    return project_root() / "services" / "picons" / "assets"


def _cache_dir() -> Path:
    return ensure_dir(project_root() / "cache" / "picons")


def _load_mark_png(name: str) -> Image.Image:
    return Image.open(_assets_dir() / "marks" / name).convert("RGBA")


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


def _is_fully_opaque(img: Image.Image) -> bool:
    """True pokud je alpha všude 255 (tj. obrázek má vlastní pozadí)."""
    if img.mode != "RGBA":
        return True
    alpha = img.split()[-1]
    # getextrema returns (min,max)
    mn, mx = alpha.getextrema()
    return mn == 255 and mx == 255


def _paste_center_by_alpha(img: Image.Image, layer: Image.Image, scale: float = 1.0):
    """Centrovat podle viditelného obsahu (alpha bbox) – sedí jako reference ct1.png."""
    w, h = layer.size
    nw, nh = int(w * scale), int(h * scale)
    layer2 = layer.resize((nw, nh), Image.LANCZOS)

    alpha = layer2.split()[-1]
    bbox = alpha.getbbox()
    if not bbox:
        img.alpha_composite(layer2, ((CANVAS - nw) // 2, (CANVAS - nh) // 2))
        return

    l, t, r, b = bbox
    bw, bh = (r - l), (b - t)
    cx, cy = CANVAS // 2, CANVAS // 2
    x = int(cx - (l + bw / 2))
    y = int(cy - (t + bh / 2))
    img.alpha_composite(layer2, (x, y))


def _draw_ivysilani_text_bottom_right(img: Image.Image, text: str = "iVysílání"):
    d = ImageDraw.Draw(img)
    font = _font(46, bold=True)
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = CANVAS - tw - SAFE
    y = CANVAS - th - SAFE
    d.text((x, y), text, font=font, fill=(255, 255, 255, 255))


def _draw_iptv_text_bottom_left(img: Image.Image, color_hex: str = "#FFFFFF", scale: float = 0.8):
    """IPTV bez rámečku: jen čistý text vlevo dole."""
    d = ImageDraw.Draw(img)

    c = color_hex.lstrip("#")
    r = int(c[0:2], 16)
    g = int(c[2:4], 16)
    b = int(c[4:6], 16)
    col = (r, g, b, 255)

    font = _font(int(54 * scale), bold=True)
    text = "IPTV"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = SAFE
    y = CANVAS - th - SAFE
    d.text((x, y), text, font=font, fill=col)


def render_master_png(
    service: str,
    channel_id: str,
    bg_hex: str,
    mark_png_name: str,
    show_iptv_icon: bool = False,
    iptv_color_hex: str = "#FFFFFF",
    show_ivysilani_text: bool = False,
    ivysilani_text: str = "iVysílání",
) -> Path:
    """Vygeneruje master 1024×1024 (cache).

    - Pokud má `mark` vlastní plné pozadí (alpha všude 255), použije se mark jako základ (nezměníme barvy/gradienty).
    - Pokud je mark průhledný (typicky ct1 mark), použije se bg_hex a mark se vycentruje podle alpha bbox.
    """
    key = sha1_text("|".join([
        service, channel_id, bg_hex, mark_png_name,
        str(show_iptv_icon), iptv_color_hex,
        str(show_ivysilani_text), ivysilani_text
    ]))
    out = _cache_dir() / f"{service}_{channel_id}_{key}_1024.png"
    if out.exists():
        return out

    mark = _load_mark_png(mark_png_name)

    if _is_fully_opaque(mark):
        base = mark.resize((CANVAS, CANVAS), Image.LANCZOS)
    else:
        base = Image.new("RGBA", (CANVAS, CANVAS), bg_hex)
        _paste_center_by_alpha(base, mark, scale=1.0)

    if show_iptv_icon:
        _draw_iptv_text_bottom_left(base, color_hex=iptv_color_hex, scale=0.8)

    if show_ivysilani_text:
        _draw_ivysilani_text_bottom_right(base, text=ivysilani_text)

    base.save(out, "PNG")
    return out


def render_png_size(master_png: Path, size: int) -> Path:
    """Downscale master PNG do NxN (cache)."""
    size = max(64, min(2048, int(size)))
    key = sha1_text(f"{master_png.name}|{master_png.stat().st_mtime}|{size}")
    out = _cache_dir() / f"{master_png.stem}_{size}_{key}.png"
    if out.exists():
        return out

    img = Image.open(master_png).convert("RGBA")
    img2 = img.resize((size, size), Image.LANCZOS)
    img2.save(out, "PNG")
    return out
