"""Timeline + frame generation + FFmpeg encoding (one encode, outro concatenated)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from . import cards, imgs
from .config import FPS, FPS_DEN, FPS_NUM, FRAMING, H, HOLD_EXTRA, OUTRO, TIMING, W
from .narration import estimate_seconds

T = TIMING
PHOTO_H = 1110     # gallery photo area: from the top (behind the title bar) down to the name band
HEADER_H = 150     # title bar height: faces are framed below it


def hold_for(scene_id: str, overrides: dict | None = None) -> float:
    key = "sibling" if scene_id.startswith("sibling") else scene_id
    if overrides and scene_id in overrides:
        return float(overrides[scene_id])
    if overrides and key in overrides:
        return float(overrides[key])
    return T["hold"] + HOLD_EXTRA.get(key, 0.0)


def plan(scenes, vo: dict | None = None, holds: dict | None = None):
    """Return timeline [{id, kind, start, dur, vo_start, vo_len}] and total seconds."""
    tl, t = [], 0.0
    for sc in scenes:
        if sc.id == "cover":
            tl.append(dict(id=sc.id, kind="card", start=t, dur=T["cover"], vo_start=None, vo_len=0.0))
        elif sc.kind == "gallery":
            dur = len(sc.extra["photos"]) * T["gallery_photo"]
            tl.append(dict(id=sc.id, kind="gallery", start=t, dur=dur, vo_start=None, vo_len=0.0))
        else:
            if vo is None:
                vlen = estimate_seconds(sc.text) if sc.text else 0.0
            else:
                vlen = vo.get(sc.id, 0.0)
            if sc.id == "intro":
                lead, mn, after = T["intro_lead"], T["min_intro"], T["intro_tail"]
            else:
                lead, mn, after = T["lead"], T["min_card"], T["tail"] + hold_for(sc.id, holds)
            dur = max(mn, lead + vlen + after) if vlen else mn
            tl.append(dict(id=sc.id, kind="card", start=t, dur=round(dur, 3),
                           vo_start=round(t + lead, 3) if vlen else None, vo_len=round(vlen, 3)))
        t += tl[-1]["dur"]
    return tl, t


class Gallery:
    def __init__(self, ctx, p, photos, start, dur):
        self.ctx, self.photos, self.start, self.dur = ctx, photos, start, dur
        self.overlay = cards.gallery_overlay(ctx, p)
        self.q = 1.25
        self._cache = {}
        states = []
        if p.get("hobbies"):
            li, ti = cards.ticker_parts(ctx, p["hobbies"])
            states.append(("ticker", li, ti))
        if p.get("sect"):
            states.append(("static", cards.strip_static(ctx, p["sect"], "sect")))
        info = cards.info_line(p)
        if info:
            states.append(("static", cards.strip_static(ctx, info, "info")))
        self.states = states or [("static", Image.new("RGB", (W, 128), "white"))]

    def _base(self, i):
        """(zoom-ready image, zoom anchor, top offset) for gallery photo i; the anchor is the face/chest point."""
        if i not in self._cache:
            self._cache = {}
            im, anchor, dy = imgs.cover_reserve(self.photos[i], W, PHOTO_H, HEADER_H, self.q,
                                                FRAMING["gallery_max_upscale"] / T["zoom_end"])
            im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=3))   # crisper after enlarging
            self._cache[i] = (imgs.apply_privacy(im, self.ctx.privacy), anchor, dy)
        return self._cache[i]

    def _strip(self, st, u):
        if st[0] == "static":
            return st[1]
        _, li, ti = st
        strip = Image.new("RGB", (W, 128), "white")
        lw = li.width
        avail = W - lw - 20
        if ti.width <= avail:
            # fits: centre "HOBBY: TEXT" as one line
            x0 = (W - (lw - 30 + ti.width)) // 2
            strip.paste(li.crop((30, 0, lw, 128)), (x0, 0))
            strip.paste(ti, (x0 + lw - 30, 0))
            return strip
        else:
            gap = 160
            off = (max(0.0, u - 0.8) * T["ticker_px_s"]) % (ti.width + gap)   # 0.8 s hold first
            region = Image.new("RGB", (avail, 128), "white")
            region.paste(ti, (int(-off), 0))
            region.paste(ti, (int(-off + ti.width + gap), 0))
            strip.paste(region, (lw, 0))
        strip.paste(li, (0, 0))
        return strip

    def frame(self, t):
        u = t - self.start
        n = len(self.photos)
        i = min(n - 1, int(u / T["gallery_photo"]))
        ph = (u - i * T["gallery_photo"]) / T["gallery_photo"]
        s = 1.0 + (T["zoom_end"] - 1.0) * ph
        q = self.q
        base, (cx, cy), dy = self._base(i)      # zoom towards the face, not the photo centre
        data = (q / s, 0, q * (cx - cx / s), 0, q / s, q * (cy - cy / s))
        photo = base.transform((W, PHOTO_H - dy), Image.AFFINE, data, Image.BICUBIC)
        fr = imgs.background().convert("RGBA")
        fr.paste(photo, (0, dy))
        fr = Image.alpha_composite(fr, self.overlay).convert("RGB")
        # rotating sub-line
        k = len(self.states)
        seg = self.dur / k
        j = min(k - 1, int(u / seg))
        loc = u - j * seg
        strip = self._strip(self.states[j], loc)
        xf = T["subline_xfade"]
        if j < k - 1 and (seg - loc) < xf / 2:
            nxt = self._strip(self.states[j + 1], 0.0)
            a = 0.5 - (seg - loc) / xf
            strip = Image.blend(strip, nxt, max(0.0, min(1.0, a)))
        elif j > 0 and loc < xf / 2:
            prv = self._strip(self.states[j - 1], seg)
            a = 0.5 + loc / xf
            strip = Image.blend(prv, strip, max(0.0, min(1.0, a)))
        fr.paste(strip, (0, 1372))
        return fr


def frames(scenes, tl, ctx, p):
    """Yield RGB bytes for every frame of the main part."""
    total = tl[-1]["start"] + tl[-1]["dur"]
    n = int(round(total * FPS))
    arrs = {}
    gal = {}
    for sc, e in zip(scenes, tl):
        if sc.kind == "card":
            arrs[sc.id] = np.asarray(sc.image.convert("RGB"), dtype=np.uint8)
        else:
            gal[sc.id] = Gallery(ctx, p, sc.extra["photos"], e["start"], e["dur"])
    starts = [e["start"] for e in tl]
    cache = {}

    def xf(a, b):      # dissolve length between two cards (short one out of the cover)
        return T["cover_xfade"] if "cover" in (a["id"], b["id"]) else T["dissolve"]
    for f in range(n):
        t = f / FPS
        i = max(0, np.searchsorted(starts, t, side="right") - 1)
        e = tl[i]
        if e["kind"] == "gallery":
            yield gal[e["id"]].frame(t).tobytes()
            continue
        cur = arrs[e["id"]]
        end = e["start"] + e["dur"]
        dn = xf(e, tl[i + 1]) if i + 1 < len(tl) else 0
        dp = xf(tl[i - 1], e) if i > 0 else 0
        if i + 1 < len(tl) and tl[i + 1]["kind"] == "card" and t > end - dn / 2:
            a = (t - (end - dn / 2)) / dn
            out = _blend(cur, arrs[tl[i + 1]["id"]], a)
        elif i > 0 and tl[i - 1]["kind"] == "card" and t < e["start"] + dp / 2:
            a = (t - (e["start"] - dp / 2)) / dp
            out = _blend(arrs[tl[i - 1]["id"]], cur, a)
        else:
            if e["id"] not in cache:
                cache = {e["id"]: cur.tobytes()}
            yield cache[e["id"]]
            continue
        yield out.tobytes()


def _blend(a, b, alpha):
    alpha = float(min(1.0, max(0.0, alpha)))
    return (a.astype(np.float32) * (1 - alpha) + b.astype(np.float32) * alpha + 0.5).astype(np.uint8)


def _gain_to(wav: Path, lufs: float) -> float:
    """dB gain that brings the integrated loudness of `wav` to `lufs` (measured by ffmpeg's EBU R128 meter)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return (lufs - float(m[-1])) if m else 0.0


def outro_duration() -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(OUTRO)], capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def encode(frame_iter, audio_wav: Path, total_dur: float, out: Path, outro: bool = True,
           preset: str = "medium", crf: int = 20, loudness: float | None = None):
    """Video: rendered frames (+ outro clip's picture). Audio: ONE mixed track for the whole length
    (voice + music + outro voice), so the music continues under the outro."""
    fr = f"{FPS_NUM}/{FPS_DEN}"
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-framerate", fr, "-i", "pipe:0", "-i", str(audio_wav)]
    # one fixed gain for the whole track (no loudness "pumping": the music stays at one level) + a peak limiter
    ln = f"volume={_gain_to(audio_wav, loudness):.2f}dB,alimiter=limit=0.84:attack=5:release=50:level=false," \
        if loudness is not None else ""
    a = (f"[1:a]{ln}aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,"
         f"apad,atrim=0:{total_dur:.4f}[a]")
    if outro:
        cmd += ["-i", str(OUTRO)]
        fc = (f"[0:v]setsar=1,format=yuv420p[v0];"
              f"[2:v]scale={W}:{H},setsar=1,fps={fr},format=yuv420p[v1];"
              f"[v0][v1]concat=n=2:v=1:a=0[v];{a}")
    else:
        fc = f"[0:v]setsar=1,format=yuv420p[v];{a}"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", preset,
            "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", fr, "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for b in frame_iter:
            proc.stdin.write(b)
    finally:
        proc.stdin.close()
        rc = proc.wait()
    if rc != 0:
        raise SystemExit(f"ffmpeg failed ({rc})")
