"""Static cards (1200x1500 RGB). Coordinates/baselines come from the PSD templates."""
from __future__ import annotations

import re

from PIL import Image, ImageDraw

from . import imgs
from .config import BLACK, BROWN, DARK, H, NEAR_BLACK, THEMES, W, WHITE
from .text import Style, draw_line, fit, ink, measure, wrap_balanced, wrap_fit

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
    n, c = " ".join(str(native or "").split()), " ".join(str(city or "").split())
    if n and n == c:                     # same village and city (team PSDs): "(બોટાદ)" only
        return f"({n})"
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
        draw_bottom_line(d, p["sect"], fit(p["sect"], st4, 1130), 1473)
    return im


BOTTOM_GAP = 24   # a text line at the bottom of a card ends at least this far above the edge (CT, 14 Oct 2026)


def draw_bottom_line(d, text: str, st: Style, baseline: float, limit: float = H - BOTTOM_GAP):
    """A line near the bottom edge: at its approved baseline, lifted only as far as its lowest letter (e.g. the ુ of
    ગુર્જર) needs to stay `limit` px from the edge."""
    draw_line(d, text, st, 600, min(baseline, limit - ink(text, st)[1]))


def draw_line_between(d, text: str, st: Style, y0: float, y1: float, margin: float = 14):
    """A line centred (by its letters) between y0 and y1, smaller if it does not fit with `margin` above and below."""
    t, b = ink(text, st)
    if b - t > y1 - y0 - 2 * margin:
        st = st.scaled((y1 - y0 - 2 * margin) / (b - t))
        t, b = ink(text, st)
    draw_line(d, text, st, 600, (y0 + y1) / 2 - (t + b) / 2)


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
    if not photos:                     # no photo uploaded: big name + place band, no empty photo area
        return _family_pair_no_photo(im, d, ctx, kind, d_)
    if kind == "parents" and d_.get("sect"):
        # team PSDs: the sect is the 3rd line INSIDE the band, white, in brackets: name / (village, city) / (sect)
        band_y, y1 = (1150, 1470), 1120
    if photos:
        boxes = photo_boxes(len(photos), _aspect(photos[0]), y0, y1, wide)
        for ph, box in zip(photos, boxes):
            imgs.paste_photo(im, ph, box, 88)
    band(im, *band_y, BROWN)
    name = d_.get("display_name", "")
    st = Style(gu="akhand_xb", lat="poppins_sb", size=104.2, color=WHITE)
    if kind == "parents" and d_.get("sect"):
        gh = gaam_haal(d_.get("village"), d_.get("city"))
        lines = [(name, fit(name, st.scaled(0.86), 1140))]
        for t in (gh, paren(d_["sect"])):
            if t:
                lines.append((t, fit(t, Style(size=64, color=WHITE), 1140)))
        offs = [0, 100, 178][:len(lines)]
        hi = min(o + ink(t, s)[0] for o, (t, s) in zip(offs, lines))
        lo = max(o + ink(t, s)[1] for o, (t, s) in zip(offs, lines))
        base = sum(band_y) / 2 - (hi + lo) / 2
        for o, (t, s) in zip(offs, lines):
            draw_line(d, t, s, 600, base + o)
        return im
    if kind == "parents":
        draw_line(d, name, fit(name, st, 1140), 600, 1280)
        gh = gaam_haal(d_.get("village"), d_.get("city"))
        if gh:
            draw_line(d, gh, fit(gh, Style(size=66.7, color=WHITE), 1140), 600, 1368)
        if d_.get("sect"):                       # between the band and the bottom edge, never touching it
            draw_line_between(d, d_["sect"], fit(d_["sect"], Style(size=70.7, color=NEAR_BLACK), 1140), band_y[1], H)
    else:
        draw_line(d, name, fit(name, st, 1140), 600, 1350)
        if d_.get("village"):
            draw_bottom_line(d, d_["village"], fit(d_["village"], Style(size=66.7, color=BLACK), 1140), 1467)
    return im


NAME_BROWN = "#684124"   # big name on the family cards without a photo (CT's reference, 13 Oct 2026)


def _family_pair_no_photo(im, d, ctx: Ctx, kind: str, d_: dict) -> Image.Image:
    """Dada-dadi / nana-nani / parents without photos (CT, 13 Oct 2026): titles lower, the name large in dark brown
    (max 2 lines) in the middle, the place (+ city) in white in a brown band, sect (parents) under the band."""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, TITLE_FAMILY, 398)
    t2 = {"parents": "માતા-પિતા", "dada_dadi": "દાદા-દાદી", "nana_nani": "નાના-નાની"}[kind]
    title2(d, ctx, t2, 166.7, 600)
    name = d_.get("display_name", "")
    if name:
        st = Style(gu="akhand_xb", lat="poppins_sb", size=186, color=NAME_BROWN)
        if measure(name, st) <= 1130:
            ls, st = [name], st
        else:
            ls, st = wrap_fit(name, st, 1130, 2, 0.55)
        pitch = st.size * 1.16
        base0 = 928 - pitch * (len(ls) - 1) / 2 + st.size * 0.30       # lines centred around y 928
        for i, ln in enumerate(ls):
            draw_line(d, ln, fit(ln, st, 1130), 600, base0 + i * pitch)
    band(im, 1207, 1357, BROWN)
    place = gaam_haal(d_.get("village"), d_.get("city")) if kind == "parents" else d_.get("village", "")
    if place:
        draw_line(d, place, fit(place, Style(size=100, color=WHITE), 1140), 600, 1321)
    if kind == "parents" and d_.get("sect"):
        draw_bottom_line(d, d_["sect"], fit(d_["sect"], Style(size=70.7, color=NEAR_BLACK), 1140), 1450)
    return im


def parent_jobs(d_: dict) -> list:
    """The app's Type / Name / Work rows of a parent (max 4): [{type, name, desc}]; [] for older profiles."""
    out = []
    for j in (d_.get("jobs") or [])[:4]:
        j = {k: " ".join(str((j or {}).get(k) or "").split()) for k in ("type", "name", "desc")}
        if j["type"] or j["name"] or j["desc"]:
            out.append(j)
    return out


def _bracket_lines(text: str, st: Style, max_w: float):
    """'Brand Name: X (Manufacturer of Y)' -> ['Brand Name: X', '(Manufacturer of Y)'] when both parts fit one line
    (CT, 16 Oct 2026: a bracket part is its own line, never cut in the middle); None when there is no such split."""
    i = text.find(" (")
    if i <= 0:
        return None
    a, b = text[:i].strip(), text[i:].strip()
    if a and b and max(measure(a, st.scaled(0.7)), measure(b, st.scaled(0.7))) <= max_w:
        return [a, b]
    return None


