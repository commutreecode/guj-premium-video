# Notes for Claude / contributors

- **Never commit personal data.** Real profiles, photos, voice files, PSDs and renders belong in
  `profiles/` and `out/` (git-ignored). The repo contains only `samples/` (dummy data, placeholder photos).
- Gujarati text needs Pillow with RAQM; `vcards/text.py` refuses to start without it.
- Akhand Gujarati has no Latin glyphs: text is split into Gujarati/Latin runs (`text.runs`). Keep that.
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
last ends with `[long pause]` (keeps the voice split reliable). If the team edits the
TTS text for a profile, put the same text into `out/<id>/narration.txt` (keep the `[NN id]` labels) before
running with `--voice`, so the voice is split on the right cards.

## Never silently degrade
If a feature can't work (face detector, RAQM), the render must stop with an error. Run `python3 tests/run_tests.py`
after any change; keep `requirements.txt` upper bounds until a new major version passes the tests.
