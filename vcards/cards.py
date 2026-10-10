"""Static cards (1200x1500 RGB). Coordinates/baselines come from the PSD templates."""
from __future__ import annotations

import re

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
    if aspect >= 0.9:  # square or landscape (typical couple photo): wide frame keeps both people
        return [(220, y0, 980, y1)]
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


def single_parent(ctx: Ctx, rel: str, d_: dict, fallback_photo=None) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, TITLE_FAMILY)
    label = "માતા" if rel == "mother" else "પિતા"
    title2(d, ctx, f"{label}: {d_.get('name', '')}".strip(": "), 126.7, 480)
    # own photo, else the parents' couple photo (wide frame), else a text panel
    ph = ctx.photo(d_.get("photo")) or ctx.photo(fallback_photo)
    if ph:
        box = (220, 559, 980, 1172) if _aspect(ph) >= 0.9 else (359, 559, 841, 1172)
        imgs.paste_photo(im, ph, box, 88)
    occ = d_.get("occupation") or []
    if isinstance(occ, str):
        occ = [occ]
    if not ph:
        imgs.fill_rrect(im, (92, 600, 1108, 1180), 88, BROWN)
        st = Style(gu="akhand_xb", lat="poppins_sb", size=80, color=WHITE)
        lines = []
        for o in occ:
            ls, s2 = wrap_fit(o, st, 900, 2, 0.6)
            lines += [(ln, s2) for ln in ls]
        pitch = 100
        first = 890 - pitch * (len(lines) - 1) / 2 + 28
        for i, (ln, s2) in enumerate(lines):
            draw_line(d, ln, fit(ln, s2, 900), 600, first + i * pitch)
        return im
    if len(occ) <= 1:
        band(im, 1216, 1457, BROWN)
        if occ:
            st = Style(gu="akhand_xb", lat="poppins_sb", size=104.2, lat_scale=1.0, color=WHITE)
            if measure(occ[0], st.scaled(0.75)) <= 1120:
                draw_line(d, occ[0], fit(occ[0], st, 1120), 600, 1377)
            else:  # long single line: 2 balanced lines
                lines, st2 = wrap_fit(occ[0], st.scaled(0.62), 1100, 2, 0.6)
                pitch = st2.size * 1.25
                first = (1216 + 1457) / 2 - pitch * (len(lines) - 1) / 2 + st2.size * 0.36
                for i, ln in enumerate(lines):
                    draw_line(d, ln, fit(ln, st2, 1100), 600, first + i * pitch)
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
    if not [x for x in s.get("photos", []) if x]:
        return sibling_no_photo(ctx, s)
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
    elif photos and _aspect(photos[0]) >= 0.9:
        boxes = [(220, 494, 980, 1108)]
    else:
        boxes = [(357, 490, 844, 1109)]
    for ph, box in zip(photos, boxes):
        imgs.paste_photo(im, ph, box, 88)
    _sibling_details(im, d, s.get("details", []))
    return im


def _sibling_details(im, d, details, y_max=1122, pad=52, max_w=1120):
    """Brown band at the bottom (always y_max..H, same on every card) with one paragraph per person
    ("who: text"): a long text continues after the name and wraps; a little space between people."""
    texts = [f"{x.get('who', '')}: {x.get('text', '')}" if x.get("who") else x.get("text", "") for x in details]
    texts = [t for t in texts if t.strip()]
    if not texts:
        band(im, y_max, H, BROWN)
        return
    gap, avail = 26, H - y_max - 2 * pad
    st1 = Style(gu="akhand_xb", lat="poppins_sb", size=83.3, lat_scale=0.85, color=WHITE)
    k = 1.0
    while True:      # largest size at which every paragraph (max 3 lines) fits the band
        paras = []
        for t in texts:
            if measure(t, st1.scaled(k)) <= max_w * 1.12:          # one line (squeezed a little if needed)
                paras.append(([t], fit(t, st1.scaled(k), max_w, 0.88), 83.3 * k * 1.12))
            else:                                                  # continues after the name, wrapped
                st = st1.scaled(k * 0.86)
                paras.append((wrap_balanced(t, st, max_w), st, st.size * 1.12))
        height = sum(p * len(ls) for ls, _, p in paras) + gap * k * (len(paras) - 1)
        if (height <= avail and all(len(ls) <= 3 for ls, _, _ in paras)) or k <= 0.5:
            break
        k -= 0.04
    top = y_max
    band(im, top, H, BROWN)
    y = top + (H - top - height) / 2
    for ls, st, p in paras:
        for ln in ls:
            y += p
            draw_line(d, ln, fit(ln, st, max_w), 600, y - p * 0.22)
        y += gap * k


