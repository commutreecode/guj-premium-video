"""Static cards (1200x1500 RGB). Coordinates/baselines come from the PSD templates."""
from __future__ import annotations

from PIL import Image, ImageDraw

from . import imgs
from .config import BLACK, BROWN, DARK, H, NEAR_BLACK, THEMES, W, WHITE
from .text import Style, draw_line, fit, measure, wrap_balanced, wrap_fit

HEADER_TEXT = "કોમ્યુટ્રી CT પ્રિમિયમ મેમ્બર"
INTRO_LINES = ["કોમ્યુટ્રી CT", "પ્રિમિયમ મેમ્બર"]
TITLE_FAMILY = "પરિવાર પરિચય"

SIBLING_TITLES = {
    "bahen-banevi": "બહેન - બનેવી",
    "bhai-bhabhi": "ભાઈ - ભાભી",
    "mota-bhai-bhabhi": "મોટા ભાઈ - ભાભી",
    "bhai": "ભાઈ",
    "bahen": "બહેન",
}


class Ctx:
    def __init__(self, theme: str, base, privacy: str = "clear"):
        self.theme = theme
        self.accent = THEMES[theme]["accent"]
        self.job_bullet = THEMES[theme]["job_bullet"]
        self.base = base
        self.privacy = privacy

    def photo(self, spec):
        return imgs.Photo(spec, self.base) if spec else None


# ---------------------------------------------------------------- basics
def canvas(ctx: Ctx, header: bool = True) -> Image.Image:
    im = imgs.background().copy()
    if header:
        draw_header(im, ctx.accent)
    return im


def draw_header(im: Image.Image, accent: str):
    imgs.fill_rrect(im, (-2, 19, 736, 139), 59, accent, corners=(False, True, True, False))
    d = ImageDraw.Draw(im)
    st = Style(gu="akhand_xb", lat="arista", size=73.5, lat_scale=1.11, color=WHITE)
    draw_line(d, HEADER_TEXT, fit(HEADER_TEXT, st, 680), 367, 103)
    lg = imgs.logo(118)
    im.paste(lg, (1072, 10), lg)


def title1(d, text: str, baseline: float = 319):
    st = Style(gu="akhand_xb", lat="anek_sb", size=166.7, color=BROWN)
    draw_line(d, text, fit(text, st, 1130), 600, baseline)


def title2(d, ctx: Ctx, text: str, size: float, baseline: float, lat: str = "anek_sb", upper=False):
    st = Style(gu="akhand_xb", lat=lat, size=size, color=ctx.accent, upper=upper)
    draw_line(d, text, fit(text, st, 1130), 600, baseline)


def band(im, y0, y1, color):
    imgs.fill_rrect(im, (0, y0, W, y1), 0, color)


def photo_boxes(n: int, aspect: float, y0: int, y1: int, wide_y1=None):
    """Layout for 1-2 people photos in family-style cards."""
    if n >= 2:
        return [(92, y0, 574, y1), (626, y0, 1108, y1)]
    if aspect > 1.15:  # one landscape photo
        return [(220, y0, 980, wide_y1 or (y0 + 597))]
    return [(359, y0, 841, y1)]


def _aspect(photo: imgs.Photo) -> float:
    im = photo.load()
    if photo.crop:
        x0, y0, x1, y1 = photo.crop
        return (x1 - x0) * im.width / max(1, (y1 - y0) * im.height)
    return im.width / im.height


def gaam_haal(native, city) -> str:
    parts = []
    if native:
        parts.append(f"ગામઃ {native}")
    if city:
        parts.append(f"હાલઃ {city}")
    return f"({', '.join(parts)})" if parts else ""


# ---------------------------------------------------------------- cards
def intro(ctx: Ctx) -> Image.Image:
    im = canvas(ctx, header=False)
    lg = imgs.logo(582)
    im.paste(lg, (309, 185), lg)
    d = ImageDraw.Draw(im)
    st = Style(gu="akhand_xb", lat="arista", size=183, lat_scale=1.11, color=ctx.accent)
    draw_line(d, INTRO_LINES[0], st, 600, 1065)
    draw_line(d, INTRO_LINES[1], st, 600, 1315)
    return im


