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
#    -> out/<id>/tts_input.txt    paste this into ElevenLabs (Text to Speech)

# 2. ElevenLabs -> Text to Speech -> paste tts_input.txt (whole text in one go) -> download MP3/WAV
#    (always the same voice, model and settings; keep the blank lines between blocks)
#    Voice: <TBD>   Model: <TBD>   Settings: <TBD>

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
| Card length | narration + 0.3 s before + 1.9–2.4 s after (as in the original reference videos; min 3 s; intro min 2.6 s) |
| Reading time | included above: 0.5 s on every card, +0.3–0.5 s on text-heavy cards (`HOLD_EXTRA` in `config.py`; per profile: `"hold": {"hero": 3}`) |
| Card → card | 1.0 s cross-dissolve |
| Gallery | photos below the header (y 150–1110), 2.0 s each, hard cuts, zoom 1.00 → 1.21 linear; no narration |
| Gallery sub-line | rotates: hobbies (centred; scrolls if too long) → sect → year/status/height, all vertically centred |
| Audio | voice levelled, background music ~24 dB under voice for the **whole video, outro included**; outro voice levelled to match; normalised to −12 LUFS |
| Outro | `assets/outro/ct_premium_end_slide.mp4` (picture + its own voice; our music continues under it) |
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

**Automatic framing:** photos without `crop`/`focus` are framed **head to chest** using face detection
(OpenCV DNN, `assets/models/`), also for couple and group photos; the gallery zoom moves towards the face.
Low-resolution photos are never enlarged more than 2.2×, so very small photos stay a little wider.

**Photo spec:** `"photos/x.jpg"` or `{"src": "photos/x.jpg", "focus": [fx, fy]}` or
`{"src": …, "crop": [x0, y0, x1, y1]}` (fractions 0–1 of the source image).
Without crop/focus the photo is centre-cropped with focus `[0.5, 0.35]`.

One photo in a family card → centred single frame (landscape photos get a wide frame); two → side by side.

## Intake form (Google Form → Sheet → profile folder)

`forms/gpv_form.gs` (v2) is a Google Apps Script that creates the Gujarati intake form and its response Sheet.
`forms/gpv_form_v1.gs` is the first version, kept only for responses already collected with it.

v2: birth **year** only · optional **couple photo** for Dada-Dadi, Nana-Nani, Mata-Pita (landscape gets the
wide frame) · siblings **branch by relation** (બહેન-બનેવી / ભાઈ-ભાભી / મોટા ભાઈ-ભાભી / ભાઈ / બહેન each get their
own fields, up to 2 siblings) · own **Income / Property** section.
v2.1: one **height** dropdown (4'6"…6'6") · occupation **branches by type** (ફેમિલી બિઝનેસ / પોતાનો બિઝનેસ / નોકરી /
પ્રોફેશનલ / કોઈ નહીં) · sibling questions without the "ભાઈ/બહેન n - " prefix. An existing v2 form is upgraded in place by
running `upgradeV2` once in its Apps Script project (same links, responses and upload questions kept).
Expected result: `forms/EXPECTED_FORM_LAYOUT.md`.

1. script.google.com → New project → paste `forms/gpv_form.gs` → run `createGujPremiumForm` (authorise).
2. The log prints the form, share and Sheet links, plus the **file-upload questions** to add by hand
   (Apps Script cannot create upload questions). Use exactly the titles printed, in the sections named.
3. Each submission creates `Drive / Guj Premium Video - Profiles / <id>_<first name>/` with `profile.json` +
   `photos/` (hero, g1…g10, dadi, dada, dd_couple, nani, nana, nn_couple, mata, pita, par_couple, s1_*, s2_*,
   edu, work, logo) and fills the Sheet's `JSON` and `Folder` columns.
4. Download that folder as a zip → `profiles/<name>/` → render.
5. After editing a row in the Sheet, run `rebuildSelectedRow` (or `rebuildAllRows`).
6. `importFromV1` copies responses from the v1 form's Sheet into the v2 Sheet (mapped to v2 questions,
   tagged "v1 row N" in a `Source` column, photos reused from Drive). Safe to run again.

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
