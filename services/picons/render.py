# -*- coding: utf-8 -*-
import io
import os
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
import cairosvg

from core.utils import project_root, sha1_text, ensure_dir

CANVAS = 1024  # master render
DEFAULT_RADIUS = 96

def _assets_dir() -> Path:
    return project_root() / "services" / "picons" / "assets"

def _cache_dir() -> Path:
    return ensure_dir(project_root() / "cache" / "picons")

def _load_mark_png(name: str) -> Image.Image:
    p = _assets_dir() / "marks" / name
    return Image.open(p).convert("RGBA")

def _render_svg_to_png_bytes(svg_path: Path, out_px: int = 256) -> bytes:
    svg_bytes = svg_path.read_bytes()
    return cairosvg.svg2png(bytestring=svg_bytes, output_width=out_px, output_height=out_px)

def _load_badge_svg_as_image(name: str, size_px: int = 256) -> Image.Image:
    svg_path = _assets_dir() / "badges" / name
    png_bytes = _render_svg_to_png_bytes(svg_path, out_px=size_px)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")

def _rounded_rect_mask(w: int, h: int, r: int) -> Image.Image:
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, w, h], radius=r, fill=255)
    return mask

def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
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

def _draw_quality_badge(img: Image.Image, text: str):
    if not text:
        return
    draw = ImageDraw.Draw(img)
    font = _font(56)
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 28, 18
    box_w = w + pad_x * 2
    box_h = h + pad_y * 2

    x = CANVAS - box_w - 80
    y = 80

    badge = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([0, 0, box_w, box_h], radius=32, fill=(0, 0, 0, 115))
    bd.text((pad_x, pad_y - 4), text, font=font, fill=(255, 255, 255, 255))
    img.alpha_composite(badge, (x, y))

def _draw_watermark(img: Image.Image, text: str = "MarvicekLogo"):
    draw = ImageDraw.Draw(img)
    font = _font(36)
    draw.text((64, CANVAS - 80), text, font=font, fill=(255, 255, 255, 64))

def _paste_center(img: Image.Image, layer: Image.Image, scale: float = 1.0, y_offset: int = 0):
    w, h = layer.size
    nw, nh = int(w * scale), int(h * scale)
    layer2 = layer.resize((nw, nh), Image.LANCZOS)
    x = (CANVAS - nw) // 2
    y = (CANVAS - nh) // 2 + y_offset
    img.alpha_composite(layer2, (x, y))

def _paste_bottom_right(img: Image.Image, layer: Image.Image, pad: Tuple[int, int] = (80, 80), scale: float = 1.0):
    w, h = layer.size
    nw, nh = int(w * scale), int(h * scale)
    layer2 = layer.resize((nw, nh), Image.LANCZOS)
    x = CANVAS - nw - pad[0]
    y = CANVAS - nh - pad[1]
    img.alpha_composite(layer2, (x, y))

def render_master_png(
    channel_id: str,
    bg_hex: str,
    mark_png_name: str,
    quality: str = "",
    badge_svg_name: Optional[str] = None,
    watermark: str = "MarvicekLogo",
) -> Path:
    key = sha1_text("|".join([channel_id, bg_hex, mark_png_name, quality or "", badge_svg_name or "", watermark]))
    out = _cache_dir() / f"{channel_id}_{key}_1024.png"
    if out.exists():
        return out

    bg = Image.new("RGBA", (CANVAS, CANVAS), bg_hex)
    mask = _rounded_rect_mask(CANVAS, CANVAS, DEFAULT_RADIUS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(bg, (0, 0), mask=mask)

    mark = _load_mark_png(mark_png_name)
    _paste_center(canvas, mark, scale=1.8, y_offset=10)

    _draw_quality_badge(canvas, quality)

    if badge_svg_name:
        badge_img = _load_badge_svg_as_image(badge_svg_name, size_px=320)
        pill_w, pill_h = 360, 160
        pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle([0, 0, pill_w, pill_h], radius=42, fill=(0, 0, 0, 90))
        bx, by = (pill_w - badge_img.size[0]) // 2, (pill_h - badge_img.size[1]) // 2
        pill.alpha_composite(badge_img, (bx, by))
        _paste_bottom_right(canvas, pill, pad=(80, 80), scale=1.0)

    if watermark:
        _draw_watermark(canvas, watermark)

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
