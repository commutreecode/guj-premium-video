"""Photo loading, cropping, rounded masks and privacy treatment."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .config import BG_IMAGE, BROWN, FRAMING, H, LOGO, W

try:  # face detection for automatic head-to-chest framing (pip install opencv-python-headless)
    import cv2
    import numpy as np
    _MODELS = Path(__file__).resolve().parent.parent / "assets/models"
    _NET = cv2.dnn.readNetFromCaffe(str(_MODELS / "deploy.prototxt"),
                                    str(_MODELS / "res10_300x300_ssd_iter_140000.caffemodel"))
    _CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
except Exception:  # pragma: no cover - framing falls back to a fixed focus point
    cv2 = None

try:  # iPhone HEIC photos from the form (optional: pip install pillow-heif)
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

SS = 4  # supersampling for anti-aliased shapes


class Photo:
    """A photo reference from JSON: "file.jpg" or {"src": ..., "crop": [x0,y0,x1,y1], "focus": [fx,fy]}.
    crop is fractional (0-1) of the source image; focus is used when crop is absent."""

    def __init__(self, spec, base: Path):
        if isinstance(spec, str):
            spec = {"src": spec}
        self.src = (base / spec["src"]).resolve()
        self.crop = spec.get("crop")
        self.focus = spec.get("focus")          # None = automatic (face detection)
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


def _dnn(img):
    h, w = img.shape[:2]
    _NET.setInput(cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104, 177, 123)))
    return [(d[3] * w, d[4] * h, d[5] * w, d[6] * h, float(d[2])) for d in _NET.forward()[0, 0]]


@lru_cache(maxsize=128)
def faces(path: Path) -> tuple:
    """Face boxes (x0, y0, x1, y1) in source pixels. OpenCV DNN detector on square tiles along the long
    side (small faces in tall photos) + the whole image; Haar cascade fallback; background faces dropped."""
    if cv2 is None:
        return ()
    im = load(path)
    k = min(1.0, 1200 / max(im.size))
    small = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))))
    bgr = cv2.cvtColor(np.asarray(small), cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    side, tall = min(h, w), h > w
    n = max(1, int(np.ceil((max(h, w) - side) / (side * 0.5))) + 1)
    boxes = []
    for i in range(n):
        o = int(round(i * (max(h, w) - side) / max(1, n - 1)))
        tile = bgr[o:o + side, :] if tall else bgr[:, o:o + side]
        for x0, y0, x1, y1, c in _dnn(tile):
            lo, hi = (y0, y1) if tall else (x0, x1)
            if (o > 0 and lo <= 2) or (o + side < max(h, w) and hi >= side - 2):
                continue                      # face cut by the tile edge: the other tile has it whole
            boxes.append((x0, y0 + o, x1, y1 + o, c) if tall else (x0 + o, y0, x1 + o, y1, c))
    boxes += _dnn(bgr)
    boxes = [b for b in boxes if b[4] > 0.6 and b[2] > b[0] and b[3] > b[1]]
    if boxes:
        r = [[int(b[0]), int(b[1]), int(b[2] - b[0]), int(b[3] - b[1])] for b in boxes]
        keep = np.array(cv2.dnn.NMSBoxes(r, [b[4] for b in boxes], 0.6, 0.3)).flatten()
        found = [boxes[i][:4] for i in keep]
    else:                                     # e.g. sunglasses / side face: Haar, largest face only
        g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        m = max(24, int(0.04 * min(g.shape)))
        hs = _CASCADE.detectMultiScale(g, scaleFactor=1.1, minNeighbors=6, minSize=(m, m))
        found = [max(((x, y, x + fw, y + fh) for x, y, fw, fh in hs), key=lambda b: b[3] - b[1])] if len(hs) else []
    if not found:
        return ()
    big = max(b[3] - b[1] for b in found)
    return tuple((b[0] / k, b[1] / k, b[2] / k, b[3] / k) for b in found if b[3] - b[1] >= 0.4 * big)


def smart_box(photo: Photo, im: Image.Image, w: int, h: int, max_upscale: float | None = None):
    """Source box that frames the face(s) head-to-chest in a w x h frame, plus the zoom anchor
    (between face and chest). Returns (box, anchor) or (None, None) when no face is found."""
    fs = faces(photo.src)
    if not fs:
        return None, None
    iw, ih = im.size
    tgt = w / h
    ux0, uy0 = min(f[0] for f in fs), min(f[1] for f in fs)
    ux1, uy1 = max(f[2] for f in fs), max(f[3] for f in fs)
    fh = sum(f[3] - f[1] for f in fs) / len(fs)
    top = uy0 - FRAMING["headroom"] * fh
    ch = max(fh / FRAMING["face_frac"], (uy1 + 1.2 * fh) - top)        # down to the chest
    cw = ch * tgt
    if cw < (ux1 - ux0) + 1.0 * fh:                                     # several faces side by side
        cw = (ux1 - ux0) + 1.0 * fh
        ch = cw / tgt
    min_h = h / (max_upscale or FRAMING["max_upscale"])                # keep the photo sharp
    if ch < min_h:
        grow = min_h - ch
        top -= grow * 0.3
        ch, cw = min_h, min_h * tgt
    f = min(1.0, iw / cw, ih / ch)                                      # never larger than the photo
    cw, ch = cw * f, ch * f
    cw, ch = min(cw, iw), min(ch, ih)                                   # float safety
    cx = (ux0 + ux1) / 2
    x0 = max(0.0, min(cx - cw / 2, iw - cw))
    y0 = max(0.0, min(top, ih - ch))
    anchor = (cx, (uy0 + uy1) / 2 + 0.5 * fh)
    return (x0, y0, x0 + cw, y0 + ch), anchor


def cover_anchor(photo: Photo, w: int, h: int, scale: float = 1.0):
    """Like cover(), also returns the zoom anchor in output pixels (w x h space)."""
    im = photo.load()
    box, anchor = (None, None)
    if not photo.crop and photo.focus is None:
        box, anchor = smart_box(photo, im, w, h)
    if box is None:
        return cover(photo, w, h, scale), (w / 2, h / 2)
    out = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
    ax = (anchor[0] - box[0]) / (box[2] - box[0]) * w
    ay = (anchor[1] - box[1]) / (box[3] - box[1]) * h
    return im.resize(out, Image.LANCZOS, box=box), (min(max(ax, 0), w), min(max(ay, 0), h))


def cover_reserve(photo: Photo, w: int, h: int, reserve: int, scale: float = 1.0, max_upscale: float | None = None):
    """Photo for a w x h area whose top `reserve` px sit under a title bar: the face is framed head to chest
    in the visible part below the bar (same size as a (h - reserve) area), and the photo continues up
    behind the bar. If the source has too little above the head, the photo starts lower (dy > 0) so the
    face still stays below the bar. Returns (image of size (w, h - dy) * scale, zoom anchor in that image, dy)."""
    im = photo.load()
    box, anchor = (None, None)
    if not photo.crop and photo.focus is None:
        box, anchor = smart_box(photo, im, w, h - reserve, max_upscale)
    if box is None:
        return cover(photo, w, h, scale), (w / 2, h / 2), 0
    x0, y0, x1, y1 = box
    k = (y1 - y0) / (h - reserve)            # source px per output px
    ny0 = y0 - reserve * k
    dy = 0
    if ny0 < 0:                              # not enough photo above the head: start the photo lower
        dy = int(round(-ny0 / k))
        ny0 = 0.0
    hh = h - dy
    ny1 = min(float(im.height), ny0 + hh * k)
    box = (x0, ny0, x1, ny1)
    out = (max(1, int(round(w * scale))), max(1, int(round(hh * scale))))
    ax = (anchor[0] - x0) / (x1 - x0) * w
    ay = (anchor[1] - ny0) / (ny1 - ny0) * hh
    return im.resize(out, Image.LANCZOS, box=box), (min(max(ax, 0), w), min(max(ay, 0), hh)), dy


def cover(photo: Photo, w: int, h: int, scale: float = 1.0) -> Image.Image:
    """Return the photo filling a w x h box (cover). `scale` renders larger for zoom headroom.
    Without crop/focus in the JSON, faces are detected and framed head to chest."""
    im = photo.load()
    iw, ih = im.size
    if not photo.crop and photo.focus is None:
        box, _ = smart_box(photo, im, w, h)
        if box is not None:
            out = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
            return im.resize(out, Image.LANCZOS, box=box)
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
        fx, fy = photo.focus or (0.5, 0.35)
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
