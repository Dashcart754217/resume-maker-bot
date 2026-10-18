import os

# ========================================================
# TELEGRAM BOT CONFIGURATION
# ========================================================
# Railway or local environment variable BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Temporary directories for uploads & generated resumes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "resumes")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========================================================
# COLOR THEMES FOR PDF RESUME
# ========================================================
RESUME_THEMES = {
    "navy": {
        "name": "👔 Modern Navy",
        "primary": "#1A365D",      # Deep Navy
        "secondary": "#2B6CB0",    # Accent Slate Blue
        "text": "#2D3748",         # Charcoal Dark
        "muted": "#718096",        # Slate Gray
        "line": "#E2E8F0",         # Light Gray Line
        "tag_bg": "#EDF2F7",       # Light Badge Background
    },
    "emerald": {
        "name": "🌲 Executive Emerald",
        "primary": "#1C4532",      # Deep Emerald Green
        "secondary": "#276749",    # Accent Green
        "text": "#2D3748",
        "muted": "#718096",
        "line": "#E2E8F0",
        "tag_bg": "#F0FFF4",
    },
    "charcoal": {
        "name": "🖤 Classic Charcoal (ATS Favorite)",
        "primary": "#1A202C",      # Dark Graphite
        "secondary": "#4A5568",    # Medium Slate
        "text": "#2D3748",
        "muted": "#718096",
        "line": "#CBD5E0",
        "tag_bg": "#EDF2F7",
    },
    "burgundy": {
        "name": "🍷 Royal Burgundy",
        "primary": "#5E1724",      # Deep Wine Red
        "secondary": "#9B2C2C",    # Crimson Accent
        "text": "#2D3748",
        "muted": "#718096",
        "line": "#E2E8F0",
        "tag_bg": "#FFF5F5",
    }
}

DEFAULT_THEME = "navy"

