# Guj Premium Video

Repo: `commutreecode/guj-premium-video`


Renders CommuTree **Premium Member** video biodatas (Gujarati, 1200×1500, 4:5) from one JSON file per profile:
intro → profile card → family cards → education / job / property → photo gallery → CT outro clip.

Layouts, fonts, colours and baselines are taken from the CommuTree PSD templates.
Boy theme = blue `#0669A4`, girl theme = pink `#FF4081`.

> **No personal data in this repo.** Real profiles, photos, PSDs and renders live in `profiles/` and `out/`, which are git-ignored.

**Day-to-day use is automated:** the team fills the profile in the "Guj Premium Video" web app and clicks buttons;
GitHub Actions in the private repo `commutreecode/guj-premium-video-auto` clones this renderer and makes the narration
and the video (no AI, no tokens per video). This repo is the renderer only; the commands below are for testing or a
manual render.

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
#    (model Eleven v4, the team's Instant Clone voice, same settings every time; keep the [long pause] tags
#    and the blank lines between blocks; never edit the text inside ElevenLabs)

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

Options: `--spans FILE` (manual voice split), `--cards-only` (PNGs + narration only), `--narration-only`
(narration.txt / tts_input.txt / scenes.json without photos — used by the automation), `--fast` (quick encode),
`--no-outro`, `--out DIR`.

**Contract with the automation** (keep these stable): `--narration-only` writes `tts_input.txt` + `scenes.json`
(ids of the narrated cards); a final render prints `[progress] N` (0–100) lines while making frames (the app's
progress bar); a voice that misses a block stops the render with a line starting `VOICE CHECK:` (shown to the team
as "Check voice: …").

## Narration style (default, team-approved)

```text
કોમ્યુટ્રી સી ટી પ્રીમિયમ મેમ્બર. [long pause]
<full name>. [long pause]
પરિવાર પરિચય. દાદા-દાદી, <names>. [long pause]
નાના-નાની, <names>. [long pause]
માતા-પિતા, <names>. [long pause]
માતા. <occupation>. [long pause]
પિતા. <occupation>. [long pause]
<relation>, <sibling names>. [long pause]
<first name> નુ એજ્યુકેશન. <degree 1>. + <degree 2>. [long pause]
<first name> નુ ઓક્યુપેશન. <job / business>.
```

- `[long pause]` is an **Eleven v4 audio tag** (not spoken). It makes ElevenLabs leave clearly longer gaps
  between cards (measured 1.1–1.85 s vs ≤ 0.8 s inside cards), so the voice is split per card reliably.
- **The voice stops after the occupation card** (team rule, Oct 2026): Past Experience, Income / Property and the photo
  gallery are shown with background music only (cards 4.5 s) and are not part of the narration
  (`VOICE_LAST_SECTION`, `TIMING["silent_card"]` in `vcards/config.py`).
- **Team PSDs** (CT, 15 Oct 2026, 79 hand-made profiles are the reference): occupation card "X નુ ઓક્યુપેશન:" +
  "જોબ / વ્યવસાય"; names Barlow Condensed Bold Italic dark brown, work in brackets golden brown; job = DESIGNATION /
  "at Company" / extra lines / logo below, photo right; one business = TYPE label / name / (work) / logo below, photo
  right, voice says the label; 2-4 businesses = heading ("BUSINESS" or `work.heading`), a bullet per business, a logo per
  row on the right (`businesses[i].logo`), NO photo. Education card "X નુ એજ્યુકેશન:"; degree typed on 2 lines (a line
  in brackets small). `edu_work_one: true` = education + occupation on one card (`edu_work`, one voice block, only when
  short); `property_card: true` = Income / Property on its own card even with one line; `mother/father.education` =
  "(M.Com + LLB)" above the type in the band; same village and city -> "(બોટાદ)".
- **Team PSDs, second round** (CT + team, 17 Oct 2026, 73 more PSDs; review page with today / after cards): parents card
  with a sect = name / (village, city) / (sect) all inside the brown band; education = Anek Gujarati Condensed, big; ONE
  degree: candidate photo on the right, no bullet, up to 3 lines; 2+ degrees: no photo, full width, round bullets; girl:
  title pink, "EDUCATION / અભ્યાસ" brown; girl job: "at Company" crimson #A71043; "as a / as an" split like "at";
  2-4 job roles (a new line that is not in brackets and does not start with at / as a) = a bullet per role, no photo, logo
  under the first role; 2+ businesses: a row's Type is its own bulleted line, the "BUSINESS" heading only when no row has
  a Type; Past Experience = title "Past Experience:" only, 1 item in the job style with the logo below + photo, 2-3 items
  bullets with a logo each, no photo; 2-3 achievements = title "Achievements:" only, round bullets; Income / Property
  text in Anek Gujarati SemiCondensed Bold, bigger. Unchanged on purpose: hero, one sibling without a photo. Spoken text
  unchanged.