def _jobs_band(jobs: list, bottom: int = 1471, top: int = 1161, edu: str = ""):
    """Brown band for a parent's jobs, never taller than the approved band (1161..1471). Per job (CT, 14 Oct 2026):
    the type BIGGEST, the name / company smaller, the work smallest. A name that would have to shrink a lot to fit one
    line goes on 2 lines instead; everything then shrinks together until it fits. Returns (band top, draw function)."""
    SZ = {"type": 80.0, "name": 66.0, "desc": 60.0}
    n_lines = sum(1 for j in jobs for r in ("type", "name", "desc") if j[r]) + (1 if edu else 0)
    pad = 30 if n_lines <= 3 else 18
    room = bottom - top - 2 * pad
    k = 1.0
    while True:
        rows = []                                        # (text, style, pitch, gap_before)
        if edu:                                          # parent's education first, e.g. "(M.Com + LLB)" (team PSDs)
            st = Style(gu="akhand_xb", lat="poppins_sb", size=SZ["desc"] * k, color=WHITE)
            for ln in ([edu] if measure(edu, st.scaled(0.86)) <= 1120 else wrap_balanced(edu, st, 1120)[:2]):
                rows.append((ln, st, st.size * 1.16, 0))
        for i, j in enumerate(jobs):
            first = True
            for role in ("type", "name", "desc"):
                if not j[role]:
                    continue
                st = Style(gu="akhand_xb", lat="poppins_sb", size=SZ[role] * k, color=WHITE)
                if measure(j[role], st.scaled(0.86)) <= 1120 or role == "type":
                    ls = [j[role]]                        # one line (fit() shrinks it at most to 86 %)
                else:                                     # name / work too long: 2 lines, "(…)" on its own line
                    ls = _bracket_lines(j[role], st, 1120) or wrap_balanced(j[role], st, 1120)[:2]
                for ln in ls:
                    rows.append((ln, st, st.size * 1.16, 14 * k if (first and (i or edu)) else 0))
                    first = False
        total = sum(p + g for _, _, p, g in rows)
        if total <= room or k <= 0.5:
            break
        k -= 0.03

    def draw(im, d):
        band(im, top, bottom, BROWN)
        y = top + (bottom - top - total) / 2
        for ln, st, p, g in rows:
            y += g + p
            draw_line(d, ln, fit(ln, st, 1120, 0.7), 600, y - p * 0.24)
    return top, draw


def single_parent(ctx: Ctx, rel: str, d_: dict, fallback_photo=None) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, TITLE_FAMILY)
    label = "માતા" if rel == "mother" else "પિતા"
    title2(d, ctx, f"{label}: {d_.get('name', '')}".strip(": "), 126.7, 480)
    # own photo, else the parents' couple photo (wide frame), else a text panel
    ph = ctx.photo(d_.get("photo")) or ctx.photo(fallback_photo)
    jobs = parent_jobs(d_)
    occ = d_.get("occupation") or []
    if isinstance(occ, str):
        occ = [occ]
    edu = paren(d_.get("education"))                  # optional (team PSDs): "(B.Com + LLB)" above the occupation
    if jobs:
        occ = [t for j in jobs for t in (j["type"], j["name"], j["desc"]) if t]
    elif edu:
        occ = [edu] + list(occ)
    if ph and jobs and (len(occ) > 1 or edu):
        # Type / Name / Work rows from the app (CT, 13 Oct 2026): type small, name larger, work medium; the band
        # grows upwards for 2+ jobs and the photo always ends 36 px above it (never touching the band)
        top, draw_band = _jobs_band(jobs, edu=edu)
        y1 = top - 36
        box = (220, 559, 980, y1) if _aspect(ph) >= 0.9 else (359, 559, 841, y1)
        imgs.paste_photo(im, ph, box, 88)
        draw_band(im, d)
        return im
    if ph:
        y1 = 1172 if len(occ) <= 1 else 1125           # multi-line band starts at 1161: keep a margin above it
        box = (220, 559, 980, y1) if _aspect(ph) >= 0.9 else (359, 559, 841, y1)
        imgs.paste_photo(im, ph, box, 88)
    if not ph:
        if jobs and edu:
            occ = [edu] + occ
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
        sts = [fit(line, Style(gu="akhand_xb", lat="poppins_sb", size=sizes[i] * (1 if len(occ) <= 3 else 0.85),
                               color=WHITE), 1120) for i, line in enumerate(occ)]
        # the letters are centred in the band (CT, 16 Oct 2026: 4 lines touched the bottom edge, 2 lines sat high);
        # 3 lines keep the approved place (it was already centred)
        base = _centred_base(occ, sts, pitch, 1161, 1471)
        for i, line in enumerate(occ):
            draw_line(d, line, sts[i], 600, base + i * pitch)
    return im


def _centred_base(lines, styles, pitch, top, bottom):
    """First baseline that puts the drawn letters of the lines (one every `pitch` px) in the middle of top..bottom,
    so the empty space above the text equals the space below it."""
    hi = min(i * pitch + ink(ln, st)[0] for i, (ln, st) in enumerate(zip(lines, styles)))
    lo = max(i * pitch + ink(ln, st)[1] for i, (ln, st) in enumerate(zip(lines, styles)))
    return (top + bottom) / 2 - (hi + lo) / 2


def sibling(ctx: Ctx, s: dict) -> Image.Image:
    if not [x for x in s.get("photos", []) if x]:
        return sibling_no_photo(ctx, s)
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    details = s.get("details", [])
    empty = not [t for t in (_detail_segments(x) for x in details) if t]
    dy = 40 if empty else 0          # no details (CT, 14 Oct 2026): no brown band, titles a little lower, bigger photo
    title1(d, SIBLING_TITLES.get(s.get("relation", ""), s.get("title", s.get("relation", ""))), 319 + dy)
    name = s.get("display_name", "")
    if s.get("place"):
        name = f"{name} ({s['place']})"
    st = Style(gu="akhand_xb", lat="poppins_sb", size=87.5, color=ctx.accent)
    draw_line(d, name, fit(name, st, 1130), 600, 441 + dy)
    photos = [ctx.photo(x) for x in s.get("photos", []) if x][:2]
    if len(photos) == 2:
        boxes = [(94, 494, 577, 1108), (628, 494, 1111, 1108)]
    elif photos and _aspect(photos[0]) >= 0.9:
        boxes = [(220, 494, 980, 1108)]
    else:
        boxes = [(357, 490, 844, 1109)]
    if empty:
        # the photo frame(s) scaled up together (same shape) into the free area under the name, centred
        x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
        x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
        top, bottom = 494 + dy + 10, (1122 + H) // 2     # down to half of the (missing) band, the rest stays free (CT)
        k = min((bottom - top) / (y1 - y0), 1110 / (x1 - x0))
        ox = 600 - (x1 - x0) * k / 2
        # width-limited (2 photos side by side): a little taller (max 1.45 x the width), centred in the free area
        h = min(bottom - top, max((y1 - y0) * k, (boxes[0][2] - boxes[0][0]) * k * 1.45))
        oy = top + (bottom - top - h) / 2
        for ph, b in zip(photos, boxes):
            imgs.paste_photo(im, ph, (ox + (b[0] - x0) * k, oy, ox + (b[2] - x0) * k, oy + h), 88)
        return im
    top, draw_band = _sibling_band(details)
    for ph, box in zip(photos, boxes):          # a shorter band (short text): the photo grows, same margin above it
        imgs.paste_photo(im, ph, (box[0], box[1], box[2], box[3] + top - 1122), 88)
    draw_band(im, d)
    return im


