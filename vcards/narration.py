"""Gujarati narration text for each card. Edit the templates here to change
the wording of every future video. English words are kept as-is (TTS reads them)."""
from __future__ import annotations

import re


NUM_GU = ["શૂન્ય", "એક", "બે", "ત્રણ", "ચાર", "પાંચ", "છ", "સાત", "આઠ", "નવ", "દસ", "અગિયાર", "બાર"]
MARITAL_GU = {"single": "અપરિણીત", "unmarried": "અપરિણીત", "divorced": "છૂટાછેડા લીધેલ",
              "widow": "વિધવા", "widower": "વિધુર"}


def height_words(h: str) -> str:
    m = re.match(r"\s*(\d+)\s*'\s*(\d+)?", str(h or ""))
    if not m:
        return str(h or "")
    ft, inch = int(m.group(1)), int(m.group(2) or 0)
    s = f"{NUM_GU[ft] if ft < len(NUM_GU) else ft} ફૂટ"
    if inch:
        s += f" {NUM_GU[inch] if inch < len(NUM_GU) else inch} ઇંચ"
    return s


def clean(s: str) -> str:
    s = re.sub(r"[()]", "", s or "")
    s = s.replace(":", ",").replace("&", "and")
    s = re.sub(r"\s*,\s*,", ",", s)
    return re.sub(r"\s+", " ", s).strip(" ,")


def _join(parts) -> str:
    return ". ".join(clean(p) for p in parts if p and clean(p)) + "."


TITLES = re.compile(r"^(CA|CS|CMA|CFA|CPA|Dr\.?|Adv\.?|Er\.?|Prof\.?|ડૉ\.?|ડો\.?)\s+", re.I)
CARD_PAUSE = "[long pause]"     # ElevenLabs v4 audio tag at the end of every block except the last


def plain_first_name(p: dict) -> str:
    """First name without a professional title: 'CA હિનલ' -> 'હિનલ' (the hero line keeps the full name)."""
    first = p.get("first_name") or p["name"].split()[0]
    return TITLES.sub("", first).strip() or first


GENERIC_WORK = {"business", "family business", "own business", "job", "service", "professional", "farming",
                "agriculture", "housewife", "home maker", "homemaker", "retired", "student", "self employed"}


def _norm(s) -> str:
    """Lower case, letters / digits only (Gujarati too), single spaces: for comparing business names."""
    return " ".join(re.sub(r"[^\w]+", " ", str(s or "").lower()).split())


def _work_keys(work) -> list[str]:
    """Names of the candidate's business / company (full text and the part before the first comma)."""
    w = work or {}
    texts = []
    if w.get("style", "business") == "bullets":
        for b in w.get("bullets") or []:
            b = str(b)
            texts.append(re.split(r"\s+at\s+", b, maxsplit=1, flags=re.I)[-1])
    else:
        texts.append(w.get("company") or "")
        texts += [str((b or {}).get("name") or "") for b in (w.get("businesses") or [])]
    keys = []
    for t in texts:
        for k in (_norm(t), _norm(str(t).split(",")[0])):
            if len(k) >= 5 and k not in GENERIC_WORK and k not in keys:
                keys.append(k)
    return keys


def same_business(occ_lines, work) -> bool:
    """True when a parent's occupation names the candidate's own business / company."""
    keys = _work_keys(work)
    text = _norm(" ".join(str(o) for o in occ_lines or []))
    return bool(keys) and any(k in text for k in keys)


