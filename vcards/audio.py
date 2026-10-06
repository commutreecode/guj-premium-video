"""Voice splitting/alignment and final audio mix (numpy + ffmpeg only)."""
from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np

from .config import AUDIO

SR = AUDIO["sr"]


def decode(path: Path, sr: int = SR, channels: int = 1) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", str(channels),
           "-ar", str(sr), "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    return x.reshape(-1, channels) if channels > 1 else x


def write_wav(path: Path, stereo: np.ndarray, sr: int = SR):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def _frames_db(x: np.ndarray, sr: int, hop: float = 0.01):
    n = int(sr * hop)
    m = len(x) // n
    fr = x[: m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9), hop


def pauses(x: np.ndarray, sr: int, min_gap: float = 0.22):
    """Return (gaps, threshold) where gaps = [(start_s, end_s)] of silence inside the speech."""
    db, hop = _frames_db(x, sr)
    ref = np.percentile(db, 90)
    thr = float(np.clip(ref - 32, -60, -35))
    sil = db < thr
    gaps, i, n = [], 0, len(sil)
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]:
                j += 1
            if (j - i) * hop >= min_gap:
                gaps.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    return gaps, thr


def align(voice: np.ndarray, sr: int, expected: list[float]):
    """Split voice into len(expected) pieces at pauses, matching expected relative lengths.
    Returns list of (start_s, end_s) speech spans and a report string."""
    k = len(expected)
    gaps, thr = pauses(voice, sr)
    total = len(voice) / sr
    # speech extent
    head = gaps[0][1] if gaps and gaps[0][0] <= 0.01 else 0.0
    tail = gaps[-1][0] if gaps and gaps[-1][1] >= total - 0.02 else total
    inner = [g for g in gaps if g[0] > head + 0.01 and g[1] < tail - 0.01]
    cuts = [((a + b) / 2, b - a) for a, b in inner]          # (time, gap length)
    if len(cuts) < k - 1:
        raise SystemExit(f"Voice has only {len(cuts)} pauses but {k} narrated cards need {k - 1}. "
                         "Regenerate the voice with a clear pause between blocks.")
    exp = np.array(expected, float)
    scale = (tail - head) / exp.sum()
    exp = exp * scale
    pts = [head] + [c[0] for c in cuts] + [tail]
    glen = [0.0] + [c[1] for c in cuts] + [0.0]
    gstart = [head] + [a for a, _ in inner] + [tail]   # speech stops here
    gend = [head] + [b for _, b in inner] + [tail]     # speech resumes here
    m = len(pts)
    INF = 1e18
    # dp[i][j]: best cost with i pieces ending at point j
    dp = np.full((k + 1, m), INF)
    bk = np.zeros((k + 1, m), int)
    dp[0][0] = 0
    for i in range(1, k + 1):
        for j in range(i, m):
            if i == k and j != m - 1:
                continue
            best, arg = INF, -1
            for s in range(i - 1, j):
                if dp[i - 1][s] >= INF:
                    continue
                dur = pts[j] - pts[s]
                c = ((dur - exp[i - 1]) / max(exp[i - 1], 0.8)) ** 2
                if j != m - 1:
                    c -= 0.35 * min(glen[j], 1.5)     # prefer long pauses as card boundaries
                v = dp[i - 1][s] + c
                if v < best:
                    best, arg = v, s
            dp[i][j], bk[i][j] = best, arg
    idx, j = [], m - 1
    for i in range(k, 0, -1):
        s = bk[i][j]
        idx.append((s, j))
        j = s
    idx.reverse()
    spans = []
    for s, j in idx:
        a, b = gend[s], gstart[j]
        spans.append((max(0.0, a - 0.05), min(total, b + 0.08)))
    rep = [f"voice length {total:.2f}s, pauses found {len(cuts)}, silence threshold {thr:.0f} dB",
           f"{'#':>3} {'expected':>9} {'actual':>8}  ratio"]
    for i, ((a, b), e) in enumerate(zip(spans, exp), 1):
        r = (b - a) / e if e else 0
        flag = "  <-- check" if r < 0.55 or r > 1.8 else ""
        rep.append(f"{i:>3} {e:9.2f} {b - a:8.2f}  {r:4.2f}{flag}")
    return spans, "\n".join(rep)


def normalise_voice(x: np.ndarray) -> np.ndarray:
    db, _ = _frames_db(x, SR)
    lin = 10 ** (db / 20)
    voiced = lin[db > np.percentile(db, 90) - 20]
    rms = float(np.sqrt((voiced ** 2).mean())) if len(voiced) else 1e-3
    g = 10 ** (AUDIO["voice_rms_db"] / 20) / max(rms, 1e-6)
    y = x * g
    pk = np.abs(y).max() if len(y) else 0
    lim = 10 ** (AUDIO["peak_db"] / 20)
    if pk > lim:
        y = y * (lim / pk)
    return y


SEG_GAP = 0.35   # silence between two voice segments placed on the same card


def spans_length(segs) -> float:
    return sum(b - a for a, b in segs) + SEG_GAP * (len(segs) - 1)


def build_mix(total_s: float, placements, voice: np.ndarray | None, music_path: Path | None,
              outro: tuple | None = None):
    """placements: [(t_start_in_video, [(a_s, b_s), ...] segments of the voice)].
    outro: (start_s, path) -> the outro clip's own audio is levelled like our voice and mixed in there;
    the background music then runs under the whole video, outro included. Returns stereo float32."""
    n = int(round(total_s * SR))
    mono = np.zeros(n, np.float32)
    if outro:
        t0, path = outro
        oa = decode(path, SR, 1)
        if len(oa):
            oa = normalise_voice(oa)
            i0 = int(t0 * SR)
            i1 = min(n, i0 + len(oa))
            mono[i0:i1] += oa[: i1 - i0]
    if voice is not None:
        v = normalise_voice(voice)
        for t, segs in placements:
            for a, b in segs:
                seg = v[int(a * SR): int(b * SR)].copy()
                f = min(len(seg), int(0.015 * SR))
                if f:
                    seg[:f] *= np.linspace(0, 1, f)
                    seg[-f:] *= np.linspace(1, 0, f)
                i0 = int(t * SR)
                i1 = min(n, i0 + len(seg))
                mono[i0:i1] += seg[: i1 - i0]
                t += (b - a) + SEG_GAP
    out = np.stack([mono, mono], axis=1)
    if music_path:
        mus = decode(music_path, SR, 2)
        if len(mus):
            reps = int(np.ceil(n / len(mus)))
            mus = np.tile(mus, (reps, 1))[:n]
            rms = float(np.sqrt((mus ** 2).mean())) or 1e-6
            target = 10 ** ((AUDIO["voice_rms_db"] - AUDIO["music_below_voice_db"]) / 20)
            mus = mus * (target / rms)
            fi, fo = int(AUDIO["music_fade_in"] * SR), int(AUDIO["music_fade_out"] * SR)
            env = np.ones(n, np.float32)
            env[:fi] = np.linspace(0, 1, fi)
            env[n - fo:] = np.linspace(1, 0, fo)
            out += mus * env[:, None]
    pk = np.abs(out).max() if len(out) else 0
    lim = 10 ** (AUDIO["peak_db"] / 20)
    if pk > lim:
        out *= lim / pk
    return out.astype(np.float32)