def hard_lines(text) -> list[str]:
    """The team's own line breaks (Enter in the form's text box) are kept: one entry per typed line,
    spaces tidied, empty lines dropped."""
    return [" ".join(x.split()) for x in str(text or "").splitlines() if x.strip()]


def _detail_segments(x: dict) -> list[str]:
    """One sibling detail ("who" + text) as its typed lines; the name goes before the first line."""
    segs = hard_lines(x.get("text", ""))
    if segs and x.get("who"):
        segs[0] = f"{x['who']}: {segs[0]}"
    return segs


def _sibling_details(im, d, details, y_max=1122, pad=52, max_w=1120):
    _, draw = _sibling_band(details, y_max, pad, max_w)
    draw(im, d)


def _sibling_band(details, y_max=1122, pad=52, max_w=1120):
    """Brown band at the bottom (y_max..H) with one paragraph per person ("who: text"): a long text continues after
    the name and wraps; a line break typed in the form starts a new line too; a little space between people.
    Short text (every paragraph one line): larger letters (up to 125 %) and a shorter band (CT, 13 Oct 2026).
    Returns (band top, draw function)."""
    texts = [t for t in (_detail_segments(x) for x in details) if t]
    if not texts:
        return y_max, lambda im, d: band(im, y_max, H, BROWN)
    if sum(len(t) for t in texts) > 3:        # 4+ typed lines: less empty band above / below, so the text stays big
        pad = 26
    gap, avail = 26, H - y_max - 2 * pad
    st1 = Style(gu="akhand_xb", lat="poppins_sb", size=83.3, lat_scale=0.85, color=WHITE)
    short = all(len(t) == 1 and measure(t[0], st1) <= max_w for t in texts)
    if short:
        k = 1.25
        while k > 1.0 and not all(measure(t[0], st1.scaled(k)) <= max_w for t in texts):
            k -= 0.05
        paras = [([t[0]], st1.scaled(k), 83.3 * k * 1.12, 1) for t in texts]
        height = sum(p for _, _, p, _ in paras) + gap * k * (len(paras) - 1)
        top = int(max(y_max, H - height - 2 * pad))
    else:
        k = 1.0
        while True:      # largest size at which every paragraph (max 3 lines, or its typed lines) fits the band
            paras = []
            for segs in texts:
                if len(segs) == 1 and measure(segs[0], st1.scaled(k)) <= max_w * 1.12:   # one line (squeezed a little)
                    paras.append(([segs[0]], fit(segs[0], st1.scaled(k), max_w, 0.88), 83.3 * k * 1.12, 1))
                else:                                  # continues after the name, wrapped; typed lines stay lines
                    st = st1.scaled(k * 0.86)
                    ls = [ln for sg in segs for ln in wrap_balanced(sg, st, max_w)]
                    paras.append((ls, st, st.size * 1.12, len(segs)))
            height = sum(p * len(ls) for ls, _, p, _ in paras) + gap * k * (len(paras) - 1)
            if (height <= avail and all(len(ls) <= max(3, n) for ls, _, _, n in paras)) or k <= 0.5:
                break
            k -= 0.04
        top = y_max

    def draw(im, d):
        band(im, top, H, BROWN)
        y = top + (H - top - height) / 2
        for ls, st, p, _ in paras:
            for ln in ls:
                y += p
                draw_line(d, ln, fit(ln, st, max_w), 600, y - p * 0.22)
            y += gap * k
    return top, draw


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
    det = [t for t in (_detail_segments(x) for x in s.get("details", [])) if t]
    lines = [ln for t in det for ln in t]                 # a line break typed in the form = a new line here
    out = []
    if len(lines) == 1:
        ls, st2 = wrap_fit(lines[0], Style(gu="akhand_xb", lat="poppins_sb", size=104.2, color=WHITE), 1100, 2, 0.6)
        out = [(ln, st2) for ln in ls]
    elif lines:
        size = 104.2 if len(det) == 1 and len(lines) == 2 else 78 * min(1.0, 3 / len(lines))
        for x in lines:
            out.append((x, fit(x, Style(gu="akhand_xb", lat="poppins_sb", size=size, color=WHITE), 1100, 0.6)))
    if out:
        pitch = max(st2.size for _, st2 in out) * 1.22
        first = (1181 + 1473) / 2 - pitch * (len(out) - 1) / 2 + out[0][1].size * 0.36
        for i, (ln, st2) in enumerate(out):
            draw_line(d, ln, st2, 600, first + i * pitch)
    return im


SIB_LIST_TITLE = "#97755F"      # relation title on the siblings text slide (team PSD, CT 16 Oct 2026); names = theme colour


def no_photo(s: dict) -> bool:
    return not [x for x in (s or {}).get("photos", []) if x]


def sibling_list_parts(s: dict) -> tuple:
    """(name, '(<place>)'), or '(<occupation / education>)' when no place is filled (CT, 15 Oct 2026); '' = nothing."""
    name = str(s.get("display_name", "")).strip()
    extra = str(s.get("place") or "").strip()
    if not extra:
        extra = ", ".join(ln for x in s.get("details", []) for ln in _detail_segments(x))
    if extra and not (extra.startswith("(") and extra.endswith(")")):
        extra = f"({extra})"
    return name, extra


def sibling_groups(sibs: list) -> list:
    """[(relation title, [(name, extra)])]; siblings next to each other with the same relation share one title."""
    out = []
    for s in sibs:
        rel = SIBLING_TITLES.get(s.get("relation", ""), s.get("relation", "")).replace(" - ", "-")
        if out and out[-1][0] == rel:
            out[-1][1].append(sibling_list_parts(s))
        else:
            out.append((rel, [sibling_list_parts(s)]))
    return out


