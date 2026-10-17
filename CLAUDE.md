# Notes for Claude / contributors

- **Never commit personal data.** Real profiles, photos, voice files, PSDs and renders belong in
  `profiles/` and `out/` (git-ignored). The repo contains only `samples/` (dummy data, placeholder photos).
- Gujarati text needs Pillow with RAQM; `vcards/text.py` refuses to start without it.
- Akhand Gujarati has no Latin glyphs: text is split into Gujarati/Latin runs (`text.runs`). Keep that.
- Akhand's half-શ looks like ર (વિશ્વાસ read "વિરવાસ"): `text.runs` draws every શ્ + consonant cluster (not શ્ર)
  with Anek Gujarati at the same letter height (`GU_FALLBACK`). Keep that.
- Layout numbers in `vcards/cards.py` come from the CommuTree PSD templates (1200x1500). Change them
  only on request, and compare the card PNGs before/after.
- Timings and audio levels live in `vcards/config.py`.
- Test after any change:
  `python3 render.py samples/profile.example.json --cards-only` (fast) and
  `python3 render.py samples/profile.example.json --fast` (full preview with gallery + outro).

## Rendering a profile in a new chat session (token-light)

1. `git clone --depth 1 https://github.com/commutreecode/guj-premium-video && cd guj-premium-video`
2. `pip install -r requirements.txt` (check RAQM: `python3 -c "from PIL import features; print(features.check('raqm'))"`)
3. The user uploads the profile folder from Drive (`<id>_<name>.zip`: `profile.json` + `photos/`).
   Unzip it to `profiles/<name>/`.
4. Stage 1: `python3 render.py profiles/<name>/profile.json` → give the user `out/<id>/preview.mp4` and
   `out/<id>/tts_input.txt` (the team generates the voice in ElevenLabs).
5. Stage 2: `python3 render.py profiles/<name>/profile.json --voice <voice.wav>` → `out/<id>/final.mp4`.
   Check `alignment.txt`; if a sentence is on the wrong card, edit `out/<id>/voice_spans.json` and re-run
   with `--spans`.
6. Do not read or print source files unless something needs changing — the code is already tested.

## Narration
Default style (team-approved, Oct 2026, Eleven v4): see "Narration style" in README.md — every block except the
last ends with `[long pause]` (keeps the voice split reliable). **Team rule: the voice stops after the occupation
card** (`VOICE_LAST_SECTION = "work"` in `vcards/config.py`): Income / Property and the gallery have music only. If the team edits the
TTS text for a profile, put the same text into `out/<id>/narration.txt` (keep the `[NN id]` labels) before
running with `--voice`, so the voice is split on the right cards.

2+ siblings without a photo: one music-only text slide `sib_list` (not narrated) where the first of them would be;
siblings with a photo keep their card + narration (CT, 15 Oct 2026). A silent card in the middle is fine: the voice is
split over the narrated cards only. Narration rule change → bump `NARRATION_STYLE` in the automation's `auto.py`.

The team PSDs (15 + 17 Oct 2026) are the reference for card looks: see "Team PSDs" and "Team PSDs, second round" in
README.md (17 Oct: hero and the single sibling card kept as they are on purpose; mother / father card with job rows,
education + occupation card and a single achievement follow the team's exact images, see "Team's exact images"). Fonts used: Akhand Gujarati,
Anek Gujarati (incl. AnekGujaratiSemiCondensed-Bold.ttf for Income / Property, OFL, added 17 Oct 2026), Barlow / Barlow
Condensed (incl. BarlowCondensed-BoldItalic.ttf, OFL, added 15 Oct 2026), Poppins.

Text in a brown band is centred by its letters (`_centred_base`: same space above and below), never by fixed
baselines; a long name / work in a parent band splits before " (" so a bracket part is its own line
(`_bracket_lines`). Self-test: "parent band … text centred" (CT, 16 Oct 2026).
A one-person photo gets the wide frame only with 2+ faces (`wide_frame`; 1 face = portrait frame like the father);
the grandparents' village is centred below the band 1206..1387 (CT, 17 Oct 2026).

## Never silently degrade
If a feature can't work (face detector, RAQM), the render must stop with an error. Run `python3 tests/run_tests.py`
after any change; keep `requirements.txt` upper bounds until a new major version passes the tests.

## The automation depends on this repo
The private repo `commutreecode/guj-premium-video-auto` (team web app + GitHub Actions) clones `main` of this repo for
every run, so a push here changes the next video immediately. Keep stable: `--narration-only` output
(`tts_input.txt`, `scenes.json`), the `[progress] N` stdout lines, the `VOICE CHECK:` error prefix, `--voice/--out`
options, `<out>/thumbnail.jpg` (uploaded as the video's thumbnail) and the photo spec fields `rotate` / `trim`
(written by the app's photo editor). If the narration wording/rules change, bump `NARRATION_STYLE` in that repo's `auto.py` too.
Push only after `python3 tests/run_tests.py` passes (it also runs on GitHub on every push and every Monday).
