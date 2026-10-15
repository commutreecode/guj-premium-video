"""Turn a profile JSON into an ordered list of scenes. Missing sections are skipped."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import cards
from .config import VOICE_LAST_SECTION
from .narration import scene_text

DEFAULT_ORDER = ["intro", "hero", "dada_dadi", "nana_nani", "parents", "mother", "father",
                 "siblings", "education", "work", "past", "awards", "property", "gallery"]


def sib_list_seconds(n: int) -> float:
    """Reading time of the siblings text slide (music only): 4.5 s, +1.2 s per sibling above 2."""
    from .config import TIMING
    return TIMING["silent_card"] + TIMING["sib_list_per"] * max(0, n - 2)


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
    past_fb = cand[2] if len(cand) > 2 else work_fb      # past experience card: another candidate photo on the right
    par_ph = (p.get("parents") or {}).get("photos") or []
    couple = par_ph[0] if len(par_ph) == 1 else None
    def mk(f):
        return f() if images else None

    out: list[Scene] = []
    has_gal = bool((p.get("photos") or {}).get("gallery")) and ctx.privacy != "hide"
    order = list(p.get("sections", DEFAULT_ORDER))
    # sections after the occupation card are shown with music only (no narration, no voice)
    silent = set(order[order.index(VOICE_LAST_SECTION) + 1:]) if VOICE_LAST_SECTION in order else set()
    for sec in order:
        n0 = len(out)
        if sec == "intro":
            out.append(Scene("intro", "card", mk(lambda: cards.intro(ctx)), scene_text("intro", p, None)))
        elif sec == "hero":
            out.append(Scene("hero", "card", mk(lambda: cards.hero(ctx, p)), scene_text("hero", p, None)))
        elif sec in ("dada_dadi", "nana_nani", "parents") and p.get(sec):
            out.append(Scene(sec, "card", mk(lambda: cards.family_pair(ctx, sec, p[sec])), scene_text(sec, p, p[sec])))
        elif sec in ("mother", "father") and p.get(sec):
            out.append(Scene(sec, "card", mk(lambda: cards.single_parent(ctx, sec, p[sec], couple)), scene_text(sec, p, p[sec])))
        elif sec == "siblings":
            sibs = p.get("siblings", [])
            plain = [s for s in sibs if cards.no_photo(s)]
            grouped = len(plain) >= 2        # 2+ siblings without a photo: ONE text slide, music only (CT, 15 Oct 2026)
            for i, s in enumerate(sibs, 1):
                if grouped and cards.no_photo(s):
                    if s is plain[0]:        # where the first of them would be
                        out.append(Scene("sib_list", "card", mk(lambda: cards.siblings_list(ctx, plain)), "",
                                         extra={"min_dur": sib_list_seconds(len(plain))}))
                    continue
                sid = f"sibling{i}"          # a sibling with a photo: own card + narration, as before
                out.append(Scene(sid, "card", mk(lambda: cards.sibling(ctx, s)), scene_text(sid, p, s)))
        elif sec == "education" and p.get("education"):
            out.append(Scene("education", "card", mk(lambda: cards.education(ctx, p["education"], first, edu_fb)),
                             scene_text("education", p, p["education"])))
        elif sec == "work" and p.get("work"):
            out.append(Scene("work", "card", mk(lambda: cards.work(ctx, p["work"], first, work_fb)), scene_text("work", p, p["work"])))
        elif sec == "past" and cards.past_items(p.get("work")):     # after the occupation card: music only
            out.append(Scene("past", "card", mk(lambda: cards.past_experience(ctx, cards.past_items(p["work"]), first, past_fb)), ""))
        elif sec == "awards" and cards.award_items(p) and not (has_gal and cards.single_award(p)):   # music only
            out.append(Scene("awards", "card", mk(lambda: cards.awards_card(ctx, cards.award_items(p), first)), ""))
        elif sec == "property" and p.get("property") and not (has_gal and cards.single_property(p)):
            out.append(Scene("property", "card", mk(lambda: cards.property_card(ctx, p["property"], first)),
                             scene_text("property", p, p["property"])))
        elif sec == "gallery":
            gal = (p.get("photos") or {}).get("gallery") or []
            if has_gal:
                out.append(Scene("gallery", "gallery",
                                 extra={"photos": [ctx.photo(g) for g in gal] if images else gal,
                                        "min_dur": sum(need for _, need in cards.gallery_sublines(ctx, p)) if images else 0}))
        if sec in silent:
            for sc in out[n0:]:
                sc.text = ""
    return out, ctx