def sibling_no_photo(ctx: Ctx, s: dict) -> Image.Image:
    """Girl PSD "BAHEN 1 DETAILS": title, then relation + name large in the centre, details in the bottom band."""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, TITLE_FAMILY, 317)
    rel = SIBLING_TITLES.get(s.get("relation", ""), s.get("relation", ""))
    words = s.get("display_name", "").split()
    lines = [rel + ":"] + ([words[0], " ".join(words[1:])] if len(words) > 1 else words)
    st = Style(gu="akhand_xb", lat="poppins_sb", size=179.2, color=ctx.accent)
    k = min(1.0, 3 / max(3, len(lines)))
    for i, ln in enumerate([x for x in lines if x]):
        draw_line(d, ln, fit(ln, st.scaled(k), 1100, 0.5), 600, 521 + i * 254 * k)
    band(im, 1181, 1473, BROWN)
    det = [f"{x['who']}: {x['text']}" if x.get("who") else x.get("text", "") for x in s.get("details", [])]
    det = [x for x in det if x]
    out = []
    if len(det) == 1:
        ls, st2 = wrap_fit(det[0], Style(gu="akhand_xb", lat="poppins_sb", size=104.2, color=WHITE), 1100, 2, 0.6)
        out = [(ln, st2) for ln in ls]
    else:
        for x in det[:3]:
            out.append((x, fit(x, Style(gu="akhand_xb", lat="poppins_sb", size=78, color=WHITE), 1100, 0.6)))
    if out:
        pitch = max(st2.size for _, st2 in out) * 1.22
        first = (1181 + 1473) / 2 - pitch * (len(out) - 1) / 2 + out[0][1].size * 0.36
        for i, (ln, st2) in enumerate(out):
            draw_line(d, ln, st2, 600, first + i * pitch)
    return im


def _draw_block(d, lines, y0, y1, x=600, align="center", max_w=1130):
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
        draw_line(d, txt, fit(txt, st.scaled(k), max_w), x, yb - p * 0.22, align)


INSTITUTE = "#652B02"      # college / university line on the education card


def education(ctx: Ctx, entries: list, first: str, fallback_photo=None) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, f"{first} નો પરિચય")
    title2(d, ctx, "Education / અભ્યાસ", 129.2, 487, upper=True)
    photo = next((ctx.photo(e["photo"]) for e in entries if e.get("photo")), None) or ctx.photo(fallback_photo)
    many = len(entries) > 3                 # 4-7 degrees: tighter spacing, smaller text if needed (1-3: as approved)

    def layout(maxw):
        k = 1.0
        while True:
            ops, bl = [], (650 if many else 698)
            for e in entries:
                deg = Style(gu="akhand_xb", lat="barlow_xb", size=104.2 * k, color=BLACK)
                dl, deg = wrap_fit(e.get("degree", ""), deg, maxw, 2, 0.7)
                ops.append(("bullet", bl))
                for i, ln in enumerate(dl):
                    ops.append(("text", ln, deg, bl))
                    bl += 105 * k if i < len(dl) - 1 else 0
                inst = Style(gu="akhand_xb", lat="barlow_m", size=66.7 * k, color=INSTITUTE)
                it = (e.get("institute") or "").strip()
                if it and not (it.startswith("(") and it.endswith(")")):
                    it = f"({it})"                  # "(BVM, Anand)" in brown (CT, 10 Oct 2026)
                for ln in wrap_balanced(it, inst, maxw) if it else []:
                    bl += 85.4 * k
                    ops.append(("text", ln, inst, bl))
                bl += 85.4 * k + (38 if many else 70) * k
            if bl - (38 if many else 70) * k <= (1460 if many else 1440) or k < (0.4 if many else 0.6):
                return ops, k
            k -= 0.05 if not many else 0.02

    if photo:  # photo on the right, text column on the left
        xb, xt = 50, 130
        ops, k = layout(800 - 130)
        if many and k < 0.6:                # too small next to the photo: the whole width for the text
            photo = None
    if photo:
        imgs.paste_photo(im, photo, (840, 582, 1174, 1284), 66, ctx.privacy)
    else:
        xb, xt = 90, 170
        ops, k = layout(1110 - 170)
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


def split_job(items: list):
    """-> (designation, company/area, extra lines). "X at Y" in one line is split."""
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return "", "", []
    if len(items) == 1:
        m = re.split(r"\s+at\s+", items[0], maxsplit=1, flags=re.I)
        return (m[0], m[1], []) if len(m) == 2 else (items[0], "", [])
    return items[0], items[1], items[2:]