def siblings_list(ctx: Ctx, sibs: list) -> Image.Image:
    """2+ siblings without a photo: ONE text slide, shown with music only (team PSD, CT 16 Oct 2026): the relation title
    in light brown, then per sibling the name in the theme colour and its (place) on the line below, spread over the
    page. Siblings with a photo keep their own card."""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    groups = sibling_groups(sibs)
    W = 1130                                            # widest line
    t_st = Style(gu="akhand_xb", lat="anek_sb", size=147, color=SIB_LIST_TITLE)
    n_st = Style(gu="akhand_xb", lat="poppins_sb", size=95, lat_scale=0.9, color=ctx.accent)
    lines = [x for _, ls in groups for nm, ex in ls for x in (nm, ex) if x]
    k = min([1.0] + [W / measure(x, n_st) for x in lines if measure(x, n_st) > 0])      # all names one size, like the PSD
    n_st = n_st.scaled(max(0.5, k))
    t_k = min([1.0] + [W / measure(t, t_st) for t, _ in groups if measure(t, t_st) > 0])
    t_st = t_st.scaled(max(0.5, t_k))
    # baseline steps measured on the PSD (3 siblings): title -> name 252, name -> (place) 119, (place) -> next name 181
    f = min(1.0, n_st.size / 95)                        # shrunk names: their lines closer together too

    def layout(T_N, N_P, P_N, P_T):
        items, y = [], 0.0
        for gi, (t, ls) in enumerate(groups):
            if gi:
                y += P_T
            items.append(("t", t, y)); y += T_N
            for i, (nm, ex) in enumerate(ls):
                if i:
                    y += P_N
                items.append(("n", nm, y))
                if ex:
                    y += N_P; items.append(("n", ex, y))
        return items, y
    top, bottom = 350.0, 1330.0                          # first title / last line baselines on the PSD
    items, span = layout(252.0, 119.0 * f, 181.0 * f, 260.0)
    if span > bottom - top:                             # more lines: use more of the page, then close the gaps a little,
        top, bottom = 290.0, 1430.0
        items, span = layout(215.0, 119.0 * f, 160.0 * f, 205.0)
    s_ = 1.0
    if span > bottom - top:                             # ... and only then make letters and gaps smaller together
        s_ = max(0.45, (bottom - top) / span)
        t_st, n_st = t_st.scaled(s_), n_st.scaled(s_)
    off = (top + bottom) / 2 - span * s_ / 2
    for kind, txt, yy in items:
        st = t_st if kind == "t" else n_st
        draw_line(d, txt, fit(txt, st, W, 0.5), 600, off + yy * s_)
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


def deg_lines(e: dict):
    """A degree as typed (team PSDs): line 1 and plain lines big ("B A" / "Bachelor of Arts"), lines in brackets small
    under it ("(Gold Medalist)", "(CA Final Group 2 Cleared)"). -> (big lines, small lines)"""
    segs = hard_lines(e.get("degree", ""))
    big = [sg for i, sg in enumerate(segs) if i == 0 or not (sg.startswith("(") and sg.endswith(")"))]
    small = [sg for i, sg in enumerate(segs) if i > 0 and sg.startswith("(") and sg.endswith(")")]
    return big, small


EDU_SUB_GIRL = "#94694A"    # "EDUCATION / અભ્યાસ" on the girl PSDs (brown; the title above is pink)


def edu_colors(ctx: Ctx):
    """(title, sub-title, degree) colours: boy = brown title, blue sub-title, black degrees; girl = pink title,
    brown sub-title, dark brown degrees (team PSDs, 17 Oct 2026)."""
    if ctx.theme == "girl":
        return ctx.accent, EDU_SUB_GIRL, "#46300D"
    return BROWN, ctx.accent, BLACK


def education(ctx: Ctx, entries: list, first: str, fallback_photo=None) -> Image.Image:
    """Team PSDs (17 Oct 2026): degrees in Anek Gujarati Condensed, big. ONE degree: candidate photo on the right, no
    bullet, the degree on up to 3 lines. 2+ degrees: no photo, full width, a round bullet per degree, the college
    small and brown under it."""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    c_title, c_sub, c_deg = edu_colors(ctx)
    t0 = f"{first} નુ એજ્યુકેશન:"
    draw_line(d, t0, fit(t0, Style(gu="akhand_xb", lat="anek_sb", size=126.9, color=c_title), 1100), 600, 297)
    st_sub = Style(gu="akhand_xb", lat="anek_sb", size=129.2, color=c_sub, upper=True)
    draw_line(d, "Education / અભ્યાસ", fit("Education / અભ્યાસ", st_sub, 1130), 600, 487)
    one = len(entries) == 1
    photo = (next((ctx.photo(e["photo"]) for e in entries if e.get("photo")), None) or ctx.photo(fallback_photo)) if one else None
    many = len(entries) > 3
    if photo:
        imgs.paste_photo(im, photo, (840, 582, 1174, 1284), 66, ctx.privacy)
        xb, xt, maxw = 50, 50, 760
    else:
        xb, xt, maxw = 70, 145, 1150 - 145
    top, bottom = 560, 1450

    def layout(k):
        deg0 = Style(gu="akhand_xb", lat="anek_sb", size=(175 if one else 150) * k, color=c_deg)
        n_max = 3 if one else 2
        sizes = [wrap_fit(sg, deg0, maxw, n_max, 0.7)[1].size for e in entries for sg in deg_lines(e)[0]]
        deg = deg0.scaled(min(sizes) / deg0.size) if sizes else deg0
        inst = Style(gu="akhand_xb", lat="anek_sb", size=deg.size * 0.56, color=INSTITUTE)
        ops, y, ok = [], 0.0, True
        for i, e in enumerate(entries):
            big, small = deg_lines(e)
            if i:
                y += (34 if many else 62) * k
            dl = [ln for sg in big for ln in wrap_balanced(sg, deg, maxw)]
            ok = ok and len(dl) <= n_max * max(1, len(big))
            for j, ln in enumerate(dl):
                y += deg.size * 1.02
                ops.append(("bullet" if (j == 0 and not one) else "text", ln, deg, y))
            it = (e.get("institute") or "").strip()
            for sg in small + ([paren(it)] if it else []):
                for ln in wrap_balanced(sg, inst, maxw):
                    y += inst.size * 1.28
                    ops.append(("text", ln, inst, y))
        return ops, y, ok

    k = 1.0
    while True:
        ops, total, ok = layout(k)
        if (ok and total <= bottom - top) or k <= 0.4:
            break
        k -= 0.03
    off = (top + bottom) / 2 - total / 2 - 10 if not photo else max(top, 933 - total / 2)
    for kind, txt, st, y in ops:
        base = off + y - st.size * 0.24
        if kind == "bullet":
            r = st.size * 0.30
            cy = base - st.size * 0.30
            imgs.fill_circle(im, (xb, cy - r / 2, xb + r, cy + r / 2), ctx.accent)
        draw_line(d, txt, fit(txt, st, maxw), xt, base, "left")
    return im


def edu_work_fits(p: dict) -> bool:
    """The app's tick "Education + occupation on one slide" and both are short enough (team PSDs: Palak, Riddhi,
    Vishvas, Vruti ...): up to 3 degrees and one job (max 2 lines) or one business, no Past Experience."""
    w, edu = p.get("work") or {}, [e for e in (p.get("education") or []) if e.get("degree")]
    if not (p.get("edu_work_one") and edu and w and len(edu) <= 3 and not past_items(w)):
        return False
    return len(business_items(w)) == 1 if w.get("style", "business") != "bullets" else 0 < len(w.get("bullets") or []) <= 2


