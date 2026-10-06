# Guj Premium Video

Repo: `commutreecode/guj-premium-video`


Renders CommuTree **Premium Member** video biodatas (Gujarati, 1200×1500, 4:5) from one JSON file per profile:
intro → profile card → family cards → education / job / property → photo gallery → CT outro clip.

Layouts, fonts, colours and baselines are taken from the CommuTree PSD templates.
Boy theme = blue `#0669A4`, girl theme = pink `#FF4081`.

> **No personal data in this repo.** Real profiles, photos, PSDs and renders live in `profiles/` and `out/`, which are git-ignored.

---

## Setup

```bash
# Ubuntu / Debian
sudo apt install ffmpeg libraqm0
pip install -r requirements.txt
python3 -c "from PIL import features; print('raqm:', features.check('raqm'))"   # must print True
```

Without RAQM, Gujarati conjuncts break, so the renderer refuses to start.

## Workflow (one profile)

```bash
# 1. put the JSON + photos in profiles/<name>/  (photo paths in the JSON are relative to it)
python3 render.py profiles/<name>/profile.json
#    -> out/<id>/cards/*.png      check every card
#    -> out/<id>/preview.mp4      silent, estimated timings, with outro
#    -> out/<id>/narration.txt    review / edit the Gujarati narration here
#    -> out/<id>/tts_input.txt    paste this into Google AI Studio

# 2. Google AI Studio -> Generate speech -> paste tts_input.txt -> download WAV
#    (always use the same voice + style instruction; keep a clear pause between blocks)
#    Voice: <TBD>   Style instruction: <TBD>

# 3. merge
python3 render.py profiles/<name>/profile.json --voice voice.wav
#    -> out/<id>/final.mp4  and  out/<id>/alignment.txt
```

`alignment.txt` shows how the voice was split per card (expected vs actual seconds).
A ratio outside 0.55–1.8 is flagged `<-- check`. If the voice has too few pauses the render stops
and asks you to regenerate it with clearer pauses.

If you edit `narration.txt` before generating the voice, step 3 uses your edited text for timing.

Every voice render also writes `out/<id>/voice_spans.json` (which seconds of the voice file go on which card).
If a sentence lands on the wrong card, fix the times there and re-run with `--spans out/<id>/voice_spans.json`.
A card can take several pieces, e.g. `"work": [[42.0, 45.3], [27.5, 32.6]]` (played in that order).

Background music `assets/music/bg_music.mp3` is used by default (`--music FILE` to change, `--no-music` to skip).

Options: `--spans FILE` (manual voice split), `--cards-only` (PNGs + narration only), `--fast` (quick encode), `--no-outro`, `--out DIR`.

## Timing rules

| Item | Rule |
|---|---|
| Card length | narration + 0.6 s before + 1.1 s after + reading time (min 3 s; intro min 2.6 s) |
| Reading time | 1 s on every card; extra on text-heavy cards: hero +3, Mata-Pita +2.5, Pita +2.5, siblings +3, education +2.5, job +3 (`HOLD_EXTRA` in `config.py`; per profile: `"hold": {"hero": 6}`) |
| Card → card | 1.0 s cross-dissolve |
| Gallery | photos below the header (y 150–1110), 2.0 s each, hard cuts, zoom 1.00 → 1.21 linear; no narration |
| Gallery sub-line | rotates: hobbies (centred; scrolls if too long) → sect → year/status/height, all vertically centred |
| Audio | voice levelled, background music ~24 dB under voice, main part normalised to −12 LUFS |
| Outro | `assets/outro/ct_premium_end_slide.mp4` appended (has its own voice + music) |
| Output | 1200×1500, 29.97 fps, H.264 yuv420p, AAC 44.1 kHz |

All numbers live in `vcards/config.py`.

## JSON reference

See `samples/profile.example.json` (dummy data, girl theme, bullet-style job).
Every section is optional; missing sections are skipped.

| Field | Notes |
|---|---|
| `id`, `version` | `id` names the output folder |
| `theme` | `boy` \| `girl` |
| `privacy` | `clear` \| `blur` \| `hide` — applies to the candidate's own photos; `hide` also drops the gallery |
| `name`, `first_name` | `first_name` is used in "… નો પરિચય" titles |
| `native_village`, `city` | shown as "(ગામઃ …, હાલઃ …)" |
| `birth_year` or `dob`, `marital_status`, `height` | info line, e.g. `2000, Single, 5'8"` |
| `sect` | e.g. "દેરાવાસી જૈન" |
| `photos.hero`, `photos.gallery[]` | photo specs (below) |
| `dada_dadi`, `nana_nani` | `display_name`, `village`, `photos[1–2]` |
| `parents` | `display_name`, `village`, `city`, `sect`, `photos[1–2]` |
| `mother`, `father` | `name`, `photo`, `occupation` (string or list of lines) |
| `siblings[]` | `relation` (`bahen-banevi`, `bhai-bhabhi`, `mota-bhai-bhabhi`, `bhai`, `bahen`), `display_name`, `place`, `photos[1–2]`, `details[{who, text}]` |
| `education[]` | `degree`, `institute`, `photo` (first photo found is used) |
| `work` | `style: business` → `label`, `logo`, `company`, `desc`, `photo`; `style: bullets` → `bullets[]` |
| `property[]` | bullet lines |
| `hobbies[]` | gallery ticker |
| `hold` | optional per-card reading time override in seconds, e.g. `{"hero": 6, "sibling": 4}` |
| `sections[]` | optional custom order / subset of: intro, hero, dada_dadi, nana_nani, parents, mother, father, siblings, education, work, property, gallery |

**Photo spec:** `"photos/x.jpg"` or `{"src": "photos/x.jpg", "focus": [fx, fy]}` or
`{"src": …, "crop": [x0, y0, x1, y1]}` (fractions 0–1 of the source image).
Without crop/focus the photo is centre-cropped with focus `[0.5, 0.35]`.

One photo in a family card → centred single frame (landscape photos get a wide frame); two → side by side.

## Quick test (sample data only)

```bash
python3 render.py samples/profile.example.json          # out/sample-girl/preview.mp4
```

## Layout

```
render.py            CLI
vcards/config.py     canvas, fonts, colours, timings, audio levels
vcards/text.py       Gujarati/Latin mixed runs (Akhand has no Latin glyphs), fit, wrap
vcards/imgs.py       photo crop, rounded masks, privacy
vcards/cards.py      every card layout (PSD coordinates)
vcards/narration.py  Gujarati narration templates
vcards/scenes.py     JSON -> ordered scenes
vcards/video.py      timeline, dissolves, gallery zoom/ticker, ffmpeg encode + outro concat
vcards/audio.py      pause detection, voice-to-card alignment, mix
tools/make_sample_photos.py   regenerates the placeholder sample photos
```