def hero(ctx: Ctx, p: dict) -> Image.Image:
    im = canvas(ctx)
    ph = ctx.photo(p["photos"]["hero"])
    imgs.paste_photo(im, ph, (213, 157, 987, 996), 104, ctx.privacy)
    band(im, 1028, 1290, ctx.accent)
    d = ImageDraw.Draw(im)
    name = p["name"]
    st = Style(gu="akhand_xb", lat="poppins_sb", size=112.2, color=WHITE)
    draw_line(d, name, fit(name, st, 1130), 600, 1149)
    gh = gaam_haal(p.get("native_village"), p.get("city"))
    if gh:
        st2 = Style(gu="akhand_xb", lat="poppins_sb", size=66.5, color=WHITE)
        draw_line(d, gh, fit(gh, st2, 1130), 600, 1253)
    info = info_line(p)
    if info:
        st3 = Style(gu="anek_b", lat="anek_b", size=83.2, color=DARK)
        draw_line(d, info, fit(info, st3, 1130), 600, 1360)
    if p.get("sect"):
        st4 = Style(gu="akhand_xb", lat="anek_b", size=83.2, color=BROWN)
        draw_line(d, p["sect"], fit(p["sect"], st4, 1130), 600, 1473)
    return im


def info_line(p: dict) -> str:
    year = p.get("birth_year") or (str(p.get("dob", ""))[:4] if p.get("dob") else "")
    parts = [str(x) for x in (year, p.get("marital_status"), p.get("height")) if x]
    return ", ".join(parts)


def family_pair(ctx: Ctx, kind: str, d_: dict) -> Image.Image:
    """kind: dada_dadi | nana_nani | parents"""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, TITLE_FAMILY)
    photos = [ctx.photo(s) for s in d_.get("photos", []) if s][:2]
    if kind == "parents":
        title2(d, ctx, "માતા-પિતા", 166.7, 502)
        y0, y1, wide = 529, 1142, 1126
        band_y = (1160, 1400)
    else:
        title2(d, ctx, "દાદા-દાદી" if kind == "dada_dadi" else "નાના-નાની", 162.5, 509)
        y0, y1, wide = 565, 1178, 1162
        band_y = (1222, 1403)
    if photos:
        boxes = photo_boxes(len(photos), _aspect(photos[0]), y0, y1, wide)
        for ph, box in zip(photos, boxes):
            imgs.paste_photo(im, ph, box, 88)
    band(im, *band_y, BROWN)
    name = d_.get("display_name", "")
    st = Style(gu="akhand_xb", lat="poppins_sb", size=104.2, color=WHITE)
    if kind == "parents":
        draw_line(d, name, fit(name, st, 1140), 600, 1280)
        gh = gaam_haal(d_.get("village"), d_.get("city"))
        if gh:
            draw_line(d, gh, fit(gh, Style(size=66.7, color=WHITE), 1140), 600, 1368)
        if d_.get("sect"):
            draw_line(d, d_["sect"], Style(size=70.7, color=NEAR_BLACK), 600, 1481)
    else:
        draw_line(d, name, fit(name, st, 1140), 600, 1350)
        if d_.get("village"):
            draw_line(d, d_["village"], Style(size=66.7, color=BLACK), 600, 1467)
    return im


def single_parent(ctx: Ctx, rel: str, d_: dict) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, TITLE_FAMILY)
    label = "માતા" if rel == "mother" else "પિતા"
    title2(d, ctx, f"{label}: {d_.get('name', '')}".strip(": "), 126.7, 480)
    ph = ctx.photo(d_.get("photo"))
    if ph:
        imgs.paste_photo(im, ph, (359, 559, 841, 1172), 88)
    occ = d_.get("occupation") or []
    if isinstance(occ, str):
        occ = [occ]
    if len(occ) <= 1:
        band(im, 1216, 1457, BROWN)
        if occ:
            st = Style(gu="akhand_xb", lat="poppins_sb", size=104.2, lat_scale=1.0, color=WHITE)
            draw_line(d, occ[0], fit(occ[0], st, 1120), 600, 1377)
    else:
        band(im, 1161, 1471, BROWN)
        sizes = [62.5] + [70.8] * (len(occ) - 1)
        pitch = 91.7 if len(occ) <= 3 else 290 / len(occ)
        base = 1241 if len(occ) <= 3 else 1161 + 45 + pitch * 0.5
        for i, line in enumerate(occ):
            st = Style(gu="akhand_xb", lat="poppins_sb", size=sizes[i] * (1 if len(occ) <= 3 else 0.85),
                       color=WHITE)
            draw_line(d, line, fit(line, st, 1120), 600, base + i * pitch)
    return im