def edu_work(ctx: Ctx, p: dict, first: str) -> Image.Image:
    """Education and occupation on ONE card, full width (no photo): "<name> નુ એજ્યુકેશન:" + degree bullets (college
    small, brown), then "<name> નુ ઓક્યુપેશન:" + one bullet (designation / business label, name, work) + logo."""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    w = p.get("work") or {}
    if w.get("photo") and not w.get("logo"):
        p0 = ctx.photo(w["photo"])
        if not imgs.faces(*p0.key):
            w = dict(w, photo=None, _logo_photo=p0)
    edu = [e for e in (p.get("education") or []) if e.get("degree")]
    if w.get("style", "business") == "bullets":
        desig, comp, extra = job_parts(w.get("bullets") or [], as_split=False)   # this slide: team image pending
        occ = [(desig, "deg"), (comp, "name")] + [(e, "work") for e in extra]
    else:
        b = business_items(w)[0]
        lab = " ".join(str(b.get("type") or w.get("label") or "Business").replace("_", " ").split())
        occ = [(lab, "deg"), (b.get("name"), "name"), (paren(b.get("desc")), "work")]
    X_B, X_T, R = 70, 140, 1140
    k = 1.0
    while True:
        rows = []                                    # (kind, text, style, pitch, gap)
        tst = Style(gu="akhand_xb", lat="anek_sb", size=112 * k, color=BROWN)
        dst = Style(gu="akhand_xb", lat="barlow_xb", size=92 * k, color=BLACK)
        ist = Style(gu="akhand_xb", lat="barlow_m", size=60 * k, color=INSTITUTE)
        nst = Style(gu="akhand_xb", lat="barlowc_bi", size=84 * k, color=OCC_NAME)
        wst = Style(gu="akhand_xb", lat="barlowc_bi", size=64 * k, color=OCC_WORK)
        rows.append(("title", f"{first} નુ એજ્યુકેશન:", tst, tst.size * 1.05, 0))
        for i, e in enumerate(edu):
            big, small = deg_lines(e)
            g = 34 * k if i == 0 else 40 * k
            for j, ln in enumerate(ln for sg in big for ln in wrap_balanced(sg, dst, R - X_T)):
                rows.append(("bullet" if j == 0 else "text", ln, dst, dst.size * 1.08, g)); g = 0
            it = paren(e.get("institute"))
            for ln in [ln for sg in small + ([it] if it else []) for ln in wrap_balanced(sg, ist, R - X_T)]:
                rows.append(("text", ln, ist, ist.size * 1.3, 0))
        rows.append(("title", f"{first} નુ ઓક્યુપેશન:", tst, tst.size * 1.05, 70 * k))
        g, first_row = 34 * k, True
        for txt, kind in occ:
            if not txt:
                continue
            st = {"deg": dst, "name": nst, "work": wst}[kind]
            for ln in wrap_balanced(txt, st, R - X_T):
                rows.append(("bullet" if first_row else "text", ln, st, st.size * 1.12, g)); g, first_row = 0, False
        room = 1450 - 165
        lg = None
        if w.get("logo") or w.get("_logo_photo"):
            lg = _job_logo(ctx, w, 420, int(min(170, room - sum(r[3] + r[4] for r in rows) - 30)), 200)
        total = sum(r[3] + r[4] for r in rows) + (lg.height + 30 if lg else 0)
        if total <= room or k <= 0.55:
            break
        k -= 0.04
    y = 165 + max(0, (room - total) / 2)
    for kind, txt, st, pch, g in rows:
        y += g + pch
        base = y - pch * 0.24
        if kind == "title":
            draw_line(d, txt, fit(txt, st, 1100), 600, base)
            continue
        if kind == "bullet":
            b = st.size * 0.42
            cy = base - st.size * 0.36
            imgs.fill_rrect(im, (X_B, cy - b / 2, X_B + b, cy + b / 2), b * 0.25, ctx.accent)
        draw_line(d, txt, fit(txt, st, R - X_T), X_T, base, "left")
    if lg:
        _paste_logo(im, lg, X_T, "left", y + 30)
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


def job_parts(items: list, as_split: bool = True):
    """Job lines as on the team PSDs -> (designation, "at company", extra lines): "Manager at ABC, Pune" is split into
    "Manager" / "at ABC, Pune"; without " at " the 2nd line is the company."""
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return "", "", []
    # "Manager at ABC" / "Working as an Accountant, Rajkot" (team PSDs: "as a / as an" is split like "at")
    m = re.split(r"\s+(?=(?:at|as an?)\s)" if as_split else r"\s+(?=at\s)", items[0], maxsplit=1, flags=re.I)
    if len(m) == 2:
        return m[0], m[1], items[1:]
    return items[0], (items[1] if len(items) > 1 else ""), items[2:]


_JOIN = re.compile(r"^(?:at|as an?)\s", re.I)


def job_roles(items: list) -> list:
    """Job lines grouped into roles (team PSDs Drashti / Henal, 17 Oct 2026): a line in brackets or starting with
    "at" / "as a" belongs to the role above it; any other line starts a new role."""
    roles = []
    for it in (i.strip() for i in items if i and i.strip()):
        if roles and ((it.startswith("(") and it.endswith(")")) or _JOIN.match(it)):
            roles[-1].append(it)
        else:
            roles.append([it])
    return roles


OCC_COMP_GIRL = "#A71043"   # "at Company" on the girl PSDs (crimson); boys keep the dark brown OCC_NAME


def comp_color(ctx: Ctx) -> str:
    return OCC_COMP_GIRL if ctx.theme == "girl" else OCC_NAME


def split_job(items: list):
    """-> (designation, company/area, extra lines). "X at Y" in one line is split."""
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return "", "", []
    if len(items) == 1:
        m = re.split(r"\s+at\s+", items[0], maxsplit=1, flags=re.I)
        return (m[0], m[1], []) if len(m) == 2 else (items[0], "", [])
    return items[0], items[1], items[2:]


def _job_logo(ctx: Ctx, w: dict, max_w: int, max_h: int, card_h: int | None = None):
    """Company logo for a job card: plain margins trimmed, a white / light background made transparent
    (a logo / visiting card on a coloured background keeps it, as a rounded label, up to card_h tall), or None."""
    src = _logo_src(ctx, w)
    if src is None or max_h < 60:
        return None
    return _logo_img(src, max_w, max_h, card_h)


def _logo_img(src, max_w: int, max_h: int, card_h: int | None = None) -> Image.Image:
    lg = imgs.contain(src, max_w, max_h, trim_bg=True, key_bg=True)
    if lg.getchannel("A").getextrema()[0] == 255:      # still opaque (coloured background, e.g. a visiting card)
        if card_h and card_h > max_h:                   # a card has text on it: may be shown larger
            lg = imgs.contain(src, max_w, card_h, trim_bg=True, key_bg=True)
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


# ---------------------------------------------------------------- occupation card (team PSDs, 15 Oct 2026)
OCC_NAME = "#4A2409"       # company / business name (dark brown, Barlow Condensed Bold Italic)
OCC_WORK = "#875632"       # work line in brackets (golden brown, like the education card's college line)


def occ_titles(d, ctx: Ctx, first: str, y_shift: float = 0):
    """'<first> નુ ઓક્યુપેશન:' (brown) + 'જોબ / વ્યવસાય' (theme colour), as on every team PSD."""
    t = f"{first} નુ ઓક્યુપેશન:"
    st = Style(gu="akhand_xb", lat="anek_sb", size=126.9, color=BROWN)
    draw_line(d, t, fit(t, st, 1100), 600, 297 + y_shift)
    st2 = Style(gu="akhand_xb", lat="anek_sb", size=151.4, color=ctx.accent)
    draw_line(d, "જોબ / વ્યવસાય", st2, 600, 487 + y_shift)


