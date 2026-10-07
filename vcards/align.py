"""Split one narration voice file into per-card spans.

1. Card markers: the narration ends every block with "[long pause]". ElevenLabs v4 then leaves clearly longer
   gaps between cards (measured 1.1-1.85 s vs <= 0.8 s inside cards), so the K-1 longest gaps ARE the boundaries.
2. Otherwise phrase-level matching: every phrase (split at . , ; : and " - ") is matched in order to the voice's
   speech segments using syllable counts, a fixed time per phrase and a preference for long gaps at card ends.
3. Safety net: several nearby settings must agree; if not, the split is marked uncertain ("<-- check").
"""
from __future__ import annotations

import re

import numpy as np

from .syllables import syllables

TAG = re.compile(r"\[[^\]]*\]")                       # ElevenLabs audio tags, e.g. [long pause]
SPLIT = re.compile(r"(?<=[.,;:!?।])\s+|\s+[-–—]\s+")
LAT = re.compile(r"[A-Za-z]+|\d+")

PARAMS = dict(w_en=0.6, over=0.35, gapw=0.4)            # chosen inside the stable range (her real voices)
ALTS = [dict(w_en=0.5, over=0.35, gapw=0.5), dict(w_en=0.65, over=0.25, gapw=0.3),
        dict(w_en=0.5, over=0.25, gapw=0.3), dict(w_en=0.65, over=0.35, gapw=0.5)]
MARKED_MIN_GAP = 0.9      # card gaps with [long pause] are at least this long ...
MARKED_RATIO = 1.25       # ... and this much longer than any gap inside a card


def strip_tags(text: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", text)).strip()


def phrases(block: str) -> list[str]:
    return [p for p in SPLIT.split(strip_tags(block)) if p.strip(" .,-")]


def phrase_syllables(p: str, w_en: float) -> float:
    lat = LAT.findall(p)
    gu = LAT.sub(" ", p)
    return (syllables(gu) if gu.strip(" .,-+") else 0) + (w_en * syllables(" ".join(lat)) if lat else 0)


def chunks(gaps, total):
    head = gaps[0][1] if gaps and gaps[0][0] <= 0.01 else 0.0
    tail = gaps[-1][0] if gaps and gaps[-1][1] >= total - 0.02 else total
    inner = [g for g in gaps if g[0] > head + 0.01 and g[1] < tail - 0.01]
    segs = list(zip([head] + [b for _, b in inner], [a for a, _ in inner] + [tail]))
    return segs, [b - a for a, b in inner]


def _starts_to_spans(starts, segs):
    n = len(starts)
    return [(segs[starts[i]][0], segs[(starts[i + 1] - 1) if i + 1 < n else len(segs) - 1][1]) for i in range(n)]


def by_markers(n_cards: int, segs, glen):
    """Card boundaries = the n-1 longest gaps, if they stand out clearly. Returns start indexes or None."""
    k = n_cards - 1
    if k == 0:
        return [0]
    if len(glen) < k:
        return None
    order = sorted(range(len(glen)), key=lambda i: -glen[i])
    cut, rest = sorted(order[:k]), order[k:]
    shortest_cut = min(glen[i] for i in cut)
    longest_rest = max((glen[i] for i in rest), default=0.0)
    if shortest_cut >= MARKED_MIN_GAP and shortest_cut >= MARKED_RATIO * longest_rest:
        return [0] + [i + 1 for i in cut]
    return None


def by_phrases(blocks, segs, glen, w_en, over, gapw, max_p=5, max_c=4):
    syl, owner = [], []
    for bi, b in enumerate(blocks):
        ps = phrases(b) or [strip_tags(b) or "."]
        for p in ps:
            syl.append(max(0.5, phrase_syllables(p, w_en)))
            owner.append(bi)
    P, C = len(syl), len(segs)
    if C < len(blocks):
        return None
    speech = sum(e - s for s, e in segs)
    k = max(0.05, (speech - over * P) / sum(syl))
    est = [over + k * s for s in syl]
    INF = 1e18
    dp = np.full((P + 1, C + 1), INF)
    bk = {}
    dp[0][0] = 0.0
    for i in range(P):
        for j in range(C):
            if dp[i][j] >= INF:
                continue
            for a in range(1, max_p + 1):
                if i + a > P or len(set(owner[i:i + a])) > 1:
                    break
                e = sum(est[i:i + a])
                for b in range(1, max_c + 1):
                    if j + b > C:
                        break
                    d = segs[j + b - 1][1] - segs[j][0]
                    c = ((d - e) / max(e, 0.6)) ** 2
                    end = j + b - 1
                    if i + a < P and owner[i + a] != owner[i] and end < len(glen):
                        c -= gapw * min(glen[end], 1.2)
                    if dp[i][j] + c < dp[i + a][j + b]:
                        dp[i + a][j + b] = dp[i][j] + c
                        bk[(i + a, j + b)] = (i, j)
    if dp[P][C] >= INF:
        return None
    i, j, groups = P, C, []
    while (i, j) != (0, 0):
        pi, pj = bk[(i, j)]
        groups.append((pi, pj))
        i, j = pi, pj
    first = {}
    for pi, pj in reversed(groups):
        first.setdefault(owner[pi], pj)
    return [first[b] for b in range(len(blocks))]


def split(blocks, gaps, total):
    """-> (spans [(start, end)] per card, method, uncertain card indexes)."""
    segs, glen = chunks(gaps, total)
    st = by_markers(len(blocks), segs, glen)
    if st is not None:
        return _starts_to_spans(st, segs), "card markers ([long pause])", []
    st = by_phrases(blocks, segs, glen, **PARAMS)
    if st is None:
        raise SystemExit(f"Voice has only {len(segs)} speech parts for {len(blocks)} cards: "
                         "regenerate it in one go from the Narration text (keep the [long pause] tags).")
    unsure = set()
    for alt in ALTS:
        a = by_phrases(blocks, segs, glen, **alt)
        if a is None:
            continue
        unsure |= {i for i, (x, y) in enumerate(zip(st, a)) if x != y}
    return _starts_to_spans(st, segs), "phrase matching", sorted(unsure)