def sibling(ctx: Ctx, s: dict) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, SIBLING_TITLES.get(s.get("relation", ""), s.get("title", s.get("relation", ""))))
    name = s.get("display_name", "")
    if s.get("place"):
        name = f"{name} ({s['place']})"
    st = Style(gu="akhand_xb", lat="poppins_sb", size=87.5, color=ctx.accent)
    draw_line(d, name, fit(name, st, 1130), 600, 441)
    photos = [ctx.photo(x) for x in s.get("photos", []) if x][:2]
    if len(photos) == 2:
        boxes = [(94, 494, 577, 1108), (628, 494, 1111, 1108)]
    elif photos and _aspect(photos[0]) > 1.15:
        boxes = [(220, 494, 980, 1092)]
    else:
        boxes = [(357, 490, 844, 1109)]
    for ph, box in zip(photos, boxes):
        imgs.paste_photo(im, ph, box, 88)
    band(im, 1122, H, BROWN)
    # details block
    lab = Style(gu="akhand_xb", lat="poppins_sb", size=83.3, lat_scale=0.72, color=WHITE)
    lines = []  # (text, style, pitch)
    for det in s.get("details", []):
        who, txt = det.get("who", ""), det.get("text", "")
        one = f"{who}: {txt}" if who else txt
        lab1 = Style(gu="akhand_xb", lat="poppins_sb", size=83.3, lat_scale=0.85, color=WHITE)
        if measure(one, lab1) <= 1120 * 1.12:
            lines.append((one, fit(one, lab1, 1120, 0.88), 92))
        else:
            if who:
                lines.append((f"{who}:", lab, 80))
            body = Style(gu="akhand_xb", lat="poppins_sb", size=83.3, lat_scale=0.70, color=WHITE)
            for ln in wrap_balanced(txt, body, 1120):
                lines.append((ln, body, 66))
    _draw_block(d, lines, 1122, H)
    return im


def _draw_block(d, lines, y0, y1, x=600, align="center"):
    """Vertically centre a list of (text, style, pitch) lines inside y0..y1."""
    if not lines:
        return
    total = sum(p for _, _, p in lines)
    avail = (y1 - y0) - 50
    k = min(1.0, avail / total) if total else 1.0
    pitches = [p * k for _, _, p in lines]
    top = y0 + ((y1 - y0) - sum(pitches)) / 2
    yb = top
    for (txt, st, _), p in zip(lines, pitches):
        yb += p
        draw_line(d, txt, fit(txt, st.scaled(k), 1130), x, yb - p * 0.22, align)


def education(ctx: Ctx, entries: list, first: str) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, f"{first} નો પરિચય")
    title2(d, ctx, "Education / અભ્યાસ", 129.2, 487, upper=True)
    photo = next((ctx.photo(e["photo"]) for e in entries if e.get("photo")), None)
    if photo:
        imgs.paste_photo(im, photo, (47, 593, 379, 1297), 66, ctx.privacy)
        xb, xt, maxw = 415, 495, 1150 - 495
    else:
        xb, xt, maxw = 90, 170, 1110 - 170
    k = 1.0
    while True:
        ops, bl = [], 698
        for e in entries:
            deg = Style(gu="akhand_xb", lat="barlow_xb", size=104.2 * k, color=BLACK)
            dl, deg = wrap_fit(e.get("degree", ""), deg, maxw, 2, 0.7)
            ops.append(("bullet", bl))
            for i, ln in enumerate(dl):
                ops.append(("text", ln, deg, bl))
                bl += 105 * k if i < len(dl) - 1 else 0
            inst = Style(gu="akhand_xb", lat="barlow_m", size=66.7 * k, color=BLACK)
            for ln in wrap_balanced(e.get("institute", ""), inst, maxw) if e.get("institute") else []:
                bl += 85.4 * k
                ops.append(("text", ln, inst, bl))
            bl += 85.4 * k + 70 * k
        if bl - 70 * k <= 1440 or k < 0.6:
            break
        k -= 0.05
    for op in ops:
        if op[0] == "bullet":
            b = 58 * k
            imgs.fill_rrect(im, (xb, op[1] - 57 * k, xb + b, op[1] - 57 * k + b), 14 * k, ctx.accent)
        else:
            draw_line(d, op[1], op[2], xt, op[3], "left")
    return im


