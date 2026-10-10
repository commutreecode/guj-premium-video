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

    from vcards.text import Style, runs
    r = runs("વિશ્વાસ શ્રી", Style())
    check("શ્વ drawn with Anek (Akhand's half-શ reads as ર)", [c for k, _, _, c in r if k == "anek_b"] == ["શ્વા"], str(r))
    check("શ્ર stays in Akhand", r[-1][0] == "akhand_xb" and r[-1][3].endswith("શ્રી"), str(r))

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

    # photo editor of the app: "rotate" (clockwise) and "trim" are applied before the normal framing
    ed = ROOT / "out" / "_edit.png"
    im0 = Image.new("RGB", (400, 300), "white")
    im0.paste((255, 0, 0), (0, 0, 100, 50))                      # red block top-left
    im0.save(ed)
    e = imgs.Photo({"src": ed.name, "rotate": 90, "trim": [0, 0, 1, 0.5]}, ed.parent).load()
    check("photo edit: rotate 90 + trim top half", e.size == (300, 200) and e.getpixel((290, 10)) == (255, 0, 0), str(e.size))
    check("photo edit: unedited photo unchanged", imgs.Photo(ed.name, ed.parent).load().size == (400, 300))
    for bad in ({"rotate": 45}, {"trim": [0.6, 0, 0.5, 1]}, {"trim": [0, 0, 1]}):
        try:
            imgs.Photo(dict(src=ed.name, **bad), ed.parent)
            check(f"photo edit: bad value refused {bad}", False)
        except ValueError:
            check(f"photo edit: bad value refused {bad}", True)

    # every photo type the app may upload as it is (the browser cannot convert HEIC / TIFF on Windows)
    src = Image.new("RGB", (64, 48), (200, 30, 30))
    fmts = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP", "gif": "GIF", "bmp": "BMP", "tif": "TIFF"}
    if features.check("avif"):
        fmts["avif"] = "AVIF"
    try:
        import pillow_heif  # noqa: F401
        fmts["heic"] = "HEIF"
    except ImportError:
        pass
    bad = []
    for ext, fmt in fmts.items():
        f = ROOT / "out" / f"_fmt.{ext}"
        try:
            src.save(f, fmt)
            im = imgs.load(f)
            if im.mode != "RGB" or im.size != (64, 48) or im.getpixel((5, 5))[0] < 150:
                bad.append(ext)
        except Exception as ex:  # noqa: BLE001
            bad.append(f"{ext}: {ex!r}"[:60])
    Image.new("I;16", (32, 32), 40000).save(ROOT / "out" / "_fmt16.png")
    if imgs.load(ROOT / "out" / "_fmt16.png").getpixel((1, 1))[0] < 120:
        bad.append("16-bit png")
    check("photo types load: " + ", ".join(fmts) + ", 16-bit png", not bad, ", ".join(bad))

    sample = ROOT / "samples" / "profile.example.json"
    r = subprocess.run([sys.executable, "render.py", str(sample), "--cards-only"], cwd=ROOT, capture_output=True, text=True)
    cards = sorted((ROOT / "out" / "sample-girl" / "cards").glob("*.png"))
    check("sample cards render", r.returncode == 0 and len(cards) == 11, f"{len(cards)} cards; {r.stderr[-200:]}")

    pe = json.loads(sample.read_text(encoding="utf-8"))          # same sample with edited photos (as the app writes them)
    pe["id"] = "_selftest-edit"
    pe["photos"]["gallery"][0] = {"src": "photos/g1.jpg", "rotate": 90}
    pe["parents"]["photos"][0] = {"src": "photos/mother.jpg", "trim": [0.1, 0.0, 0.9, 0.8]}
    pj = ROOT / "samples" / "_selftest_edit.json"
    pj.write_text(json.dumps(pe, ensure_ascii=False), encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, "render.py", str(pj), "--cards-only"], cwd=ROOT, capture_output=True, text=True)
    finally:
        pj.unlink()
    check("sample cards render with edited photos", r.returncode == 0, r.stderr[-200:])
    try:
        g_im, _, _ = imgs.cover_reserve(imgs.Photo(pe["photos"]["gallery"][0], ROOT / "samples"), 1200, 1110, 150)
        check("gallery photo with rotate frames", g_im.width == 1200, str(g_im.size))
    except Exception as ex:  # noqa: BLE001
        check("gallery photo with rotate frames", False, repr(ex))

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
    try:   # the narration has one block more than the voice (ElevenLabs stopped early): must stop, not guess
        align.split(blocks + ["x."], [tuple(g) for g in fx["gaps"]], fx["total"])
        check("voice with a block missing is refused", False, "split without error")
    except align.VoiceMismatch as e:
        check("voice with a block missing is refused", "VOICE CHECK" in str(e), str(e)[:80])

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

    # job card: company logo ABOVE the company name, transparent; the person's photo stays on the right
    from vcards import cards
    from vcards.config import BROWN
    from PIL import ImageColor, ImageChops
    lgp = ROOT / "out" / "_logo.jpg"
    li = Image.new("RGB", (1732, 385), "white")
    li.paste((0, 200, 0), (60, 60, 1600, 320))
    li.save(lgp)
    ctx = cards.Ctx("boy", ROOT, "clear")
    job = {"style": "bullets", "bullets": ["Engineer at Sample Systems Pvt. Ltd., Ahmedabad"], "logo": "out/_logo.jpg"}
    jc = cards.work(ctx, job, "x", "samples/photos/g2.jpg").convert("RGB")
    pix = lambda box: list(zip(*[iter(jc.crop(box).tobytes())] * 3))
    green = lambda box: any(g > 150 and r < 80 and b < 80 for r, g, b in pix(box))
    ys = [y for y in range(560, 1440, 4) if green((40, y, 800, y + 4))]
    acc = ImageColor.getrgb(ctx.accent)
    comp_y = min(y for y in range(560, 1440, 4) if any(max(abs(a - b) for a, b in zip(c, acc)) < 30 for c in pix((40, y, 800, y + 4))))
    check("job card: logo above the company name", ys and max(ys) < comp_y, f"logo {ys[:1]}..{ys[-1:]} company {comp_y}")
    check("job card: logo not in the photo frame", not green((830, 560, 1190, 1300)))
    check("job card: white logo background made transparent", sum(1 for c in pix((40, 560, 800, 1440)) if min(c) >= 250) < 200)
    job4 = dict(job, bullets=["A at B, C", "D", "E", "F"])
    jc = cards.work(ctx, job4, "x", "samples/photos/g2.jpg").convert("RGB")
    check("job card with 4 points: logo above the list", green((40, 560, 800, 780)))

    # a logo uploaded in the occupation PHOTO box (team habit): drawn as the logo, a person photo on the right
    jc = cards.work(ctx, {"style": "bullets", "bullets": job["bullets"], "photo": {"src": "out/_logo.jpg", "trim": [0, 0, 0.5, 1]}},
                    "x", "samples/photos/g2.jpg").convert("RGB")
    check("logo in the photo box: drawn in the text column, not in the photo frame",
          green((40, 560, 800, 1440)) and not green((830, 560, 1190, 1300)))
    noise = ROOT / "out" / "_busy.jpg"
    Image.frombytes("RGB", (8, 10), random.Random(1).randbytes(8 * 10 * 3)).resize((400, 500), Image.BILINEAR).save(noise)
    check("a busy photo (no face) is not taken for a logo", not imgs.looks_like_logo(imgs.Photo("out/_busy.jpg", ROOT)))

    # Past Experience: own card after the occupation card (up to 3, each with its logo), music only
    past = [{"text": "Data Scientist at Sample Analytics, Bangalore", "logo": "out/_logo.jpg"}, "Intern at Sample Labs", {"text": "C"}, {"text": "D"}]
    check("past experience: up to 3 items", len(cards.past_items({"past": past})) == 3 and cards.past_items({"past": "X"}) == [{"text": "X", "logo": None}])
    jc = cards.past_experience(ctx, cards.past_items({"past": past}), "x").convert("RGB")
    check("past experience card: logo drawn", green((0, 560, 1200, 1440)))
    jp = cards.work(ctx, dict(job, past=past), "x", "samples/photos/g2.jpg").convert("RGB")
    j0 = cards.work(ctx, job, "x", "samples/photos/g2.jpg").convert("RGB")
    check("past experience: not on the occupation card", ImageChops.difference(jp, j0).getbbox() is None)
    pp = json.loads(sample.read_text(encoding="utf-8"))
    pp["work"] = dict(pp.get("work") or {"style": "bullets", "bullets": ["A"]}, past=["Data Scientist at Sample Analytics"])
    sc = scenes.build(pp, ROOT / "samples", images=False)[0]
    ids = [x.id for x in sc]
    check("past experience: card right after the occupation card, no voice",
          "past" in ids and ids.index("past") == ids.index("work") + 1 and not sc[ids.index("past")].text)

    # one Income / Property line: shown in the gallery strip (no own card); a long hobby text scrolls to its end
    pp["property"] = ["Residence 2BHK at Sample Nagar"]
    pp["hobbies"] = ["Associated with a very long sample hobby description that does not fit", "Chess", "Badminton", "Table Tennis"]
    sc, cx = scenes.build(pp, ROOT / "samples", images=False)
    check("one property line: no Income / Property card", "property" not in [x.id for x in sc])
    subs = cards.gallery_sublines(cx, pp)
    check("one property line: in the gallery strip", any(st[0] == "ticker" and st[1].width < 400 and st[2].width > 300 for st, _ in subs[1:2]))
    check("long hobby text: time to scroll to its end", subs[0][1] > cards.STATIC_SECONDS + 2, f"{subs[0][1]:.1f} s")
    pp["property"] = ["Income: 10-20 Lakhs", "Residence 2BHK at Sample Nagar"]
    check("two property lines: own card as before", "property" in [x.id for x in scenes.build(pp, ROOT / "samples", images=False)[0]])

    # education: up to 7 degrees on one card (1-3 keep the approved layout), nothing below the card's bottom
    eds = [{"degree": f"Degree number {i} in Sample Engineering", "institute": f"Sample University {i}, Ahmedabad"} for i in range(7)]
    e7 = cards.education(ctx, eds, "x", None).convert("RGB")
    e0 = cards.education(ctx, [], "x", None).convert("RGB")
    check("education: 7 degrees fit on the card", ImageChops.difference(e7.crop((0, 1462, 1200, 1500)), e0.crop((0, 1462, 1200, 1500))).getbbox() is None
          and ImageChops.difference(e7.crop((0, 1300, 1200, 1460)), e0.crop((0, 1300, 1200, 1460))).getbbox() is not None)

    e1 = cards.education(ctx, [{"degree": "B.Com", "institute": "Sample College, Anand"}], "x", None).convert("RGB")
    brown = sum(1 for r, g, b in e1.crop((0, 600, 1200, 1100)).getdata() if abs(r - 0x65) < 12 and abs(g - 0x2B) < 12 and b < 20)
    check("education: institute line in brown #652B02", brown > 300, str(brown))

    # sibling card: "who: text" continues after the name; the brown band keeps its size
    sib = lambda det: cards.sibling(cards.Ctx("boy", ROOT / "samples", "clear"),
                                    {"relation": "bhai", "display_name": "x", "photos": ["photos/couple.jpg"], "details": det}).convert("RGB")
    isb = lambda im, y: max(abs(a - b) for a, b in zip(im.getpixel((10, y)), ImageColor.getrgb(BROWN))) < 6
    short = sib([{"who": "અ", "text": "Service"}, {"who": "બ", "text": "Service"}])
    long_ = sib([{"who": "અ", "text": "HouseWife"}, {"who": "બ", "text": "Professor at Sample Institute of Technology, Anand"}])
    check("sibling band: same size for short and long text", all(isb(im, 1130) and isb(im, 1490) and not isb(im, 1110) for im in (short, long_)))

    r = subprocess.run([sys.executable, "render.py", str(sample), "--fast"], cwd=ROOT, capture_output=True, text=True)
    mp4 = ROOT / "out" / "sample-girl" / "preview.mp4"
    check("sample preview video renders", r.returncode == 0 and mp4.exists(), r.stderr[-200:])

    print("\nALL PASSED" if not FAILED else f"\n{len(FAILED)} FAILED: {', '.join(FAILED)}")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