def scene_text(scene_id: str, p: dict, data) -> str:
    """Default narration style (team-approved, Oct 2026). Names only for family; Mata/Pita/sibling cards say
    the relation (+ occupation for parents) without names; villages, city, year, height, sect, colleges and
    job labels are shown on the cards but not spoken."""
    first = plain_first_name(p)
    if scene_id == "intro":
        return "કોમ્યુટ્રી સી ટી પ્રીમિયમ મેમ્બર."
    if scene_id == "hero":
        return _join([p["name"]])
    if scene_id in ("dada_dadi", "nana_nani"):
        lab = "પરિવાર પરિચય. દાદા-દાદી" if scene_id == "dada_dadi" else "નાના-નાની"
        return _join([f"{lab}, {data.get('display_name', '')}"])
    if scene_id == "parents":
        return _join([f"માતા-પિતા, {data.get('display_name', '')}"])
    if scene_id in ("mother", "father"):
        lab = "માતા" if scene_id == "mother" else "પિતા"
        occ = data.get("occupation") or []
        occ = [occ] if isinstance(occ, str) else occ
        occ = [clean(o) for o in occ if clean(o)]
        from .cards import parent_jobs
        jobs = parent_jobs(data)
        if jobs:      # app rows Type / Name / Work: a job in the candidate's own business says only its type
            parts = []
            for j in jobs:
                if j["name"] and same_business([j["name"]], p.get("work")):
                    parts.append(clean(j["type"]) or "Business")
                else:
                    parts += [clean(x) for x in (j["type"], j["name"], j["desc"]) if clean(x)]
            return _join([lab, ", ".join(parts)])
        if occ and same_business(occ, p.get("work")):
            # same business as the candidate (CT, 13 Oct 2026): only the label ("પિતા. Business."); the
            # company and description are spoken once, on the candidate's occupation card
            keys = _work_keys(p.get("work"))
            first = occ[0] if not any(k in _norm(occ[0]) for k in keys) else "Business"
            return _join([lab, first])
        return _join([lab, ", ".join(occ)])
    if scene_id.startswith("sibling"):
        from .cards import SIBLING_TITLES
        rel = SIBLING_TITLES.get(data.get("relation", ""), data.get("relation", ""))
        return _join([f"{rel.replace(' - ', '-')}, {data.get('display_name', '')}"])
    if scene_id == "education":
        degs = [clean(e.get("degree", "")) for e in data if clean(e.get("degree", ""))]
        return _join([f"{first} નુ એજ્યુકેશન"] + [d if i == 0 else f"+ {d}" for i, d in enumerate(degs)])
    if scene_id == "work":
        if data.get("style") == "bullets":
            items = [clean(b) for b in data.get("bullets", []) if clean(b)]
        else:                    # per business "name, work" (2-4 businesses: one sentence each)
            from .cards import business_items
            items = []
            from .cards import is_family_business
            bizs = business_items(data)
            from .cards import business_heading
            if business_heading(data):           # 2+ businesses with a heading: said first (CT, 15 Oct 2026)
                items.append(clean(business_heading(data)))
            for b in bizs:
                parts = [ln for x in [b["name"], b["desc"]] for ln in str(x or "").splitlines()]
                txt = ", ".join(clean(x) for x in parts if clean(x))          # a typed line break = a comma
                # 2+ businesses: a Family Business row is said as on the slide, "Family Business <name>, <work>"
                if len(bizs) > 1 and is_family_business(b.get("type")) and txt:
                    txt = "Family Business " + txt
                items.append(txt)
        return _join([f"{first} નુ ઓક્યુપેશન"] + [i for i in items if i])
    if scene_id == "property":
        return _join(["આવક અને પ્રોપર્ટી"] + list(data))
    return ""


def estimate_seconds(text: str) -> float:
    """Spoken length estimate for the silent preview (syllables; English counts ~0.6)."""
    from .align import PARAMS, phrase_syllables, phrases
    ps = phrases(text)
    return sum(0.35 + phrase_syllables(x, PARAMS["w_en"]) / 5.3 for x in ps)


def write_files(out_dir, profile_id: str, items):
    """items: list of (scene_id, text). Writes narration.txt (review) and tts_input.txt (paste)."""
    lines = [f"# CommuTree video narration - profile {profile_id}",
             "# Review / edit the text below (keep the [NN id] labels and the [long pause] tags). Then paste",
             "# tts_input.txt into ElevenLabs (Eleven v4) in ONE go, same voice + settings every time.",
             "# Download MP3 or WAV and run:  python3 render.py <profile.json> --voice <file>",
             ""]
    plain = []
    for i, (sid, txt) in enumerate(items, 1):
        txt = txt if i == len(items) else f"{txt} {CARD_PAUSE}"
        lines += [f"[{i:02d} {sid}]", txt, ""]
        plain += [txt, ""]
    (out_dir / "narration.txt").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "tts_input.txt").write_text("\n".join(plain).strip() + "\n", encoding="utf-8")
