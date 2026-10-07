#!/usr/bin/env python3
"""Self-test of the renderer. Runs in GitHub Actions on every push and weekly (catches library updates that
break things, e.g. OpenCV 5 removed the face-detector loader). Sample data only.   python3 tests/run_tests.py"""
import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""), flush=True)
    if not cond:
        FAILED.append(name)


def main():
    from PIL import features, Image
    check("Pillow has RAQM (Gujarati shaping)", features.check("raqm"))

    from vcards import imgs
    check("face detector loads (OpenCV DNN)", imgs.cv2 is not None)
    if imgs.cv2 is not None:
        tmp = ROOT / "out" / "_selftest.png"
        tmp.parent.mkdir(exist_ok=True)
        Image.new("RGB", (640, 800), "gray").save(tmp)
        try:
            imgs.faces.cache_clear()
            check("face detector runs", imgs.faces(tmp) == ())
        except Exception as e:  # noqa: BLE001
            check("face detector runs", False, repr(e))

    sample = ROOT / "samples" / "profile.example.json"
    r = subprocess.run([sys.executable, "render.py", str(sample), "--cards-only"], cwd=ROOT, capture_output=True, text=True)
    cards = sorted((ROOT / "out" / "sample-girl" / "cards").glob("*.png"))
    check("sample cards render", r.returncode == 0 and len(cards) == 11, f"{len(cards)} cards; {r.stderr[-200:]}")

    tts = (ROOT / "out" / "sample-girl" / "tts_input.txt").read_text(encoding="utf-8").strip().split("\n\n")
    check("narration: [long pause] after every block except the last",
          all(b.rstrip().endswith("[long pause]") for b in tts[:-1]) and not tts[-1].rstrip().endswith("]"))

    from vcards import align, scenes
    fx = json.loads((ROOT / "tests" / "fixture_v4_pauses.json").read_text())
    blocks = ["x."] * fx["cards"]
    spans, method, unsure = align.split(blocks, [tuple(g) for g in fx["gaps"]], fx["total"])
    starts = [round(a, 2) for a, _ in spans]
    check("real v4 voice: split by card markers", method.startswith("card markers") and not unsure, method)
    check("real v4 voice: card starts", all(abs(a - b) < 0.02 for a, b in zip(starts, fx["expected_starts"])), str(starts))

    p = json.loads(sample.read_text(encoding="utf-8"))
    bl = [s.text for s in scenes.build(p, ROOT / "samples", images=False)[0] if s.text]
    rnd = random.Random(3)
    ok = 0
    for _ in range(60):
        t, gaps, truth = 0.0, [], []
        for i, b in enumerate(bl):
            if i:
                g = rnd.uniform(1.1, 1.9); gaps.append((t, t + g)); t += g
            truth.append(t)
            for j, ph in enumerate(align.phrases(b)):
                t += 0.3 + 0.19 * align.phrase_syllables(ph, rnd.uniform(0.45, 0.75)) * rnd.uniform(0.85, 1.15)
                if j < len(align.phrases(b)) - 1 and rnd.random() > 0.2:
                    g = rnd.uniform(0.28, 0.8); gaps.append((t, t + g)); t += g
        sp, _, _ = align.split(bl, gaps, t)
        ok += all(abs(a - s) < 0.06 for (a, _), s in zip(sp, truth))
    check("simulated v4 voices (sample profile): all cards correct", ok == 60, f"{ok}/60")

    r = subprocess.run([sys.executable, "render.py", str(sample), "--fast"], cwd=ROOT, capture_output=True, text=True)
    mp4 = ROOT / "out" / "sample-girl" / "preview.mp4"
    check("sample preview video renders", r.returncode == 0 and mp4.exists(), r.stderr[-200:])

    print("\nALL PASSED" if not FAILED else f"\n{len(FAILED)} FAILED: {', '.join(FAILED)}")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
