"""Text rendering with Pillow + RAQM.

Akhand Gujarati has no Latin letters, so every line is split into runs:
Gujarati letters -> `gu` font, Latin letters -> `lat` font. Digits, spaces and
punctuation stay in the current run when that font has the glyph.
Akhand's half-શ looks like ર (શ્વ in વિશ્વાસ reads "વિરવાસ"), so a cluster શ્ + consonant (not શ્ર, which Akhand
draws correctly) is drawn with Anek Gujarati (same condensed style, proper શ્વ / શ્ચ / શ્ન ligatures), sized to the
same letter height (`GU_FALLBACK`).
All drawing is anchored on the baseline, so positions match PSD type layers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from functools import lru_cache

from fontTools.ttLib import TTFont
from PIL import ImageFont, features

from .config import FONTS

if not features.check("raqm"):
    raise SystemExit("Pillow is built without RAQM: Gujarati shaping would break. "
                     "Install libraqm and reinstall Pillow (see README).")

_GU = re.compile(r"[\u0A80-\u0AFF\u200C\u200D]")
_LAT = re.compile(r"[A-Za-z\u00C0-\u024F]")
# શ + virama + consonant other than ર (+ more virama-consonant pairs, nukta, vowel signs, anusvara / candrabindu / visarga)
_SHA_CLUSTER = re.compile("\u0AB6\u0ACD(?!\u0AB0)[\u0A95-\u0AB9](?:\u0ABC)?(?:\u0ACD[\u0A95-\u0AB9](?:\u0ABC)?)*"
                          "[\u0ABE-\u0AC5\u0AC7-\u0AC9\u0ACB\u0ACC\u0AE2\u0AE3]*[\u0A81-\u0A83]*")
GU_FALLBACK = {"akhand_xb": "anek_b", "akhand_b": "anek_sb"}   # font for the clusters above, same weight look


@dataclass(frozen=True)
class Style:
    gu: str = "akhand_xb"     # font key for Gujarati runs
    lat: str = "poppins_sb"   # font key for Latin runs
    size: float = 80          # px size of Gujarati runs
    lat_scale: float = 1.0    # Latin size = size * lat_scale
    color: str = "#000000"
    upper: bool = False

    def scaled(self, k: float) -> "Style":
        return replace(self, size=self.size * k)


@lru_cache(maxsize=None)
def font(key: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS[key]), max(4, int(size)),
                              layout_engine=ImageFont.Layout.RAQM)


@lru_cache(maxsize=None)
def _cmap(key: str) -> frozenset:
    return frozenset(TTFont(str(FONTS[key]), lazy=True).getBestCmap().keys())


def runs(text: str, st: Style):
    """Split text into [(font_key, px_size, lang, chunk)]."""
    if st.upper:
        text = text.upper()
    out, cur, buf = [], None, ""

    def key_of(kind):
        return st.gu if kind == "g" else st.lat

    for ch in text:
        if _GU.match(ch):
            kind = "g"
        elif _LAT.match(ch):
            kind = "l"
        else:
            kind = None
        if kind is None:
            # neutral char: keep in current run if that font has it
            if cur is not None and ord(ch) not in _cmap(key_of(cur)) and not ch.isspace():
                other = "l" if cur == "g" else "g"
                if buf:
                    out.append((cur, buf))
                cur, buf = other, ch
            else:
                buf += ch
            continue
        if cur is None:
            cur = kind
        if kind != cur:
            out.append((cur, buf))
            cur, buf = kind, ""
        buf += ch
    if buf:
        if cur is None:   # only neutral chars: use Gujarati font if it has them
            cur = "g" if all(ord(c) in _cmap(st.gu) or c.isspace() for c in buf) else "l"
        out.append((cur, buf))
    res = []
    for kind, chunk in out:
        k = key_of(kind)
        sz = st.size if kind == "g" else st.size * st.lat_scale
        if kind == "g" and k in GU_FALLBACK:
            res += _sha_split(k, sz, chunk)
            continue
        res.append((k, int(round(sz)), "gu" if kind == "g" else "en", chunk))
    return res


@lru_cache(maxsize=None)
def _height_ratio(key: str, fb: str) -> float:
    """Size factor so that the fallback font's શ has the same height as the main font's."""
    h = lambda k: (lambda b: b[3] - b[1])(font(k, 200).getbbox("\u0AB6", language="gu"))
    return h(key) / h(fb)


def _sha_split(key: str, size: float, chunk: str):
    """A Gujarati run with each શ્-cluster as its own run in the fallback font."""
    fb, out, i = GU_FALLBACK[key], [], 0
    for m in _SHA_CLUSTER.finditer(chunk):
        if m.start() > i:
            out.append((key, int(round(size)), "gu", chunk[i:m.start()]))
        out.append((fb, int(round(size * _height_ratio(key, fb))), "gu", m.group()))
        i = m.end()
    if i < len(chunk):
        out.append((key, int(round(size)), "gu", chunk[i:]))
    return out


def measure(text: str, st: Style) -> float:
    return sum(font(k, s).getlength(c, language=lg) for k, s, lg, c in runs(text, st))


def draw_line(draw, text: str, st: Style, x: float, baseline: float, align: str = "center"):
    """Draw one line. align: left | center | right (x is that edge/centre)."""
    w = measure(text, st)
    if align == "center":
        x0 = x - w / 2
    elif align == "right":
        x0 = x - w
    else:
        x0 = x
    for k, s, lg, c in runs(text, st):
        f = font(k, s)
        draw.text((x0, baseline), c, font=f, fill=st.color, anchor="ls", language=lg)
        x0 += f.getlength(c, language=lg)
    return w


def fit(text: str, st: Style, max_w: float, min_scale: float = 0.6) -> Style:
    """Shrink style until text fits max_w (never below min_scale)."""
    w = measure(text, st)
    if w <= max_w:
        return st
    k = max(min_scale, max_w / w)
    s2 = st.scaled(k)
    while measure(text, s2) > max_w and k > min_scale:
        k -= 0.01
        s2 = st.scaled(k)
    return s2


def wrap(text: str, st: Style, max_w: float) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if not cur or measure(trial, st) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def wrap_balanced(text: str, st: Style, max_w: float) -> list[str]:
    """Same line count as greedy wrap, but breaks chosen to make lines even
    (e.g. "Residence 3BHK / at Mulund" instead of "Residence 3BHK at / Mulund")."""
    greedy = wrap(text, st, max_w)
    n = len(greedy)
    words = text.split()
    if n <= 1 or len(words) > 40:
        return greedy
    if n == 2:  # prefer a top-heavy pair: first line >= second, as short as possible
        cands = []
        for j in range(1, len(words)):
            a, b = " ".join(words[:j]), " ".join(words[j:])
            wa, wb = measure(a, st), measure(b, st)
            if wa <= max_w and wb <= max_w:
                cands.append((0 if wa >= wb else 1, max(wa, wb), [a, b]))
        if cands:
            return min(cands, key=lambda c: (c[0], c[1]))[2]
        return greedy
    from functools import lru_cache as _lc

    @_lc(None)
    def best(i, k):  # words[i:] into k lines -> (max_width, lines)
        if k == 1:
            ln = " ".join(words[i:])
            return measure(ln, st), (ln,)
        res = (float("inf"), ())
        for j in range(i + 1, len(words) - k + 2):
            ln = " ".join(words[i:j])
            w = measure(ln, st)
            if w > max_w:
                break
            mw, rest = best(j, k - 1)
            cand = (max(w, mw), (ln,) + rest)
            if cand[0] < res[0]:
                res = cand
        return res

    mw, lines = best(0, n)
    return list(lines) if lines and mw <= max_w else greedy


def wrap_fit(text: str, st: Style, max_w: float, max_lines: int, min_scale: float = 0.6):
    """Wrap into <= max_lines, shrinking if needed. Returns (lines, style)."""
    k = 1.0
    while True:
        s2 = st.scaled(k)
        lines = wrap_balanced(text, s2, max_w)
        if len(lines) <= max_lines and all(measure(l, s2) <= max_w for l in lines):
            return lines, s2
        if k <= min_scale:
            return lines, s2
        k -= 0.03