def _job_logo(ctx: Ctx, w: dict, max_w: int, max_h: int):
    """Company logo for a job card: plain margins trimmed, a white / light background made transparent
    (a logo on a dark background keeps it, as a rounded label), or None."""
    src = _logo_src(ctx, w)
    if src is None or max_h < 60:
        return None
    return _logo_img(src, max_w, max_h)


def _logo_img(src, max_w: int, max_h: int) -> Image.Image:
    lg = imgs.contain(src, max_w, max_h, trim_bg=True, key_bg=True)
    if lg.getchannel("A").getextrema()[0] == 255:      # still opaque (dark background): soft rounded label
        lg.putalpha(imgs.rrect_mask(lg.width, lg.height, min(18, lg.height / 5)))
    return lg


def _logo_src(ctx: Ctx, w: dict):
    """The logo file, or the logo the team uploaded in the occupation photo box (edited image), or None."""
    if w.get("logo"):
        return ctx.base / w["logo"]
    return w["_logo_photo"].load() if w.get("_logo_photo") else None


def _paste_logo(im: Image.Image, lg: Image.Image, x: float, align: str, top: float):
    left = x if align == "left" else x - lg.width / 2
    im.paste(lg, (int(left), int(top)), lg)


def work(ctx: Ctx, w: dict, first: str, fallback_photo=None) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, f"{first} નો પરિચય")
    title2(d, ctx, "જોબ / વ્યવસાય", 166.7, 509)
    if w.get("photo") and not w.get("logo"):
        p0 = ctx.photo(w["photo"])
        if imgs.looks_like_logo(p0):      # a company logo in the photo box: drawn as the logo, a person photo on the right
            w = dict(w, photo=None, _logo_photo=p0)
    ph = ctx.photo(w.get("photo")) or ctx.photo(fallback_photo)
    right = 790 if ph else 1150
    if ph:
        imgs.paste_photo(im, ph, (840, 582, 1174, 1284), 66, ctx.privacy)
    if w.get("style", "business") == "bullets":
        items = w.get("bullets", [])
        x, align, maxw = (50, "left", right - 50) if ph else (600, "center", 1100)
        if len(items) > 3:  # a real list of roles: bullets (company logo, if any, above the list)
            lg = _job_logo(ctx, w, min(maxw, 560), 150)
            top = 580 + (lg.height + 40 if lg else 0)
            if lg:
                _paste_logo(im, lg, x, align, 580)
            bullet_list(im, d, items, ctx.accent, ctx.job_bullet, 50,
                        100 if ctx.job_bullet == "dot" else 130, right, top + 100, 72, 1440, center_top=top)
            return im
        desig, comp, extra = split_job(items)
        blocks = []  # (lines, style, pitch) or ("logo", None, height)
        if desig:
            st0 = Style(gu="akhand_xb", lat="barlow_xb", size=96, color=BLACK)
            if measure(desig, st0.scaled(0.8)) <= maxw:      # keep a designation on one line when it nearly fits
                ls, st = [desig], fit(desig, st0, maxw, 0.8)
            else:
                ls, st = wrap_fit(desig, st0, maxw, 2, 0.6)
            blocks.append((ls, st, 110))
        texts = []
        if comp:
            ls, st = wrap_fit(comp, Style(gu="akhand_xb", lat="barlow_b", size=66.7, color=ctx.accent), maxw, 3, 0.7)
            texts.append((ls, st, 85))
        for e in extra:
            ls, st = wrap_fit(e, Style(gu="akhand_xb", lat="barlow_m", size=58, color=BLACK), maxw, 2, 0.7)
            texts.append((ls, st, 74))
        gaps = 40
        height = sum(p * len(ls) for ls, _, p in blocks + texts) + gaps * (len(blocks + texts) - 1)
        # company logo ABOVE the company name (never in the photo frame), sized to the room left on the card
        lg = _job_logo(ctx, w, min(maxw, 520), min(170, 1440 - 560 - height - gaps))
        if lg:
            blocks.append(("logo", lg, lg.height))
        blocks += texts
        total = sum(p if ls == "logo" else p * len(ls) for ls, _, p in blocks) + gaps * (len(blocks) - 1)
        y = max(560, 933 - total / 2)  # vertical centre of the photo (582..1284)
        for ls, st, p in blocks:
            if ls == "logo":
                _paste_logo(im, st, x, align, y + 8)
                y += p + gaps
                continue
            for ln in ls:
                y += p
                draw_line(d, ln, st, x, y - p * 0.22, align)
            y += gaps
        return im
    y_company, y_desc = 999, 1178
    if w.get("logo") or w.get("_logo_photo"):
        lg = imgs.contain(_logo_src(ctx, w), 353, 328) if w.get("logo") else _logo_img(_logo_src(ctx, w), 353, 328)
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