def bullet_list(im, d, items, accent, shape, x_b, x_t, max_w, first_bl, size, bottom,
                lat="barlow_sb", color=BLACK, b_side=None, b_off=None, line_k=1.39, gap_k=1.04,
                center_top=None):
    """Bullets + wrapped text, auto-shrinking to fit above `bottom`.
    max_w = right edge of the text. If center_top is set, the block is centred
    vertically between center_top and bottom. Returns final size."""
    k = 1.0
    while True:
        s = size * k
        st = Style(gu="akhand_xb", lat=lat, size=s, color=color)
        layout, bl = [], first_bl * 1.0
        for it in items:
            lines = wrap_balanced(it, st, max_w - x_t)
            layout.append((bl, lines))
            bl += s * line_k * (len(lines) - 1) + s * line_k + s * gap_k
        last = bl - s * line_k - s * gap_k
        if last <= bottom or k < 0.5:
            break
        k -= 0.04
    if center_top is not None:
        top_ink = first_bl - s * 0.75
        shift = ((center_top + bottom) / 2) - ((top_ink + last + s * 0.25) / 2)
        layout = [(bl + shift, lines) for bl, lines in layout]
    side = (b_side or 0.75 * size) * k
    off = (b_off or 0.68 * size) * k
    for bl, lines in layout:
        if shape == "dot":
            r = s * 0.42
            cy = bl - s * 0.36
            imgs.fill_circle(im, (x_b, cy - r / 2, x_b + r, cy + r / 2), accent)
        else:
            imgs.fill_rrect(im, (x_b, bl - off, x_b + side, bl - off + side), 14 * k, accent)
        for i, ln in enumerate(lines):
            draw_line(d, ln, st, x_t, bl + i * s * line_k, "left")
    return s


def work(ctx: Ctx, w: dict, first: str) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, f"{first} નો પરિચય")
    title2(d, ctx, "જોબ / વ્યવસાય", 166.7, 509)
    ph = ctx.photo(w.get("photo"))
    right = 790 if ph else 1150
    if ph:
        imgs.paste_photo(im, ph, (840, 582, 1174, 1284), 66, ctx.privacy)
    if w.get("style", "business") == "bullets":
        bullet_list(im, d, w.get("bullets", []), ctx.accent, ctx.job_bullet, 50,
                    100 if ctx.job_bullet == "dot" else 130, right, 680, 72, 1440, center_top=580)
        return im
    y_company, y_desc = 999, 1178
    if w.get("logo"):
        lg = imgs.contain(ctx.base / w["logo"], 353, 328)
        cx = 377 if ph else 600
        im.paste(lg, (int(cx - lg.width / 2), int(726 - lg.height / 2)), lg)
    else:
        y_company, y_desc = 760, 900
    x_left = 50 if ph else 600
    align = "left" if ph else "center"
    if w.get("company"):
        st = Style(gu="akhand_xb", lat="barlow_xb", size=91.1, color=BLACK)
        draw_line(d, w["company"], fit(w["company"], st, right - 50), x_left, y_company, align)
    if w.get("desc"):
        st = Style(gu="akhand_xb", lat="barlow_b", size=66.7, color=ctx.accent)
        lines, st = wrap_fit(w["desc"], st, right - 70, 3, 0.7)
        for i, ln in enumerate(lines):
            draw_line(d, ln, st, (70 if ph else 600), y_desc + i * 85.4, align)
    return im


