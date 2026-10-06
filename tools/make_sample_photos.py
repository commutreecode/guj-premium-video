#!/usr/bin/env python3
"""Generate neutral placeholder 'photos' for samples/ (no real people)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "samples/photos"
SPECS = {"hero": (900, 1100, "#c9b8a6"), "g1": (1000, 1300, "#a9c1d6"), "g2": (1200, 900, "#b9d6a9"),
         "g3": (900, 1200, "#d6b9c9"), "elder_f": (700, 900, "#d8cdbf"), "elder_m": (700, 900, "#bfc8d8"),
         "mother": (700, 900, "#e0c8c8"), "father": (700, 900, "#c8d0e0"), "couple": (1000, 800, "#d0d8c8"),
         "edu": (600, 1000, "#cfd8e6"), "logo": (400, 400, None)}

def person(w, h, bg, n=1):
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    for i in range(n):
        cx = w * (i + 1) / (n + 1)
        r = min(w / (2.6 * n), h / 5)
        d.ellipse((cx - r, h * 0.28 - r, cx + r, h * 0.28 + r), fill="#7a6a5a")
        d.rounded_rectangle((cx - r * 1.7, h * 0.28 + r * 1.2, cx + r * 1.7, h + r), radius=r, fill="#5a6a7a")
    return im.filter(ImageFilter.GaussianBlur(2))

OUT.mkdir(parents=True, exist_ok=True)
for name, (w, h, bg) in SPECS.items():
    if name == "logo":
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((20, 20, w - 20, h - 20), outline="#2a7f62", width=24)
        d.text((w / 2, h / 2), "LOGO", fill="#2a7f62", anchor="mm", font_size=90)
        im.save(OUT / "logo.png")
    else:
        person(w, h, bg, 2 if name == "couple" else 1).save(OUT / f"{name}.jpg", quality=85)
print("written to", OUT)