def ticker_parts(ctx: Ctx, hobbies: list, label: str = "HOBBY:"):
    """Returns (label_img, text_img). The label image has a 30 px left margin and an 18 px gap after."""
    lab = Style(gu="anek_sb", lat="anek_sb", size=70, color=ctx.accent)
    txt = Style(gu="anek_sb", lat="anek_sb", size=70, color=BLACK, upper=True)
    bl = _ink_baseline(_line_fn, label, lab)          # caps: centre on the label's ink
    lw = int(measure(label, lab)) + 30 + 18
    li = Image.new("RGB", (lw, STRIP_H), WHITE)
    draw_line(ImageDraw.Draw(li), label, lab, 30, bl, "left")
    s = ", ".join(hobbies)
    tw = int(measure(s, txt)) + 10
    ti = Image.new("RGB", (tw, STRIP_H), WHITE)
    draw_line(ImageDraw.Draw(ti), s, txt, 0, bl, "left")
    return li, ti


def single_property(p: dict):
    """(label, text) when the profile has exactly ONE Income / Property line: it is shown in the gallery's
    white strip (like the hobbies) instead of an own card. Otherwise None."""
    items = [str(x).strip() for x in (p.get("property") or []) if str(x).strip()]
    if len(items) != 1:
        return None
    it = items[0]
    if it.lower().startswith("income:"):
        return "INCOME:", it.split(":", 1)[1].strip()
    return "PROPERTY:", it


STATIC_SECONDS = 3.0   # a fixed sub-line (sect / info) stays at least this long


def gallery_sublines(ctx: Ctx, p: dict) -> list:
    """Rotating white strip under the gallery name band: [(state, seconds needed)].
    state = ("ticker", label_img, text_img) or ("static", img). A long ticker scrolls ONCE to its end (never cut)."""
    from .config import TIMING
    out = []
    tick = []
    if p.get("hobbies"):
        tick.append(ticker_parts(ctx, p["hobbies"]))
    sp = single_property(p)
    if sp:
        tick.append(ticker_parts(ctx, [sp[1]], sp[0]))
    for li, ti in tick:
        avail = W - li.width - 20
        need = STATIC_SECONDS if ti.width <= avail else 0.8 + (ti.width - avail) / TIMING["ticker_px_s"] + 1.4
        out.append((("ticker", li, ti), need))
    if p.get("sect"):
        out.append((("static", strip_static(ctx, p["sect"], "sect")), STATIC_SECONDS))
    info = info_line(p)
    if info:
        out.append((("static", strip_static(ctx, info, "info")), STATIC_SECONDS))
    return out


def past_items(w: dict) -> list:
    """Past experiences of the occupation: "text" / ["text", ...] / [{"text", "logo"}] -> [{"text", "logo"}] (max 3)."""
    past = (w or {}).get("past")
    if not past:
        return []
    if isinstance(past, str):
        past = [past]
    out = []
    for x in past:
        x = {"text": x} if isinstance(x, str) else dict(x or {})
        if str(x.get("text") or "").strip():
            out.append({"text": str(x["text"]).strip(), "logo": x.get("logo")})
    return out[:3]


def past_experience(ctx: Ctx, items: list, first: str) -> Image.Image:
    """Card after the occupation card: up to 3 past jobs, each with its company logo above the text (music only)."""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, f"{first} નો પરિચય")
    title2(d, ctx, "Past Experience:", 166.7, 521, upper=True)
    n = len(items)
    k = 1.0
    while True:
        blocks = []
        for it in items:
            lg = _logo_img(ctx.photo(it["logo"]).load(), int(560 * k), int((210 if n == 1 else 150) * k)) if it.get("logo") else None
            st = Style(gu="akhand_xb", lat="barlow_b", size=(78 if n == 1 else 68) * k, color=BLACK)
            ls, st = wrap_fit(it["text"], st, 1080, 2, 0.7)
            blocks.append((lg, ls, st, st.size * 1.25))
        gap = 70 * k
        height = sum((lg.height + 26 * k if lg else 0) + p * len(ls) for lg, ls, _, p in blocks) + gap * (n - 1)
        if height <= 1440 - 600 or k < 0.6:
            break
        k -= 0.05
    y = 600 + (840 - height) / 2
    for lg, ls, st, p in blocks:
        if lg:
            im.paste(lg, (int(600 - lg.width / 2), int(y)), lg)
            y += lg.height + 26 * k
        for ln in ls:
            y += p
            draw_line(d, ln, st, 600, y - p * 0.22)
        y += gap
    return im