def property_card(ctx: Ctx, items: list, first: str) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, f"{first} નો પરિચય")
    title2(d, ctx, "Income / Property:", 166.7, 521, upper=True)
    bullet_list(im, d, items, ctx.accent, "square", 86, 176, 1131, 753, 93, 1440,
                b_side=70, b_off=63, line_k=1.39, gap_k=1.04)
    return im


# ---------------------------------------------------------------- gallery overlay
def gallery_overlay(ctx: Ctx, p: dict) -> Image.Image:
    """RGBA overlay for the photo gallery: header + name band + white strip."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rgb = Image.new("RGB", (W, H), WHITE)
    mask = Image.new("L", (W, H), 0)
    draw_header(rgb, ctx.accent)
    band(rgb, 1110, 1372, ctx.accent)
    d = ImageDraw.Draw(rgb)
    name = p["name"]
    st = Style(gu="akhand_xb", lat="poppins_sb", size=112.2, color=WHITE)
    draw_line(d, name, fit(name, st, 1130), 600, 1234)
    gh = gaam_haal(p.get("native_village"), p.get("city"))
    if gh:
        draw_line(d, gh, fit(gh, Style(size=66.5, color=WHITE), 1130), 600, 1338)
    md = ImageDraw.Draw(mask)
    # opaque areas: header pill, logo, band + strip
    pill = imgs.rrect_mask(738, 120, 59, (False, True, True, False))
    mask.paste(pill, (-2, 19))
    lg = imgs.logo(118)
    mask.paste(lg.split()[3], (1072, 10), lg.split()[3])
    md.rectangle((0, 1110, W, H), fill=255)
    ov = rgb.convert("RGBA")
    ov.putalpha(mask)
    return ov


STRIP_H = 128   # white sub-line strip under the gallery name band (y 1372..1500)


def _ink_baseline(draw_fn, ref_text: str, st: Style) -> int:
    """Baseline that puts the ink of ref_text exactly in the vertical middle of the strip."""
    tmp = Image.new("L", (W, 400), 0)
    draw_fn(ImageDraw.Draw(tmp), ref_text, st, 200)
    bb = tmp.getbbox()
    if not bb:
        return 84
    return int(round(200 + STRIP_H / 2 - (bb[1] + bb[3]) / 2))


def _line_fn(d, text, st, baseline):
    draw_line(d, text, replace_color(st, 255), 600, baseline)


def replace_color(st: Style, color):
    from dataclasses import replace as _r
    return _r(st, color=color)


def strip_static(ctx: Ctx, text: str, kind: str) -> Image.Image:
    """White sub-line strip, text centred horizontally and vertically."""
    im = Image.new("RGB", (W, STRIP_H), WHITE)
    if kind == "sect":
        st = Style(gu="akhand_xb", lat="anek_b", size=83.2, color=BROWN)
    else:
        st = Style(gu="anek_b", lat="anek_b", size=83.2, color=DARK)
    st = fit(text, st, 1130)
    bl = _ink_baseline(_line_fn, text, st)
    draw_line(ImageDraw.Draw(im), text, st, 600, bl)
    return im


def ticker_parts(ctx: Ctx, hobbies: list):
    """Returns (label_img, text_img). The label image has a 30 px left margin and an 18 px gap after."""
    lab = Style(gu="anek_sb", lat="anek_sb", size=70, color=ctx.accent)
    txt = Style(gu="anek_sb", lat="anek_sb", size=70, color=BLACK, upper=True)
    label = "HOBBY:"
    bl = _ink_baseline(_line_fn, label, lab)          # caps: centre on the label's ink
    lw = int(measure(label, lab)) + 30 + 18
    li = Image.new("RGB", (lw, STRIP_H), WHITE)
    draw_line(ImageDraw.Draw(li), label, lab, 30, bl, "left")
    s = ", ".join(hobbies)
    tw = int(measure(s, txt)) + 10
    ti = Image.new("RGB", (tw, STRIP_H), WHITE)
    draw_line(ImageDraw.Draw(ti), s, txt, 0, bl, "left")
    return li, ti
