"""Gujarati narration text for each card. Edit the templates here to change
the wording of every future video. English words are kept as-is (TTS reads them)."""
from __future__ import annotations

import re

from .config import TIMING

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


def scene_text(scene_id: str, p: dict, data) -> str:
    first = p.get("first_name") or p["name"].split()[0]
    if scene_id == "intro":
        return "કોમ્યુટ્રી સી ટી પ્રીમિયમ મેમ્બર."
    if scene_id == "hero":
        place = ", ".join(x for x in [f"ગામ {p['native_village']}" if p.get("native_village") else "",
                                      f"હાલ {p['city']}" if p.get("city") else ""] if x)
        year = p.get("birth_year") or str(p.get("dob", ""))[:4]
        ms = MARITAL_GU.get(str(p.get("marital_status", "")).lower(), p.get("marital_status", ""))
        info = ", ".join(x for x in [f"જન્મ વર્ષ {year}" if year else "", ms,
                                      f"ઊંચાઈ {height_words(p.get('height'))}" if p.get("height") else ""] if x)
        return _join([p["name"], place, info, p.get("sect")])
    if scene_id in ("dada_dadi", "nana_nani"):
        lab = "પરિવાર પરિચય. દાદા-દાદી" if scene_id == "dada_dadi" else "નાના-નાની"
        return _join([f"{lab}, {data.get('display_name', '')}",
                      f"ગામ {data['village']}" if data.get("village") else ""])
    if scene_id == "parents":
        return _join([f"માતા-પિતા, {data.get('display_name', '')}",
                      ", ".join(x for x in [f"ગામ {data['village']}" if data.get("village") else "",
                                            f"હાલ {data['city']}" if data.get("city") else ""] if x)])
    if scene_id in ("mother", "father"):
        lab = "માતા" if scene_id == "mother" else "પિતા"
        occ = data.get("occupation") or []
        occ = [occ] if isinstance(occ, str) else occ
        return _join([f"{lab} {data.get('name', '')}", ", ".join(clean(o) for o in occ)])
    if scene_id.startswith("sibling"):
        from .cards import SIBLING_TITLES
        rel = SIBLING_TITLES.get(data.get("relation", ""), data.get("relation", ""))
        rel = rel.replace(" - ", "-")
        head = f"{rel}, {data.get('display_name', '')}"
        if data.get("place"):
            head += f", {data['place']}"
        return _join([head] + [f"{d.get('who', '')}, {d.get('text', '')}" for d in data.get("details", [])])
    if scene_id == "education":
        parts = [f"{first} નો અભ્યાસ"]
        for e in data:
            parts.append(", ".join(x for x in [e.get("degree"), e.get("institute")] if x))
        return _join(parts)
    if scene_id == "work":
        lab = f"{first} નો વ્યવસાય"
        if data.get("label"):
            lab += f", {data['label']}"
        if data.get("style") == "bullets":
            return _join([lab] + data.get("bullets", []))
        return _join([lab, data.get("company"), data.get("desc")])
    if scene_id == "property":
        return _join(["આવક અને પ્રોપર્ટી"] + list(data))
    return ""


def estimate_seconds(text: str) -> float:
    letters = len(re.sub(r"[\s.,:;()\-]", "", text))
    pauses = text.count(".") + text.count(",") * 0.5
    return letters / TIMING["chars_per_sec"] + pauses * 0.25


def write_files(out_dir, profile_id: str, items):
    """items: list of (scene_id, text). Writes narration.txt (review) and tts_input.txt (paste)."""
    lines = [f"# CommuTree video narration - profile {profile_id}",
             "# Review / edit the text below. Then paste tts_input.txt into Google AI Studio",
             "# (Generate speech). Keep the block ORDER; leave a clear pause between blocks.",
             "# Download the result as WAV and run:  python3 render.py <profile.json> --voice <file.wav>",
             ""]
    plain = []
    for i, (sid, txt) in enumerate(items, 1):
        lines += [f"[{i:02d} {sid}]", txt, ""]
        plain += [txt, ""]
    (out_dir / "narration.txt").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "tts_input.txt").write_text("\n".join(plain).strip() + "\n", encoding="utf-8")
