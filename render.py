#!/usr/bin/env python3
"""CommuTree video cards renderer.

Stage 1 (no voice):  python3 render.py profiles/<id>/profile.json
    -> out/<id>/cards/*.png, preview.mp4 (silent, estimated timing), narration.txt, tts_input.txt
Stage 2 (with voice): python3 render.py profiles/<id>/profile.json --voice voice.wav [--music bed.mp3]
    -> out/<id>/final.mp4, alignment.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path


from vcards import audio, narration, scenes, video
from vcards.config import AUDIO, MUSIC, ROOT


def read_narration(path: Path) -> dict:
    """Parse an (optionally hand-edited) narration.txt -> {scene_id: text}."""
    out, cur, buf = {}, None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\[(\d+)\s+(\S+)\]\s*$", line)
        if m:
            if cur:
                out[cur] = " ".join(buf).strip()
            cur, buf = m.group(2), []
        elif cur and not line.startswith("#"):
            buf.append(line.strip())
    if cur:
        out[cur] = " ".join(buf).strip()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profile", type=Path)
    ap.add_argument("--voice", type=Path, help="narration audio from Google AI Studio (wav/mp3)")
    ap.add_argument("--music", type=Path, default=MUSIC, help="background music (default: assets/music/bg_music.mp3)")
    ap.add_argument("--no-music", action="store_true", help="render without background music")
    ap.add_argument("--spans", type=Path, help="voice_spans.json: manual {card_id: [[start,end], ...]} "
                                                "(seconds in the voice file) instead of automatic split")
    ap.add_argument("--out", type=Path, help="output folder (default out/<id>)")
    ap.add_argument("--cards-only", action="store_true", help="only write card PNGs + narration")
    ap.add_argument("--no-outro", action="store_true")
    ap.add_argument("--fast", action="store_true", help="faster, lower-quality encode")
    a = ap.parse_args(argv)
    if a.no_music or (a.music and not a.music.exists()):
        a.music = None

    t0 = time.time()
    p = json.loads(a.profile.read_text(encoding="utf-8"))
    base = a.profile.resolve().parent
    pid = str(p.get("id", a.profile.parent.name))
    out = a.out or (ROOT / "out" / pid)
    (out / "cards").mkdir(parents=True, exist_ok=True)

    scs, ctx = scenes.build(p, base)
    for i, sc in enumerate(scs, 1):
        if sc.kind == "card":
            sc.image.save(out / "cards" / f"{i:02d}_{sc.id}.png")

    narrated = [sc for sc in scs if sc.text]
    narr_path = out / "narration.txt"
    if a.voice and narr_path.exists():
        edited = read_narration(narr_path)
        for sc in narrated:
            sc.text = edited.get(sc.id, sc.text)
    else:
        narration.write_files(out, pid, [(sc.id, sc.text) for sc in narrated])
    print(f"[ok] {len([s for s in scs if s.kind == 'card'])} cards -> {out / 'cards'}")
    print(f"[ok] narration -> {narr_path}")
    if a.cards_only:
        return

    vo, placements, voice = None, [], None
    if a.voice:
        voice = audio.decode(a.voice, audio.SR, 1)
        if a.spans:
            raw = json.loads(a.spans.read_text(encoding="utf-8"))
            span_of = {k: [tuple(x) for x in v] for k, v in raw.items() if not k.startswith("_")}
            missing = [sc.id for sc in narrated if sc.id not in span_of]
            if missing:
                print(f"[warn] no voice for: {', '.join(missing)} (cards stay silent)")
            print(f"[ok] using manual voice spans from {a.spans}")
        else:
            exp = [narration.estimate_seconds(sc.text) for sc in narrated]
            spans, report = audio.align(voice, audio.SR, exp)
            span_of = {sc.id: [sp] for sc, sp in zip(narrated, spans)}
            rep = "\n".join(f"{line}   {sc.id}" if i >= 2 else line
                            for i, (line, sc) in enumerate(zip(report.splitlines(), [None, None] + narrated)))
            (out / "alignment.txt").write_text(rep + "\n", encoding="utf-8")
            print(rep)
        # always write the spans used, so they can be corrected and passed back with --spans
        (out / "voice_spans.json").write_text(json.dumps(
            {"_note": "seconds in the voice file; edit and re-run with --spans this_file", **{
                k: [[round(a_, 2), round(b, 2)] for a_, b in v] for k, v in span_of.items()}},
            ensure_ascii=False, indent=1), encoding="utf-8")
        vo = {k: audio.spans_length(v) for k, v in span_of.items()}

    tl, total = video.plan(scs, vo, p.get("hold"))
    if a.voice:
        placements = [(e["vo_start"], span_of[e["id"]]) for e in tl if e["id"] in span_of and e["vo_start"] is not None]
    mix = audio.build_mix(total, placements, voice, a.music)
    wav = out / ("final_audio.wav" if a.voice else "preview_audio.wav")
    audio.write_wav(wav, mix)
    (out / "timeline.json").write_text(json.dumps({"total_main_s": round(total, 3), "scenes": tl},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")

    name = "final.mp4" if a.voice else "preview.mp4"
    preset, crf = ("veryfast", 23) if (a.fast or not a.voice) else ("medium", 20)
    video.encode(video.frames(scs, tl, ctx, p), wav, total, out / name, outro=not a.no_outro,
                 preset=preset, crf=crf, loudness=AUDIO["main_lufs"] if a.voice else None)
    print(f"[ok] {out / name}  (main {total:.1f}s + outro)  in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    sys.exit(main())