def paren(s: str) -> str:
    s = str(s or "").strip()
    return s if not s or (s.startswith("(") and s.endswith(")")) else f"({s})"


def _stack(im, d, blocks, x: int, maxw: int, top: int, bottom: int, centre: float | None = None, logo=None):
    """Left-aligned text blocks [(text, style, max_lines, gap_before)] (+ a logo below), shrunk together until they fit
    between top and bottom; centred on `centre` (the photo's middle) when given."""
    k = 1.0
    while True:
        rows, ok = [], True
        for txt, st, n, gap in blocks:
            for seg in hard_lines(txt):
                s2 = st.scaled(k)
                ls = [seg] if measure(seg, s2.scaled(0.86)) <= maxw else wrap_balanced(seg, s2, maxw)
                ok = ok and len(ls) <= n
                for li, ln in enumerate(ls):
                    rows.append((ln, s2, s2.size * 1.16, gap * k if li == 0 else 0))
                    gap = 0
        lg = logo(bottom - top - sum(p + g for *_, p, g in rows) - 40) if logo else None
        total = sum(p + g for *_, p, g in rows) + (lg.height + 40 if lg else 0)
        if (ok and total <= bottom - top) or k <= 0.55:
            break
        k -= 0.05
    y = max(top, (centre - total / 2) if centre else top)
    for ln, st, p, g in rows:
        y += g + p
        draw_line(d, ln, fit(ln, st, maxw), x, y - p * 0.24, "left")
    if lg:
        _paste_logo(im, lg, x, "left", y + 40)
    return im


def work(ctx: Ctx, w: dict, first: str, fallback_photo=None) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    occ_titles(d, ctx, first)
    if w.get("photo") and not w.get("logo"):
        p0 = ctx.photo(w["photo"])
        # the app's box is "LOGO / COMPANY CARD": without a face it is a logo or a visiting card, drawn in the text
        # column (never cut by the photo frame); a candidate photo goes on the right. With a face: the person, as before.
        if not imgs.faces(*p0.key):
            w = dict(w, photo=None, _logo_photo=p0)
    bizs = business_items(w)
    if w.get("style", "business") != "bullets" and len(bizs) > 1:
        return _business_list(im, d, ctx, w, bizs)       # 2-4 businesses: full width, no candidate photo (PSDs)
    if w.get("style", "business") == "bullets" and 2 <= len(job_roles(w.get("bullets") or [])) <= 4:
        return _job_roles_card(im, d, ctx, w, job_roles(w.get("bullets") or []))   # 2-4 roles: bullets, no photo
    ph = ctx.photo(w.get("photo")) or ctx.photo(fallback_photo)
    right = 790 if ph else 1150
    if ph:
        imgs.paste_photo(im, ph, (840, 582, 1174, 1284), 66, ctx.privacy)
    x, maxw = (50, right - 50) if ph else (110, 980)
    lab = Style(gu="akhand_xb", lat="barlowc_b", size=96, color=BLACK, upper=True)
    if w.get("style", "business") == "bullets":
        items = w.get("bullets", [])
        if len(items) > 3:  # a real list of roles: bullets (company logo, if any, above the list)
            lg = _job_logo(ctx, w, min(maxw, 560), 150)
            top = 580 + (lg.height + 40 if lg else 0)
            if lg:
                _paste_logo(im, lg, x, "left", 580)
            bullet_list(im, d, items, ctx.accent, ctx.job_bullet, 50,
                        100 if ctx.job_bullet == "dot" else 130, right, top + 100, 72, 1440, center_top=top)
            return im
        desig, comp, extra = job_parts(items)         # "Manager at ABC" -> designation / "at ABC" (PSD)
        blocks = [(desig, lab, 2, 0)]
        if comp:
            blocks.append((comp, Style(gu="akhand_xb", lat="barlowc_bi", size=104, color=comp_color(ctx)), 3, 30))
        for e in extra:
            blocks.append((e, Style(gu="akhand_xb", lat="barlowc_bi", size=80, color=OCC_WORK), 2, 20))
    else:                                           # one business: label, name, (work), logo below (Viral / Raj PSDs)
        b = bizs[0] if bizs else {"type": w.get("label", ""), "name": w.get("company", ""), "desc": w.get("desc", "")}
        label = " ".join(str(b.get("type") or w.get("label") or "Business").replace("_", " ").split())
        blocks = [(label, lab, 1, 0)]
        if b.get("name"):
            blocks.append((b["name"], Style(gu="akhand_xb", lat="barlowc_bi", size=112, color=OCC_NAME), 3, 34))
        if b.get("desc"):
            blocks.append((paren(b["desc"]), Style(gu="akhand_xb", lat="barlowc_bi", size=80, color=OCC_WORK), 3, 26))
    logo = (lambda room: _job_logo(ctx, w, min(maxw, 600), min(260, room), min(320, room))) \
        if (w.get("logo") or w.get("_logo_photo")) else None
    return _stack(im, d, blocks, x, maxw, 580, 1440, 933 if ph else None, logo)


def _job_roles_card(im, d, ctx: Ctx, w: dict, roles: list) -> Image.Image:
    """2-4 job roles (team PSDs Drashti / Henal, 17 Oct 2026): full width, no candidate photo; per role a theme-colour
    bullet, the DESIGNATION, "at Company" under it (girl: crimson), a line in brackets under its role; the logo under
    the first role."""
    X_B, X_T, R = 56, 110, 1150
    k = 1.0
    while True:
        rows = []                                   # (text, style, pitch, gap, bullet)
        for ri, role in enumerate(roles):
            desig, comp, extra = job_parts(role)
            gap = (0 if ri == 0 else 70) * k
            parts = [(desig, Style(gu="akhand_xb", lat="barlowc_b", size=96 * k, color=BLACK, upper=True), 1.12)]
            if comp:
                parts.append((comp, Style(gu="akhand_xb", lat="barlowc_bi", size=86 * k, color=comp_color(ctx)), 1.14))
            parts += [(e, Style(gu="akhand_xb", lat="barlowc_bi", size=72 * k, color=OCC_WORK), 1.18) for e in extra]
            bullet = True
            for txt, st, pk in parts:
                for ln in wrap_balanced(txt, st, R - X_T):
                    rows.append((ln, st, st.size * pk, gap, bullet)); gap, bullet = 0, False
            if ri == 0:
                rows.append(("__logo__", None, 0, 0, False))
        lg = None
        if w.get("logo") or w.get("_logo_photo"):
            lg = _job_logo(ctx, w, int(420 * k), int(190 * k), int(230 * k))
        total = sum(r[2] + r[3] for r in rows) + (lg.height + 40 if lg else 0)
        if total <= 1440 - 575 or k <= 0.55:
            break
        k -= 0.05
    y = 575 + max(0, (1440 - 575 - total) / 2 - 20)
    for txt, st, p, g, bullet in rows:
        if txt == "__logo__":
            if lg:
                _paste_logo(im, lg, X_T, "left", y + 26)
                y += lg.height + 40
            continue
        y += g + p
        base = y - p * 0.24
        if bullet:
            b = max(20, st.size * 0.30)
            cy = base - st.size * 0.33
            imgs.fill_circle(im, (X_B, cy - b / 2, X_B + b, cy + b / 2), ctx.accent)
        draw_line(d, txt, fit(txt, st, R - X_T), X_T, base, "left")
    return im


