"""Photo loading, cropping, rounded masks and privacy treatment."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .config import BG_IMAGE, BROWN, H, LOGO, W

SS = 4  # supersampling for anti-aliased shapes


class Photo:
    """A photo reference from JSON: "file.jpg" or {"src": ..., "crop": [x0,y0,x1,y1], "focus": [fx,fy]}.
    crop is fractional (0-1) of the source image; focus is used when crop is absent."""

    def __init__(self, spec, base: Path):
        if isinstance(spec, str):
            spec = {"src": spec}
        self.src = (base / spec["src"]).resolve()
        self.crop = spec.get("crop")
        self.focus = spec.get("focus", [0.5, 0.35])
        if not self.src.exists():
            raise FileNotFoundError(f"photo not found: {self.src}")

    def load(self) -> Image.Image:
        return load(self.src)


@lru_cache(maxsize=64)
def load(path: Path) -> Image.Image:
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")


def cover(photo: Photo, w: int, h: int, scale: float = 1.0) -> Image.Image:
    """Return the photo filling a w x h box (cover). `scale` renders larger for zoom headroom."""
    im = photo.load()
    iw, ih = im.size
    if photo.crop:
        x0, y0, x1, y1 = photo.crop
        box = (x0 * iw, y0 * ih, x1 * iw, y1 * ih)
        bw, bh = box[2] - box[0], box[3] - box[1]
        # adjust to exact target aspect around the crop centre
        tgt = w / h
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if bw / bh > tgt:
            bw = bh * tgt
        else:
            bh = bw / tgt
        box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    else:
        tgt = w / h
        if iw / ih > tgt:
            bh, bw = ih, ih * tgt
        else:
            bw, bh = iw, iw / tgt
        fx, fy = photo.focus
        cx = min(max(fx * iw, bw / 2), iw - bw / 2)
        cy = min(max(fy * ih, bh / 2), ih - bh / 2)
        box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    out = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
    return im.resize(out, Image.LANCZOS, box=box)


def contain(path: Path, w: int, h: int) -> Image.Image:
    """Fit a logo inside w x h keeping alpha."""
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGBA")
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    k = min(w / im.width, h / im.height)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def rrect_mask(w: int, h: int, r: float, corners=(True, True, True, True)) -> Image.Image:
    """Anti-aliased rounded-rect mask. corners = (tl, tr, br, bl)."""
    m = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(m)
    R = int(r * SS)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=R, fill=255, corners=corners)
    return m.resize((w, h), Image.LANCZOS)


def fill_rrect(canvas: Image.Image, box, r: float, color, corners=(True, True, True, True)):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    # clip to canvas but keep shape geometry (corners outside canvas are cut off)
    w, h = x1 - x0, y1 - y0
    m = rrect_mask(w, h, r, corners) if r > 0 else Image.new("L", (w, h), 255)
    layer = Image.new("RGB", (w, h), color)
    canvas.paste(layer, (x0, y0), m)


def fill_circle(canvas: Image.Image, box, color):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    m = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(m).ellipse((0, 0, w * SS - 1, h * SS - 1), fill=255)
    canvas.paste(Image.new("RGB", (w, h), color), (x0, y0), m.resize((w, h), Image.LANCZOS))


def apply_privacy(im: Image.Image, mode: str) -> Image.Image:
    if mode == "blur":
        return im.filter(ImageFilter.GaussianBlur(radius=max(im.size) / 14))
    if mode == "hide":
        out = Image.new("RGB", im.size, BROWN)
        lg = contain(LOGO, int(im.width * 0.45), int(im.height * 0.45))
        out.paste(lg, ((im.width - lg.width) // 2, (im.height - lg.height) // 2), lg)
        return out
    return im


def paste_photo(canvas: Image.Image, photo: Photo, box, r: float, privacy: str = "clear"):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    im = apply_privacy(cover(photo, w, h), privacy)
    canvas.paste(im, (x0, y0), rrect_mask(w, h, r))


@lru_cache(maxsize=1)
def background() -> Image.Image:
    bg = Image.open(BG_IMAGE).convert("RGB")
    if bg.size != (W, H):
        bg = ImageOps.fit(bg, (W, H), Image.LANCZOS)
    return bg


@lru_cache(maxsize=4)
def logo(size: int) -> Image.Image:
    return contain(LOGO, size, size)
