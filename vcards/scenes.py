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


def build(p: dict, base: Path) -> tuple[list[Scene], cards.Ctx]:
    theme = p.get("theme", "boy")
    ctx = cards.Ctx(theme, base, p.get("privacy", "clear"))
    first = p.get("first_name") or p["name"].split()[0]
    out: list[Scene] = []
    for sec in p.get("sections", DEFAULT_ORDER):
        if sec == "intro":
            out.append(Scene("intro", "card", cards.intro(ctx), scene_text("intro", p, None)))
        elif sec == "hero":
            out.append(Scene("hero", "card", cards.hero(ctx, p), scene_text("hero", p, None)))
        elif sec in ("dada_dadi", "nana_nani", "parents") and p.get(sec):
            out.append(Scene(sec, "card", cards.family_pair(ctx, sec, p[sec]), scene_text(sec, p, p[sec])))
        elif sec in ("mother", "father") and p.get(sec):
            out.append(Scene(sec, "card", cards.single_parent(ctx, sec, p[sec]), scene_text(sec, p, p[sec])))
        elif sec == "siblings":
            for i, s in enumerate(p.get("siblings", []), 1):
                sid = f"sibling{i}"
                out.append(Scene(sid, "card", cards.sibling(ctx, s), scene_text(sid, p, s)))
        elif sec == "education" and p.get("education"):
            out.append(Scene("education", "card", cards.education(ctx, p["education"], first),
                             scene_text("education", p, p["education"])))
        elif sec == "work" and p.get("work"):
            out.append(Scene("work", "card", cards.work(ctx, p["work"], first), scene_text("work", p, p["work"])))
        elif sec == "property" and p.get("property"):
            out.append(Scene("property", "card", cards.property_card(ctx, p["property"], first),
                             scene_text("property", p, p["property"])))
        elif sec == "gallery":
            gal = (p.get("photos") or {}).get("gallery") or []
            if gal and ctx.privacy != "hide":
                out.append(Scene("gallery", "gallery", extra={"photos": [ctx.photo(g) for g in gal]}))
    return out, ctx