def list_heading(w: dict, bizs: list) -> str:
    """Heading above 2-4 businesses: the team's own heading, else "Business" only when no row has a Type (team PSDs,
    17 Oct 2026: a typed row shows its Type as its own bulleted line, so no extra heading)."""
    typed = any(" ".join(str(b.get("type") or "").split()) for b in bizs)
    return business_heading(w) or ("" if typed else "Business")


def _business_list(im, d, ctx: Ctx, w: dict, bizs: list) -> Image.Image:
    """2-4 businesses (Siddarth / Rajan / Viraj PSDs): heading ("BUSINESS" or the team's own heading), then per business
    a theme-colour bullet, the name (dark brown italic) and the work in brackets (golden brown italic), a business
    logo on the right of its row when given; a Family Business row gets its own bulleted "FAMILY BUSINESS" line."""
    # team PSDs (Mitanshi, Darshan, 17 Oct 2026): rows with a Type show it as their own bulleted line and there is
    # no "BUSINESS" heading; the heading stays when no row has a Type (Dhaval) or the team set their own heading
    head = list_heading(w, bizs)
    X_B, X_T, R = 56, 110, 1150
    k = 1.0
    while True:
        rows = []                                   # (text, style, pitch, gap, bullet, logo_row)
        if head:
            hs = fit(head, Style(gu="akhand_xb", lat="barlowc_b", size=112 * k, color=BLACK, upper=True), R - X_T)
            rows.append((head, hs, hs.size * 1.1, 0, False, None))
        ok, logos = True, []
        for bi, b in enumerate(bizs):
            lg = None
            if b.get("logo"):
                lg = _logo_img(_logo_src(ctx, {"logo": b["logo"]}), int(300 * max(k, 0.7)), int(170 * max(k, 0.7)))
            tw = R - X_T - (lg.width + 30 if lg else 0)
            gap, bullet, start = (40 if bi == 0 else (58 if len(bizs) < 3 else 34)) * k, True, len(rows)
            bt = " ".join(str(b.get("type") or "").replace("_", " ").split())
            if bt:
                st = Style(gu="akhand_xb", lat="barlowc_b", size=100 * k, color=BLACK, upper=True)
                rows.append(("Family Business" if is_family_business(bt) else bt, st, st.size * 1.12, gap, True, None))
                gap, bullet = 8 * k, False
            nst = Style(gu="akhand_xb", lat="barlowc_bi", size=94.7 * k, color=OCC_NAME)
            for seg in hard_lines(b.get("name")):
                ls = [seg] if measure(seg, nst.scaled(0.86)) <= tw else wrap_balanced(seg, nst, tw)
                ok = ok and len(ls) <= 2
                for ln in ls:
                    rows.append((ln, nst, nst.size * (1.14 if len(bizs) < 3 else 1.06), gap, bullet, None)); gap, bullet = 0, False
            wst = Style(gu="akhand_xb", lat="barlowc_bi", size=77.5 * k, color=OCC_WORK)
            for seg in hard_lines(b.get("desc")):
                seg = paren(seg)
                ls = [seg] if measure(seg, wst.scaled(0.86)) <= tw else wrap_balanced(seg, wst, tw)
                ok = ok and len(ls) <= 2
                for ln in ls:
                    rows.append((ln, wst, wst.size * (1.18 if len(bizs) < 3 else 1.1), gap, bullet, None)); gap, bullet = 0, False
            if lg:
                logos.append((start, len(rows), lg))
        total = sum(r[2] + r[3] for r in rows)
        if (ok and total <= 1440 - 575) or k <= 0.55:
            break
        k -= 0.05
    y = 575 + max(0, (1440 - 575 - total) / 2 - 20)
    ys = []
    for txt, st, p, g, bullet, _ in rows:
        y += g + p
        base = y - p * 0.24
        ys.append((y - p, y))
        if bullet:
            b = max(22, st.size * 0.34)
            cy = base - st.size * 0.33
            imgs.fill_rrect(im, (X_B, cy - b / 2, X_B + b, cy + b / 2), max(3, b * 0.2), ctx.accent)
        draw_line(d, txt, fit(txt, st, R - X_T), X_T if txt is not head else X_B, base, "left")
    for a, b2, lg in logos:                         # logo on the right, centred on its business
        top, bot = ys[a][0], ys[b2 - 1][1]
        im.paste(lg, (int(R - lg.width), int((top + bot) / 2 - lg.height / 2)), lg)
    return im


def business_items(w: dict) -> list:
    """The candidate's businesses: work.businesses [{type, name, desc}] (app rows, max 4) or the single
    company / desc (type = the occupation label)."""
    out = []
    for x in (w.get("businesses") or [])[:4]:
        x = x or {}
        n, ds = str(x.get("name") or "").strip(), str(x.get("desc") or "").strip()
        if n or ds:
            out.append({"type": " ".join(str(x.get("type") or "").split()), "name": n, "desc": ds,
                        "logo": x.get("logo") or (w.get("logo") if not out else None)})   # row 1 = the profile logo
    if not out and (w.get("company") or w.get("desc")):
        out.append({"type": str(w.get("label") or ""), "name": str(w.get("company") or ""), "desc": str(w.get("desc") or "")})
    return out


def business_heading(w: dict) -> str:
    """2-4 businesses: the optional heading over all of them (work.heading, e.g. "Businesses in Kolhapur": the team's
    own occupation type, written by the app), shown once above the list and said first in the narration."""
    if len(business_items(w or {})) < 2:
        return ""
    return " ".join(str((w or {}).get("heading") or "").split()).rstrip(":")


def is_family_business(t) -> bool:
    return " ".join(str(t or "").replace("_", " ").lower().split()) == "family business"


def property_card(ctx: Ctx, items: list, first: str) -> Image.Image:
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    title1(d, f"{first} નો પરિચય")
    title2(d, ctx, "Income / Property:", 166.7, 521, upper=True)
    # team PSDs (17 Oct 2026): bigger text in Anek Gujarati SemiCondensed Bold (shrinks for 4+ lines)
    bullet_list(im, d, items, ctx.accent, "square", 86, 176, 1131, 753, 118, 1440, lat="anek_semi_b",
                b_side=58, b_off=60, line_k=1.18, gap_k=0.85, center_top=600)
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
    """Returns (label_img, text_img). The label image has a 30 px left margin and an 18 px gap after.
    label=None: a square bullet in the theme colour (blue / pink) instead of a word."""
    lab = Style(gu="anek_sb", lat="anek_sb", size=70, color=ctx.accent)
    txt = Style(gu="anek_sb", lat="anek_sb", size=70, color=BLACK, upper=True)
    bl = _ink_baseline(_line_fn, label or "HOBBY:", lab)          # caps: centre on the label's ink
    if label:
        lw = int(measure(label, lab)) + 30 + 18
        li = Image.new("RGB", (lw, STRIP_H), WHITE)
        draw_line(ImageDraw.Draw(li), label, lab, 30, bl, "left")
    else:
        b = 40                                                    # like the bullets of the Income / Property card
        lw = 30 + b + 26
        li = Image.new("RGB", (lw, STRIP_H), WHITE)
        imgs.fill_rrect(li, (30, (STRIP_H - b) / 2, 30 + b, (STRIP_H + b) / 2), 7, ctx.accent)
    s = ", ".join(hobbies)
    tw = int(measure(s, txt)) + 10
    ti = Image.new("RGB", (tw, STRIP_H), WHITE)
    draw_line(ImageDraw.Draw(ti), s, txt, 0, bl, "left")
    return li, ti


