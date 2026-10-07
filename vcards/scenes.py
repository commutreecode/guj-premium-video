"""Turn a profile JSON into an ordered list of scenes. Missing sections are skipped."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import cards
from .narration import scene_text

DEFAULT_ORDER = ["intro", "hero", "dada_dadi", "nana_nani", "parents", "mother", "father",
                 "siblings", "education", "work", "property", "gallery"]


@dataclass
class Scene:
    id: str
    kind: str                      # card | gallery
    image: object = None           # PIL image for cards
    text: str = ""                 # narration ("" = silent)
    extra: dict = field(default_factory=dict)


def build(p: dict, base: Path, images: bool = True) -> tuple[list[Scene], cards.Ctx]:
    """images=False: same scene list and narration, without drawing cards or opening photos
    (used by --narration-only, e.g. by the automation before the photos are downloaded)."""
    theme = p.get("theme", "boy")
    ctx = cards.Ctx(theme, base, p.get("privacy", "clear"))
    first = p.get("first_name") or p["name"].split()[0]
    # photo fallbacks: education / job cards use candidate photos when none were given for them,
    # single-parent cards use the parents' couple photo when a parent has no own photo
    ph = p.get("photos") or {}
    cand = [] if ctx.privacy == "hide" else (list(ph.get("gallery") or []) or ([ph["hero"]] if ph.get("hero") else []))
    edu_fb = cand[0] if cand else None
    work_fb = cand[1] if len(cand) > 1 else edu_fb
    par_ph = (p.get("parents") or {}).get("photos") or []
    couple = par_ph[0] if len(par_ph) == 1 else None
    def mk(f):
        return f() if images else None

    out: list[Scene] = []
    for sec in p.get("sections", DEFAULT_ORDER):
        if sec == "intro":
            out.append(Scene("intro", "card", mk(lambda: cards.intro(ctx)), scene_text("intro", p, None)))
        elif sec == "hero":
            out.append(Scene("hero", "card", mk(lambda: cards.hero(ctx, p)), scene_text("hero", p, None)))
        elif sec in ("dada_dadi", "nana_nani", "parents") and p.get(sec):
            out.append(Scene(sec, "card", mk(lambda: cards.family_pair(ctx, sec, p[sec])), scene_text(sec, p, p[sec])))
        elif sec in ("mother", "father") and p.get(sec):
            out.append(Scene(sec, "card", mk(lambda: cards.single_parent(ctx, sec, p[sec], couple)), scene_text(sec, p, p[sec])))
        elif sec == "siblings":
            for i, s in enumerate(p.get("siblings", []), 1):
                sid = f"sibling{i}"
                out.append(Scene(sid, "card", mk(lambda: cards.sibling(ctx, s)), scene_text(sid, p, s)))
        elif sec == "education" and p.get("education"):
            out.append(Scene("education", "card", mk(lambda: cards.education(ctx, p["education"], first, edu_fb)),
                             scene_text("education", p, p["education"])))
        elif sec == "work" and p.get("work"):
            out.append(Scene("work", "card", mk(lambda: cards.work(ctx, p["work"], first, work_fb)), scene_text("work", p, p["work"])))
        elif sec == "property" and p.get("property"):
            out.append(Scene("property", "card", mk(lambda: cards.property_card(ctx, p["property"], first)),
                             scene_text("property", p, p["property"])))
        elif sec == "gallery":
            gal = (p.get("photos") or {}).get("gallery") or []
            if gal and ctx.privacy != "hide":
                out.append(Scene("gallery", "gallery",
                                 extra={"photos": [ctx.photo(g) for g in gal] if images else gal}))
    return out, ctx