- **Team's exact images** (CT, 17 Oct 2026; measured, within 3 px): mother / father card with Type / Name / Work rows
  (Harit) = band 1145..1474, photo 515..1125, type and name the same size, the work smaller and in brackets, no "+", a gap
  between jobs; education + occupation card (Binjal) = big Anek degrees, round brown bullets, girl titles pink, business
  TYPE black / name / (work), logo below, baseline steps 154 / 112 / 262 / 156 / 128 / 121; ONE achievement (Raj) =
  "ACHIEVEMENTS:" + the text centred, Anek SemiCondensed Bold 122, lines 184 px apart, a typed line break (`\n` in the
  text) = a line on the slide; shown on its own slide only with the app tick `award_card: true` (otherwise one achievement
  stays in the gallery strip); 2-3 achievements (Vicky) = brown "Achievements:" (Poppins SemiBold, the closest free font
  to the PSD's Nirmala UI), a theme-colour rounded square each, Anek Condensed SemiBold 114, 203 px per item.
- **Photo frame + grandparents' place** (CT, 17 Oct 2026, a profile with "સુથરી" touching the band and a zoomed mother
  photo): a one-person card picks the wide couple frame only for a photo with 2+ faces; ONE face = the portrait frame
  (same as the father) even when the photo is almost square; no face = by shape (`wide_frame`). Dada-dadi / nana-nani
  with photos: band 1206..1387 (the PSD place), the village line centred between the band and the bottom edge
  (fixed letter height, so every village sits the same). Self-test: "grandparents: the village never touches the band".
- **Business heading** (CT, 15 Oct 2026): `work.heading` (the team's own occupation type, e.g. "Businesses in Kolhapur")
  with 2+ businesses is drawn once above the list (no bullet) and said first in the occupation sentence; ignored for one business.
- **2 or more siblings without a photo** (CT, 15 Oct 2026): they are left out of the narration and shown together on
  ONE text slide (`sib_list`, music only, 4.5 s + 1.2 s per sibling above 2). Look = the team PSD (CT, 16 Oct 2026):
  relation title in light brown `SIB_LIST_TITLE` #97755F (siblings next to each other with the same relation share one
  title), then per sibling the name in the theme colour (boy blue / girl pink) and `(<place>)` on the line below, or
  `(<occupation / education>)` when no place is filled; spacing measured on the PSD (3 siblings: title 147 px, names
  95 px), more lines → gaps closed a little, then letters and gaps smaller together (`cards.siblings_list`). Siblings with a
  photo keep their own card and their narration; a single sibling without a photo keeps its own card as before.
- If a voice has fewer parts than the narration (a block was not spoken), the render stops with `VOICE CHECK: …`
  instead of putting every later sentence on the wrong card.
- In the education / occupation lines the first name is said without a title (`CA હિનલ` → `હિનલ`).
- A parent in the candidate's own business (the occupation names the candidate's company) says only the label:
  `પિતા. Business.` — the company and description are spoken once, on the occupation card (CT, Oct 2026).
- Villages, city, birth year, marital status, height, sect, colleges and the sibling's occupation are shown on
  the cards but not spoken. Templates: `vcards/narration.py`.
- **If the wording must change, change the Narration text first (Sheet / `narration.txt`), then make the voice
  from it.** The video uses that exact text to place the voice.

## Voice splitting

`vcards/align.py`: with `[long pause]` markers the card boundaries are the longest gaps; otherwise each phrase is
matched to the voice by syllables. If nearby settings disagree, `alignment.txt` marks the cards `<-- check`
(the automation then uploads the video as `<Name_En>_CHECK.mp4` and shows "Check voice: please watch cards …").

## Timing rules