def award_items(p: dict) -> list:
    """Awards / achievements (max 3 lines)."""
    return [str(x).strip() for x in (p.get("awards") or []) if str(x).strip()][:3]


def single_award(p: dict):
    """The text when the profile has exactly ONE award / achievement line: shown in the gallery's white strip
    (first, before the property line and the hobbies) instead of an own card. Otherwise None."""
    a = award_items(p)
    return a[0] if len(a) == 1 else None


def awards_card(ctx: Ctx, items: list, first: str) -> Image.Image:
    """Awards / achievements: own card after the occupation (and past experience) card, music only."""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    if len(items) == 1:                  # one achievement on its own slide: unchanged until the team's image (CT, 17 Oct)
        title1(d, f"{first} નો પરિચય")
        title2(d, ctx, "Awards / Achievements:", 166.7, 521, upper=True)
        bullet_list(im, d, items, ctx.accent, "square", 86, 176, 1131, 753, 93, 1440,
                    b_side=70, b_off=63, line_k=1.39, gap_k=1.04)
        return im
    # team PSDs (Henal, Vicky, 17 Oct 2026): only the title "Achievements:" (big, theme colour; boys in capitals),
    # round bullets, Anek Gujarati Condensed (girl: dark brown). ONE achievement on its own slide: team image pending.
    t = "Achievements:"
    draw_line(d, t, Style(gu="akhand_xb", lat="anek_b", size=190, color=ctx.accent, upper=ctx.theme == "boy"), 600, 400)
    col = "#46300D" if ctx.theme == "girl" else BLACK
    bullet_list(im, d, items, ctx.accent, "dot", 80, 150, 1150, 700, 120, 1430, lat="anek_sb", color=col,
                line_k=1.12, gap_k=1.2, center_top=540)
    return im


def single_property(p: dict):
    """The text when the profile has exactly ONE Income / Property line: it is shown in the gallery's white strip
    after a theme-colour bullet (no "PROPERTY:" word) instead of an own card. Otherwise None."""
    if p.get("property_card"):           # app tick "Income / Property on its own slide" (team PSDs)
        return None
    items = [str(x).strip() for x in (p.get("property") or []) if str(x).strip()]
    return items[0] if len(items) == 1 else None


STATIC_SECONDS = 3.0   # a fixed sub-line (sect / info) stays at least this long


def gallery_sublines(ctx: Ctx, p: dict) -> list:
    """Rotating white strip under the gallery name band: [(state, seconds needed)].
    state = ("ticker", label_img, text_img) or ("static", img). A long ticker scrolls ONCE to its end (never cut)."""
    from .config import TIMING
    out = []
    tick = []                          # order (CT, 12 Oct 2026): one award, one property line, hobbies, સમાજ, info
    sa = single_award(p)
    if sa:
        tick.append(ticker_parts(ctx, [sa], None))
    sp = single_property(p)
    if sp:
        tick.append(ticker_parts(ctx, [sp], None))
    if p.get("hobbies"):
        tick.append(ticker_parts(ctx, p["hobbies"]))
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


def past_experience(ctx: Ctx, items: list, first: str, fallback_photo=None) -> Image.Image:
    """Card after the occupation card (music only). Team PSDs (Nehal, Nikunj, Nirali, Vatstal, 17 Oct 2026): only the
    title "Past Experience:" (brown); ONE item: big, in the job style (DESIGNATION / "at Company"), logo BELOW the
    text, candidate photo on the right (centred without photo); 2-3 items: full width, no photo, a round bullet per
    item, its logo under it."""
    im = canvas(ctx)
    d = ImageDraw.Draw(im)
    t = "Past Experience:"
    draw_line(d, t, Style(gu="akhand_xb", lat="anek_sb", size=170, color=EDU_SUB_GIRL), 600, 370)
    if len(items) == 1:
        it = items[0]
        ph = ctx.photo(fallback_photo)
        if ph:
            imgs.paste_photo(im, ph, (840, 520, 1174, 1222), 66, ctx.privacy)
        x, maxw = (50, 740) if ph else (110, 980)
        desig, comp, extra = job_parts([it["text"]])
        lab = Style(gu="akhand_xb", lat="barlowc_b", size=104, color=BLACK, upper=True)
        blocks = [(desig, lab, 2, 0)]
        if comp:
            blocks.append((comp, Style(gu="akhand_xb", lat="barlowc_bi", size=104, color=comp_color(ctx)), 3, 30))
        logo = None
        if it.get("logo"):
            src_img = imgs.opaque(ctx.photo(it["logo"]).load())
            logo = lambda room: _logo_img(src_img, min(maxw, 560), int(min(240, room))) if room >= 60 else None
        return _stack(im, d, blocks, x, maxw, 500, 1440, 871 if ph else 960, logo)
    X_B, X_T, R = 70, 140, 1150
    k = 1.0
    while True:
        rows = []
        for it in items:
            st = Style(gu="akhand_xb", lat="anek_sb", size=100 * k, color=BLACK)
            ls = wrap_balanced(it["text"], st, R - X_T)
            lg = (_logo_img(imgs.opaque(ctx.photo(it["logo"]).load()), int(380 * k), int(120 * k))
                  if it.get("logo") else None)
            rows.append((ls, st, lg))
        total = sum(st.size * 1.1 * len(ls) + (lg.height + 24 * k if lg else 0) for ls, st, lg in rows) + 70 * k * (len(rows) - 1)
        if total <= 1440 - 470 or k <= 0.55:
            break
        k -= 0.04
    y = 470 + max(0, (1440 - 470 - total) / 2)
    for i, (ls, st, lg) in enumerate(rows):
        if i:
            y += 70 * k
        for j, ln in enumerate(ls):
            y += st.size * 1.1
            base = y - st.size * 0.24
            if j == 0:
                b = st.size * 0.30
                cy = base - st.size * 0.30
                imgs.fill_circle(im, (X_B, cy - b / 2, X_B + b, cy + b / 2), ctx.accent)
            draw_line(d, ln, fit(ln, st, R - X_T), X_T, base, "left")
        if lg:
            _paste_logo(im, lg, X_T, "left", y + 24 * k)
            y += lg.height + 24 * k
    return im
