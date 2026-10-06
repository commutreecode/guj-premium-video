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
