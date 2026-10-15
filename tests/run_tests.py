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
    # 10: the sample's one property line is shown in the gallery strip, not on an own card (renderer b51b227)
    check("sample cards render", r.returncode == 0 and len(cards) == 10, f"{len(cards)} cards; {r.stderr[-200:]}")

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

    # father / mother in the candidate's own business: only the label is spoken (CT, 13 Oct 2026)
    from vcards.narration import scene_text
    biz = {"name": "x", "work": {"style": "business", "company": "Sample Electronics, Deesa", "desc": "Wholesaler"}}
    same = scene_text("father", biz, {"occupation": ["Business:", "Sample Electronics, Deesa", "(Wholesaler of Electronics & Electrical)"]})
    other = scene_text("father", biz, {"occupation": ["Business:", "Other Traders, Deesa"]})
    check("narration: father in the same business -> 'પિતા. Business.'", same == "પિતા. Business.", same)
    check("narration: father in another business -> full text", other == "પિતા. Business, Other Traders, Deesa.", other)
    check("narration: one-line same business, generic company names ignored",
          scene_text("father", biz, {"occupation": ["SAMPLE ELECTRONICS"]}) == "પિતા. Business."
          and scene_text("father", {"name": "x", "work": {"company": "Business"}}, {"occupation": ["Business"]}) == "પિતા. Business."
          and scene_text("mother", biz, {"occupation": ["HouseWife"]}) == "માતા. HouseWife.")

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

    # 2+ siblings WITHOUT a photo: one text slide, music only; a sibling with a photo keeps its card + voice (CT, 15 Oct 2026)
    from vcards import cards as C, video as V
    def sib(rel, name, place=None, occ=None, photo=None):
        o = {"relation": rel, "display_name": name, "details": [{"who": "", "text": occ}] if occ else []}
        if place: o["place"] = place
        if photo: o["photos"] = [photo]
        return o
    q = json.loads(sample.read_text(encoding="utf-8"))
    photo_sib = q["siblings"][0]
    q["siblings"] = [sib("bhai-bhabhi", "સાધના વિનોદ છેડા", "ગોરેગામ"), photo_sib, sib("bhai-bhabhi", "શીતલ શાંતિલાલ છેડા", "મલાડ"),
                     sib("bahen-banevi", "સંગીતા હંસરાજ નિસર", "ફોર્ટ", "Teacher"), sib("bahen", "પૂજા છેડા", None, "B.Com")]
    sc_q = scenes.build(q, ROOT / "samples", images=False)[0]
    ids = [x.id for x in sc_q]
    sl = [x for x in sc_q if x.id == "sib_list"]
    check("2+ siblings without photo: one text slide where the first of them is, photo sibling keeps its card",
          ids[ids.index("father") + 1:ids.index("education")] == ["sib_list", "sibling2"], str(ids))
    check("siblings text slide: music only, not in the narration",
          sl and sl[0].text == "" and not any("સાધના" in x.text or "પૂજા" in x.text for x in sc_q)
          and [x.text for x in sc_q if x.id == "sibling2"][0] != "", str([x.text for x in sc_q if x.text][-4:]))
    g = C.sibling_groups([x for x in q["siblings"] if C.no_photo(x)])
    check("siblings text slide: same relation once, (place) else (occupation)",
          g == [("ભાઈ-ભાભી", ["સાધના વિનોદ છેડા (ગોરેગામ)", "શીતલ શાંતિલાલ છેડા (મલાડ)"]),
                ("બહેન-બનેવી", ["સંગીતા હંસરાજ નિસર (ફોર્ટ)"]), ("બહેન", ["પૂજા છેડા (B.Com)"])], str(g))
    tl, _ = V.plan(sc_q, vo={x.id: 2.0 for x in sc_q if x.text})
    dur = {e["id"]: e for e in tl}
    check("siblings text slide: 4.5 s + 1.2 s per sibling above 2, no voice on it",
          abs(dur["sib_list"]["dur"] - 6.9) < 0.01 and dur["sib_list"]["vo_start"] is None, str(dur["sib_list"]))
    bl_q = [x.text for x in sc_q if x.text]
    rnd = random.Random(5); okq = 0
    for _ in range(20):
        t, gaps, truth = 0.0, [], []
        for i, b in enumerate(bl_q):
            if i:
                g_ = rnd.uniform(1.1, 1.9); gaps.append((t, t + g_)); t += g_
            truth.append(t)
            for j, ph in enumerate(align.phrases(b)):
                t += 0.3 + 0.19 * align.phrase_syllables(ph, rnd.uniform(0.45, 0.75)) * rnd.uniform(0.85, 1.15)
                if j < len(align.phrases(b)) - 1 and rnd.random() > 0.2:
                    g_ = rnd.uniform(0.28, 0.8); gaps.append((t, t + g_)); t += g_
        sp, _, _ = align.split(bl_q, gaps, t)
        okq += all(abs(a - s_) < 0.06 for (a, _), s_ in zip(sp, truth))
    check("simulated v4 voices with a music-only siblings slide in the middle: all cards correct", okq == 20, f"{okq}/20")
    one = dict(q, siblings=[photo_sib, sib("bahen", "પૂજા છેડા", None, "B.Com")])
    ids1 = [x.id for x in scenes.build(one, ROOT / "samples", images=False)[0]]
    check("only ONE sibling without photo: own card + voice, as before", "sib_list" not in ids1 and "sibling2" in ids1, str(ids1))
    ctx_q = C.Ctx("girl", ROOT / "samples")
    im = C.siblings_list(ctx_q, [x for x in q["siblings"] if C.no_photo(x)])
    many = [sib(r, "લાંબુ નામ ઉદાહરણ હસમુખલાલ પ્રવીણચંદ્ર શાહ", "ઘાટકોપર") for r in ("bhai-bhabhi", "bahen-banevi", "bhai", "bahen", "mota-bhai-bhabhi")]
    im5 = C.siblings_list(ctx_q, many)
    def ink_rows(img):
        px = img.convert("RGB").load()
        return [y for y in range(150, img.size[1]) if any(px[x, y][0] < 200 and abs(px[x, y][0] - px[x, y][2]) > 40
                                                          for x in range(40, 1160, 3))]
    r5 = ink_rows(im5)
    check("siblings text slide: 5 groups with long names fit between header and bottom edge",
          im.size == (1200, 1500) and r5 and r5[0] > 150 and r5[-1] < 1476, f"{r5[:1]}..{r5[-1:]}")

    # job card: company logo BELOW the company name, transparent; the person's photo stays on the right
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
    comp_ys = [y for y in range(560, 1440, 4) if any(max(abs(a - b) for a, b in zip(c, acc)) < 30 for c in pix((40, y, 800, y + 4)))]
    check("job card: designation, company name, then the logo below it (CT, 14 Oct 2026)",
          ys and comp_ys and min(ys) > max(comp_ys), f"logo {ys[:1]}..{ys[-1:]} company {comp_ys[:1]}..{comp_ys[-1:]}")
    check("job card: logo larger than before (wide logo up to 600 px wide)", ys and 96 <= max(ys) - min(ys) + 4, f"{max(ys) - min(ys) + 4} px tall")
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
    jc = cards.work(ctx, {"style": "bullets", "bullets": job["bullets"], "photo": "out/_busy.jpg"}, "x", "samples/photos/g2.jpg").convert("RGB")
    j2 = cards.work(ctx, {"style": "bullets", "bullets": job["bullets"]}, "x", "samples/photos/g2.jpg").convert("RGB")
    check("LOGO / COMPANY CARD box without a face (e.g. a blue visiting card): in the text column, photo frame unchanged",
          ImageChops.difference(jc.crop((830, 560, 1190, 1300)), j2.crop((830, 560, 1190, 1300))).getbbox() is None
          and ImageChops.difference(jc.crop((40, 560, 800, 1440)), j2.crop((40, 560, 800, 1440))).getbbox() is not None)

    # Past Experience: own card after the occupation card (up to 3, each with its logo), music only
    past = [{"text": "Data Scientist at Sample Analytics, Bangalore", "logo": "out/_logo.jpg"}, "Intern at Sample Labs", {"text": "C"}, {"text": "D"}]
    check("past experience: up to 3 items", len(cards.past_items({"past": past})) == 3 and cards.past_items({"past": "X"}) == [{"text": "X", "logo": None}])
    jc = cards.past_experience(ctx, cards.past_items({"past": past}), "x").convert("RGB")
    check("past experience card: logo drawn", green((0, 560, 1200, 1440)))
    jcp = cards.past_experience(ctx, cards.past_items({"past": past}), "x", "samples/photos/g2.jpg").convert("RGB")
    jw = cards.work(ctx, job, "x", "samples/photos/g2.jpg").convert("RGB")
    jc = jcp
    check("past experience card with a candidate photo: photo on the right like the occupation card, logo + text left",
          ImageChops.difference(jcp.crop((830, 560, 1190, 1300)), jw.crop((830, 560, 1190, 1300))).getbbox() is None
          and green((0, 560, 800, 1440)))
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
    check("one property line: in the gallery strip after a theme-colour bullet (no PROPERTY: word)",
          any(st[0] == "ticker" and st[1].width < 120 and st[2].width > 300 for st, _ in subs[0:1]))
    check("long hobby text: time to scroll to its end", subs[1][1] > cards.STATIC_SECONDS + 2, f"{subs[1][1]:.1f} s")
    # one award + one property line: strip order award, property, hobby, સમાજ, info; 2-3 awards: own card (music only)
    pp["awards"] = ["Gold medal in Sample University"]
    subs = cards.gallery_sublines(cx, pp)
    check("strip order: award, property, hobby, sect, info",
          [st[0] for st, _ in subs][:3] == ["ticker"] * 3 and subs[0][0][1].width < 120 and subs[1][0][1].width < 120
          and subs[2][0][1].width > 120 and [st[0] for st, _ in subs][3:] == ["static", "static"], str(len(subs)))
    ids = [x.id for x in scenes.build(pp, ROOT / "samples", images=False)[0]]
    check("one award: no awards card", "awards" not in ids)
    pp["awards"] = ["Gold medal in Sample University", "Best Employee 2024", "State level chess"]
    sc = scenes.build(pp, ROOT / "samples", images=False)[0]
    ids = [x.id for x in sc]
    check("2-3 awards: own card after past experience, before the gallery, no voice",
          "awards" in ids and ids.index("awards") == ids.index("past") + 1 and not sc[ids.index("awards")].text)
    check("awards card renders", cards.awards_card(cards.Ctx("boy", ROOT, "clear"), cards.award_items(pp), "x").size == (1200, 1500))
    pp.pop("awards")
    pp["property"] = ["Income: 10-20 Lakhs", "Residence 2BHK at Sample Nagar"]
    check("two property lines: own card as before", "property" in [x.id for x in scenes.build(pp, ROOT / "samples", images=False)[0]])

    # gallery photo cropped tight above the head (dy > 0): the top is filled from the photo, never a light bar
    from vcards import video
    tight = ROOT / "out" / "_tight.png"
    gim = Image.new("RGB", (900, 1100), (40, 90, 160))
    gim.save(tight)
    g = video.Gallery(cards.Ctx("boy", ROOT, "clear"), {"name": "x"}, [imgs.Photo("out/_tight.png", ROOT)], 0, 2.0)
    g._cache[0] = (Image.new("RGB", (1500, 1200), (40, 90, 160)), (750, 300), 150)   # as cover_reserve gives for a tight crop
    fr = g.frame(0.5)
    r, gg, b = fr.getpixel((1000, 60))
    check("gallery: no light bar above a tightly cropped photo", b > r + 60, str((r, gg, b)))

    # education: up to 7 degrees on one card (1-3 keep the approved layout), nothing below the card's bottom
    eds = [{"degree": f"Degree number {i} in Sample Engineering", "institute": f"Sample University {i}, Ahmedabad"} for i in range(7)]
    e7 = cards.education(ctx, eds, "x", None).convert("RGB")
    e0 = cards.education(ctx, [], "x", None).convert("RGB")
    check("education: 7 degrees fit on the card", ImageChops.difference(e7.crop((0, 1462, 1200, 1500)), e0.crop((0, 1462, 1200, 1500))).getbbox() is None
          and ImageChops.difference(e7.crop((0, 1300, 1200, 1460)), e0.crop((0, 1300, 1200, 1460))).getbbox() is not None)

    e1 = cards.education(ctx, [{"degree": "B.Com", "institute": "Sample College, Anand"}], "x", None).convert("RGB")
    brown = sum(1 for r, g, b in e1.crop((0, 600, 1200, 1100)).getdata() if abs(r - 0x65) < 12 and abs(g - 0x2B) < 12 and b < 20)
    check("education: institute line in brown #652B02", brown > 300, str(brown))
    # several degrees: one size for all (CT, 14 Oct 2026: "B.Tech in Mechanical Engineering" was smaller than the next)
    def ink_heights(im, x0=60, x1=800):                       # heights of the dark text rows in the text column
        rows, inside, start = [], False, 0
        for y in range(560, 1440):
            ink = any(max(im.getpixel((x, y))) < 60 for x in range(x0, x1, 2))
            if ink and not inside:
                start = y
            if not ink and inside:
                rows.append(y - start)
            inside = ink
        return rows
    e2 = cards.education(ctx, [{"degree": "B.Tech in Mechanical Engineering", "institute": "GEC, Modasa"},
                               {"degree": "Masters in Social Work", "institute": "Sample University"}], "x", "samples/photos/g2.jpg").convert("RGB")
    hh = ink_heights(e2)
    check("education: every degree in the same size (first lines: capitals, no descenders)",
          len(hh) >= 3 and abs(hh[0] - hh[2]) <= 4, str(hh))
    # sibling without details: no brown band, the photo uses the free space
    nb = cards.sibling(cards.Ctx("boy", ROOT / "samples", "clear"),
                       {"relation": "bahen-banevi", "display_name": "x", "photos": ["photos/couple.jpg"], "details": []}).convert("RGB")
    br = ImageColor.getrgb(BROWN)
    def photo_bottom(im, x=600):                     # last row of the photo (not the light card background)
        return max(y for y in range(900, 1500) if max(abs(c - d) for c, d in zip(im.getpixel((x, y)), im.getpixel((8, y)))) > 30)
    check("sibling without details: no brown band, photo down to half of where the band would be (CT, 14 Oct 2026)",
          not any(max(abs(a - b) for a, b in zip(nb.getpixel((10, y)), br)) < 6 for y in (1200, 1300, 1450))
          and 1290 <= photo_bottom(nb) <= 1312, str(photo_bottom(nb)))
    # text at the bottom of a card never touches the edge (CT, 14 Oct 2026: ગુર્જર / ગજ્જર સુથાર under the parents band)
    def ink_bottom(im, y0=1380):
        bg = lambda y: im.getpixel((8, y))
        return max([y for y in range(y0, 1500) if sum(1 for x in range(150, 1050, 3)
                    if max(abs(c - d) for c, d in zip(im.getpixel((x, y)), bg(y))) > 60) > 2] or [0])
    sc = cards.Ctx("boy", ROOT / "samples", "clear")
    sect = "ગુર્જર / ગજ્જર સુથાર"
    par = cards.family_pair(sc, "parents", {"display_name": "x", "village": "ગામ", "city": "શહેર", "sect": sect,
                                             "photos": ["photos/mother.jpg", "photos/father.jpg"]}).convert("RGB")
    nn = cards.family_pair(sc, "nana_nani", {"display_name": "x", "village": "ભુજ", "photos": ["photos/couple.jpg"]}).convert("RGB")
    np_ = cards.family_pair(sc, "parents", {"display_name": "x", "village": "ગામ", "sect": sect, "photos": []}).convert("RGB")
    bott = [ink_bottom(par, 1405), ink_bottom(nn), ink_bottom(np_)]
    check("bottom text: at least 14 px above the edge (parents sect between band and edge), 24 px elsewhere",
          bott[0] <= 1486 and bott[1] <= 1476 and bott[2] <= 1476, str(bott))

    # sibling card: "who: text" continues after the name; the brown band keeps its size
    sib = lambda det: cards.sibling(cards.Ctx("boy", ROOT / "samples", "clear"),
                                    {"relation": "bhai", "display_name": "x", "photos": ["photos/couple.jpg"], "details": det}).convert("RGB")
    isb = lambda im, y: max(abs(a - b) for a, b in zip(im.getpixel((10, y)), ImageColor.getrgb(BROWN))) < 6
    short = sib([{"who": "અ", "text": "Service"}, {"who": "બ", "text": "Service"}])
    long_ = sib([{"who": "અ", "text": "HouseWife"}, {"who": "બ", "text": "Professor at Sample Institute of Technology, Anand"}])
    check("sibling band: long text keeps the band at 1122", isb(long_, 1130) and isb(long_, 1490) and not isb(long_, 1110))
    one = sib([{"who": "", "text": "Student"}])
    check("sibling band: one short line -> shorter band, photo grows (CT, 13 Oct 2026)",
          not isb(one, 1200) and isb(one, 1300) and isb(one, 1490) and isb(short, 1490) and not isb(short, 1110))
    pj = lambda jobs: cards.single_parent(cards.Ctx("boy", ROOT / "samples", "clear"), "father", {"name": "x", "jobs": jobs},
                                          "photos/couple.jpg").convert("RGB")
    j2 = pj([{"type": "Business", "name": "Shree Sample Saw Mill, Kurundwad-Kolhapur", "desc": "Retailer of Building Material"},
             {"type": "Own Business", "name": "Sample Construction Contractor", "desc": ""}])
    check("parent Type / Name / Work: band never taller than 1161..1471, photo ends above it",
          isb(j2, 1165) and isb(j2, 1468) and not isb(j2, 1150) and not isb(j2, 1490)
          and not any(max(abs(a - b) for a, b in zip(j2.getpixel((600, y)), ImageColor.getrgb(BROWN))) < 6 for y in (1126, 1140)))

    # dada-dadi / nana-nani / parents without photos: big dark-brown name in the middle, place in the band (CT, 13 Oct 2026)
    nb = ImageColor.getrgb(cards.NAME_BROWN)
    fctx = cards.Ctx("boy", ROOT / "samples", "clear")
    for kind in ("dada_dadi", "nana_nani", "parents"):
        f0 = cards.family_pair(fctx, kind, {"display_name": "મંજુલાબેન મનુભાઈ કેશવલાલ ગજ્જર", "village": "ચલોડા"}).convert("RGB")
        f1 = cards.family_pair(fctx, kind, {"display_name": "મંજુલાબેન શાહ", "village": "ચલોડા", "photos": ["photos/couple.jpg"]}).convert("RGB")
        px = list(zip(*[iter(f0.crop((0, 640, 1200, 1180)).tobytes())] * 3))
        dark = sum(1 for p in px if max(abs(a - b) for a, b in zip(p, nb)) < 14)
        check(f"{kind} without photos: name large in dark brown, band 1207-1357",
              dark > 20000 and isb(f0, 1210) and isb(f0, 1354) and not isb(f0, 1200) and not isb(f0, 1362), str(dark))
        px1 = list(zip(*[iter(f1.crop((0, 640, 1200, 1180)).tobytes())] * 3))
        check(f"{kind} with a photo: photo layout (no big name)", sum(1 for p in px1 if max(abs(a - b) for a, b in zip(p, nb)) < 14) < 2000)

    # business card: a long company name (or typed lines) wraps and never runs into the photo (CT, 13 Oct 2026)
    bctx = cards.Ctx("boy", ROOT / "samples", "clear")
    long_c = {"style": "business", "company": "Shree Sample Saw Mill, Kurundwad-Kolhapur + Construction Material Supplier",
              "desc": "Retailer of Building Material"}
    two_c = dict(long_c, company="Shree Sample Saw Mill, Kurundwad-Kolhapur\n+ Sample Construction, Kolhapur")
    short_c = dict(long_c, company="Sample Electronics, Deesa")
    bl, bt, bs = (cards.work(bctx, c, "x", "photos/g3.jpg").convert("RGB") for c in (long_c, two_c, short_c))
    dark_in = lambda im, box: any(max(p) < 60 for p in zip(*[iter(im.crop(box).tobytes())] * 3))
    check("long business name: wrapped, nothing between the text column and the photo, photo frame unchanged",
          not dark_in(bl, (800, 560, 838, 1440)) and not dark_in(bt, (800, 560, 838, 1440))
          and ImageChops.difference(bl.crop((838, 560, 1190, 1300)), bs.crop((838, 560, 1190, 1300))).getbbox() is None)
    def dark_rows(im, x0=40, x1=800, y0=560, y1=1440):     # text lines (runs of rows with dark ink) in the text column
        n, inside = 0, False
        for y in range(y0, y1):
            ink = any(max(im.getpixel((x, y))) < 60 for x in range(x0, x1, 3))
            n, inside = n + (ink and not inside), ink
        return n
    check("business name typed on 2 lines: kept as lines (4 rows: 2 + 2 wrapped), short name: 1 row",
          dark_rows(bt) == 4 and dark_rows(bs) == 1, f"{dark_rows(bt)} / {dark_rows(bs)}")
    b3 = cards.work(bctx, dict(long_c, company="Shree Kailashpati Saw Mill, Kurundwad-Kolhapur\n+ Construction Contractor"),
                    "x", "photos/g3.jpg").convert("RGB")
    check("a typed line that nearly fits stays whole (2 + 1 rows), not into the photo",
          dark_rows(b3) == 3 and not dark_in(b3, (800, 560, 838, 1440)), str(dark_rows(b3)))
    # 2-4 businesses (app rows Name / Work): stacked on the occupation card, text from the top without a logo
    bb = {"style": "business", "company": "Shree Sample Saw Mill, Kurundwad-Kolhapur", "desc": "Retailer of Building Material",
          "businesses": [{"name": "Shree Sample Saw Mill, Kurundwad-Kolhapur", "desc": "Retailer of Building Material"},
                         {"name": "Sample Construction Contractor", "desc": ""}]}
    b4 = cards.work(bctx, bb, "x", "photos/g3.jpg").convert("RGB")
    top_ink = next((y for y in range(560, 1440) if any(max(b4.getpixel((x, y))) < 60 for x in range(40, 800, 3))), 9999)
    check("2 businesses: stacked, text starts a little below the photo top (582), not into the photo",
          dark_rows(b4) in (3, 4) and 600 < top_ink < 700 and not dark_in(b4, (800, 560, 838, 1440)), f"{dark_rows(b4)} rows, top {top_ink}")
    acc = ImageColor.getrgb(bctx.accent)
    def bullets(im):                                        # theme-colour squares at the left edge of the text column
        n, inside = 0, False
        for y in range(560, 1440):
            hit = any(max(abs(a - b) for a, b in zip(im.getpixel((x, y)), acc)) < 30 for x in range(51, 66, 2))
            n, inside = n + (hit and not inside), hit
        return n
    fam = dict(bb, businesses=[dict(bb["businesses"][0], type="Family Business"), dict(bb["businesses"][1], type="Own Business")])
    bf = cards.work(bctx, fam, "x", "photos/g3.jpg").convert("RGB")
    check("2 businesses: one bullet each (Family Business on its own bulleted line)", bullets(b4) == 2 and bullets(bf) == 2,
          f"{bullets(b4)} / {bullets(bf)}")
    check("one business: no bullet (approved layout)", bullets(cards.work(bctx, short_c, "x", "photos/g3.jpg").convert("RGB")) == 0)
    from vcards.narration import scene_text
    pb = {"name": "x", "first_name": "x", "work": bb}
    nb = scene_text("work", pb, bb)
    nfam = scene_text("work", pb, dict(bb, businesses=[dict(bb["businesses"][0], type="Family Business"), dict(bb["businesses"][1], type="Own Business")]))
    check("narration: 2+ businesses, a Family Business row is said 'Family Business <name>'",
          nfam == "x નુ ઓક્યુપેશન. Family Business Shree Sample Saw Mill, Kurundwad-Kolhapur, Retailer of Building Material. Sample Construction Contractor.", nfam)
    check("narration: one sentence per business",
          nb == "x નુ ઓક્યુપેશન. Shree Sample Saw Mill, Kurundwad-Kolhapur, Retailer of Building Material. Sample Construction Contractor.", nb)
    nf = scene_text("father", pb, {"jobs": [{"type": "Business", "name": "Shree Sample Saw Mill, Kurundwad-Kolhapur", "desc": "x"},
                                            {"type": "Job", "name": "Sample Bank, Kolhapur", "desc": ""}]})
    check("narration: parent rows, the candidate's own business says only its type", nf == "પિતા. Business, Job, Sample Bank, Kolhapur.", nf)

    # a line break typed in the form's text box = a new line on the card (CT, 12 Oct 2026)
    def rows(im, y0=1122, y1=1500):            # number of text lines (runs of rows with white ink) in the band
        n, inside = 0, False
        for y in range(y0, y1):
            ink = any(min(im.getpixel((x, y))) > 235 for x in range(40, 1160, 3))
            n, inside = n + (ink and not inside), ink
        return n
    check("typed line breaks: kept, spaces / empty lines tidied",
          cards.hard_lines("Masters in Mass Media\r\n\r\n  HouseWife ") == ["Masters in Mass Media", "HouseWife"]
          and cards.hard_lines(None) == [])
    br = sib([{"who": "અ", "text": "Masters in Mass Media\nHouseWife"},
              {"who": "બ", "text": "M S in Information Technology (IT)\nWorking at Google, Bangalore"}])
    sp = sib([{"who": "અ", "text": "Masters in Mass Media HouseWife"},
              {"who": "બ", "text": "M S in Information Technology (IT) Working at Google, Bangalore"}])
    check("typed line breaks: 4 lines on the sibling card (without: 3)", rows(br) == 4 and rows(sp) == 3, f"{rows(br)} / {rows(sp)}")
    one = cards.sibling_no_photo(cards.Ctx("girl", ROOT, "clear"),
                                 {"relation": "bahen", "display_name": "x y", "details": [{"who": "", "text": "Masters in Mass Media\nHouseWife"}]}).convert("RGB")
    check("typed line breaks: sibling card without photo too", rows(one, 1181, 1473) == 2, str(rows(one, 1181, 1473)))

    r = subprocess.run([sys.executable, "render.py", str(sample), "--fast"], cwd=ROOT, capture_output=True, text=True)
    mp4 = ROOT / "out" / "sample-girl" / "preview.mp4"
    check("sample preview video renders", r.returncode == 0 and mp4.exists(), r.stderr[-200:])

    print("\nALL PASSED" if not FAILED else f"\n{len(FAILED)} FAILED: {', '.join(FAILED)}")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