| Item | Rule |
|---|---|
| Card length | voice starts 0.65 s after the card's start (the 1 s cross-dissolve is centred on the cut, so that is 0.15 s after the dissolve has finished), 1.55–2.05 s after it (tail 1.05 + hold 0.5 + 0–0.5 extra; as in the original reference videos; min 3 s; intro min 2.6 s) |
| Reading time | included above: 0.5 s on every card, +0.3–0.5 s on text-heavy cards (`HOLD_EXTRA` in `config.py`; per profile: `"hold": {"hero": 3}`) |
| Opening | the hero card for 0.5 s, then a 0.3 s dissolve into the intro, so the first frame (the thumbnail in WhatsApp etc.) shows the candidate; also saved as `thumbnail.jpg` |
| Card → card | 1.0 s cross-dissolve |
| Gallery | photos fill the top too (y 0–1110, behind the title bar); faces framed below the bar (y > 150) during the whole zoom; a photo with too little above the head starts lower, enlargement capped at 2.0× at the end of the zoom (small/WhatsApp photos are framed a bit wider instead of looking blurred) + light sharpening, 2.0 s each, hard cuts, zoom 1.00 → 1.21 linear; no narration |
| Gallery sub-line | rotates: hobbies (centred; scrolls if too long) → sect → year/status/height, all vertically centred |
| Audio | voice levelled, background music ~16 dB under voice, rising softly from low to full level in the first 1.5 s (the file's own slow fade-in is skipped), then steady for the **whole video, outro included**; outro voice levelled to match; one fixed gain to −12 LUFS + peak limiter (no level pumping) |
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
| `name`, `first_name` | `first_name` is used in "… નો પરિચય" titles. The on-screen header/intro text is "કોમ્યુટ્રી CT પ્રિમિયમ મેમ્બર" (as in the PSD); the narration says "કોમ્યુટ્રી સી ટી પ્રીમિયમ મેમ્બર" (spelled for the TTS) — both intended |
| `name_en` | full name in English; not drawn, the automation names the video file `<Name_En>.mp4` |
| `native_village`, `city` | shown as "(ગામઃ …, હાલઃ …)" |
| `birth_year` or `dob`, `marital_status`, `height` | info line, e.g. `2000, Single, 5'8"` |
| `sect` | e.g. "દેરાવાસી જૈન" |
| `photos.hero`, `photos.gallery[]` | photo specs (below) |
| `dada_dadi`, `nana_nani` | `display_name`, `village`, `photos[1–2]`; without photos (also `parents`): the name large in dark brown (#684124, max 2 lines) in the middle, the place in white in the brown band (no empty photo area) |
| `parents` | `display_name`, `village`, `city`, `sect`, `photos[1–2]` |
| `mother`, `father` | `name`, `photo`, `occupation` (string or list of lines); optional `jobs[{type, name, desc}]` (app rows, max 4): band = type biggest, name smaller, work smallest (brackets typed in Work are kept; a long name / work on 2 lines), never taller than the approved band, photo always ends above it; a job in the candidate's own business says only its type |
| `siblings[]` | any number of entries, one card each (the team app allows 5, the old form 2); `relation` (`bahen-banevi`, `bhai-bhabhi`, `mota-bhai-bhabhi`, `bhai`, `bahen`), `display_name`, `place`, `photos[1–2]`, `details[{who, text}]` (a line break typed in `text` = a new line in the card's brown band, same card; no details = no band, titles a little lower and the photo(s) scaled up) |
| `education[]` | `degree`, `institute` (shown in brackets, colour #652B02), `photo` (first photo found is used); one card for up to 7 degrees, every degree in the same size (1–3: approved layout; 4–7: tighter, smaller text, the photo is dropped if the text would get too small next to it) |
| `work` | `style: business` → `label`, `logo`, `company`, optional `businesses[{type, name, desc}]` (2–4 → stacked on the same occupation card with a theme-colour bullet each; type "Family Business" → its own bulleted line "Family Business" with the name and work below it; one narration sentence each, a Family Business row said as "Family Business <name>, <work>", other types not spoken; without a logo the text starts a little below the photo top) (a typed line break = a new line; a name too long for one line wraps, never into the photo), `desc`, `photo`; `style: bullets` → `bullets[]`, `photo`, `logo` (job: the logo is drawn ABOVE the company name, a white background made transparent; `photo` = the person, right side). A `photo` without a face (the app's box is "LOGO / COMPANY CARD": a logo or a visiting card) is drawn in the text column above the company name (light background made transparent; a coloured card kept as a rounded card, up to 300 px tall) and the right side gets a candidate photo; a photo with a face is the person, as before. Optional `past`: `[{"text", "logo"}]` (max 3; a plain string also works) → own **Past Experience** card after the occupation card, each logo above its text (left column), a candidate photo on the right like the occupation card (3rd gallery photo, else the occupation card's), music only |
| `property[]` | bullet lines (the app/form put `Income: …` as the first line when an income is given) |
| `awards[]` | Awards / Achievements (max 3): ONE line (with gallery photos) → gallery strip after a theme-colour bullet; 2–3 → own card after Past Experience (music only) |
| `hobbies[]` | gallery ticker: a long text scrolls once to its end (the gallery gets longer if needed). Strip order: one award, one property line, hobbies, સમાજ, birth year / marital / height. With exactly ONE `property` line (and gallery photos) that line is shown in the same strip after a square bullet in the theme colour (no "PROPERTY:" word) instead of an own card. A gallery photo cropped tight above the head fills the area from the top (the face sits higher, partly behind the title bar): no blurred band, no light bar (blurred top edge only for a very wide + short strip) |
| `hold` | optional per-card reading time override in seconds, e.g. `{"hero": 6, "sibling": 4}` |
| `sections[]` | optional custom order / subset of: intro, hero, dada_dadi, nana_nani, parents, mother, father, siblings, education, work, property, gallery |

**Automatic framing:** photos without `crop`/`focus` are framed **head to chest** using face detection
(OpenCV DNN, `assets/models/`), also for couple and group photos; the gallery zoom moves towards the face.
Low-resolution photos are never enlarged more than 2.2× on the cards; in the gallery the limit is 2.0× at the end of
the zoom (`FRAMING` in `config.py`), so very small photos are framed a little wider instead of looking blurred.

**Photo types:** JPEG, PNG, WEBP, HEIC/HEIF (pillow-heif), AVIF, GIF (first frame), BMP, TIFF; 16-bit, CMYK and
fully opaque PNGs are converted to 8-bit RGB as before. A **see-through** photo (✎ Background → Transparent in the app: a PNG
`<role>.png` with alpha) stays RGBA: the card's own design shows behind the person (photo frames, family / sibling / job
cards) and in the gallery the slide background shows behind it; face framing still runs on the photo flattened on white.

**Gujarati conjuncts:** Akhand's half-શ looks like ર, so શ્ + consonant clusters (શ્વ, શ્ચ, શ્ન, શ્મ …, not શ્ર) are
drawn with Anek Gujarati at the same letter height (`GU_FALLBACK` in `vcards/text.py`).

**Photo spec:** `"photos/x.jpg"` or `{"src": "photos/x.jpg", "focus": [fx, fy]}` or
`{"src": …, "crop": [x0, y0, x1, y1]}` (fractions 0–1 of the source image).
Without crop/focus the photo is centre-cropped with focus `[0.5, 0.35]`.

**Photo edits from the app** (✎ on a photo box): `{"src": …, "rotate": 90, "trim": [x0, y0, x1, y1]}`.
`rotate` = 0/90/180/270 clockwise, `trim` = fractions 0–1 of the rotated photo. Both are applied first (the uploaded
file is never changed), then the photo is framed as usual (head to chest, couple/landscape frames, gallery zoom), so
the approved look stays the same. A wrong value stops the render with an error.

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
3. Each submission creates `Drive / Guj Premium Video - Profiles / <id>_<first name>/` (`<id>` = ProfileID from the
   CommuTree link, or `gpv-<sheet row>` without a link) with `profile.json` +
   `photos/` (hero, g1…g10, dadi, dada, dd_couple, nani, nana, nn_couple, mata, pita, par_couple, s1_*, s2_*,
   edu, work, logo) and fills the Sheet's `JSON` and `Folder` columns.
4. Download that folder as a zip → `profiles/<name>/` → render.
5. After editing a row in the Sheet, run `rebuildSelectedRow` (or `rebuildAllRows`).
6. `importFromV1` copies responses from the v1 form's Sheet into the v2 Sheet (mapped to v2 questions,
   tagged "v1 row N" in a `Source` column, photos reused from Drive). Safe to run again.

## Self-test

`python3 tests/run_tests.py` checks Gujarati shaping, the face detector (OpenCV < 5), card rendering, the narration
markers, voice splitting on a real measured pause pattern and a full sample render. It runs on GitHub on every push
and every Monday (`.github/workflows/test.yml`), so a breaking library update shows up as a red test, not in a video.
`requirements.txt` pins tested major versions.

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
vcards/audio.py      pause detection, music loop/fade, final mix
vcards/align.py      voice -> cards split ([long pause] markers, phrase matching, VOICE CHECK)
vcards/syllables.py  Gujarati syllable counter (phrase matching)
tests/run_tests.py   self-test (also on GitHub: .github/workflows/test.yml)
forms/               Google Form v1 / v2.1 Apps Scripts (old intake; the team now uses the web app)
tools/make_sample_photos.py   regenerates the placeholder sample photos
```
