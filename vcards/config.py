"""Static configuration. All geometry is in px on the 1200x1500 master canvas
(values taken from the CommuTree PSD templates)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

W, H = 1200, 1500
FPS_NUM, FPS_DEN = 30000, 1001          # 29.97 fps, same as the outro clip
FPS = FPS_NUM / FPS_DEN

_F = ASSETS / "fonts"
FONTS = {
    "akhand_xb": _F / "akhand-gujarati/AKHANDGUJARATI-EXTRABOLD.OTF",
    "akhand_b": _F / "akhand-gujarati/AKHANDGUJARATI-BOLD.OTF",
    "arista": _F / "zarista/_Z__ARISTA_TRIAL.TTF",
    "anek_sb": _F / "anek-gujarati/AnekGujaratiCondensed-SemiBold.ttf",
    "anek_b": _F / "anek-gujarati/AnekGujaratiCondensed-Bold.ttf",
    "barlow_m": _F / "barlow/Barlow-Medium.ttf",
    "barlow_sb": _F / "barlow/Barlow-SemiBold.ttf",
    "barlow_b": _F / "barlow/Barlow-Bold.ttf",
    "barlow_xb": _F / "barlow/Barlow-ExtraBold.ttf",
    "barlowc_sb": _F / "barlow/BarlowCondensed-SemiBold.ttf",
    "barlowc_b": _F / "barlow/BarlowCondensed-Bold.ttf",
    "poppins_sb": _F / "poppins/Poppins-SemiBold.ttf",
    "poppins_b": _F / "poppins/Poppins-Bold.ttf",
}

BG_IMAGE = ASSETS / "bg/patch_bg.jpg"
LOGO = ASSETS / "brand/ct_logo.png"
OUTRO = ASSETS / "outro/ct_premium_end_slide.mp4"
MUSIC = ASSETS / "music/bg_music.mp3"     # default background music (use --no-music to skip)

BROWN = "#98755C"
DARK = "#282828"
BLACK = "#000000"
NEAR_BLACK = "#1E1C1B"
WHITE = "#FFFFFF"
LOGO_BLUE = "#0669A4"

THEMES = {
    "boy": {"accent": "#0669A4", "job_bullet": "square"},
    "girl": {"accent": "#FF4081", "job_bullet": "dot"},
}

TIMING = {
    "dissolve": 1.0,        # card-to-card cross dissolve (s)
    "lead": 0.65,           # card start -> narration start: after the 1 s dissolve's second half
    "tail": 1.05,           # narration end -> next card start
    "intro_lead": 0.2,
    "intro_tail": 0.6,
    "min_card": 3.0,
    "min_intro": 2.6,
    "gallery_photo": 2.0,   # seconds per gallery photo (hard cuts)
    "zoom_end": 1.21,       # Ken Burns 1.00 -> 1.21, linear
    "ticker_px_s": 210,     # hobby ticker speed
    "subline_xfade": 0.4,
    "hold": 0.5,            # extra reading time after the narration, every card (s)
}

# extra reading time on top of TIMING["hold"] for text-heavy cards (s).
# A profile can override per card with  "hold": {"hero": 4, ...}  in its JSON.
# Total time after the voice on a card = tail + hold + extra. Matched to the original reference videos
# (about 2.2 s on average, a bit more on text-heavy cards).
HOLD_EXTRA = {
    "hero": 0.5,
    "parents": 0.3,
    "father": 0.3,
    "sibling": 0.5,      # applies to sibling1, sibling2, ...
    "education": 0.5,
    "work": 0.5,
}

# Automatic photo framing (photos without "crop"/"focus" in the JSON): head to chest.
FRAMING = {
    "face_frac": 1 / 3.0,   # face height = 1/3 of the frame height  -> head to chest
    "headroom": 0.55,       # space above the face, in face heights
    "max_upscale": 2.2,     # never enlarge the source more than this (keeps photos sharp)
}

AUDIO = {
    "sr": 44100,
    "voice_rms_db": -20.0,      # voiced-frame RMS target (~ -18 LUFS)
    "music_below_voice_db": 24.0,
    "music_fade_in": 0.3,
    "music_fade_out": 1.0,
    "peak_db": -1.0,
    "main_lufs": -12.0,         # final loudness of the main part (outro clip is ~ -10.5 LUFS)
}
