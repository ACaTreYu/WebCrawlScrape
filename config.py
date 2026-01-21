"""
WebCrawlScrape - Configuration Module
Centralized settings and common extension presets.
"""

# -----------------------------
# DEFAULT SETTINGS
# -----------------------------
DEFAULT_DOWNLOAD_DIR = "downloads"
DEFAULT_MAX_PAGES = 200
DEFAULT_TIMEOUT = 15

# -----------------------------
# EXTENSION PRESETS
# -----------------------------
EXTENSION_PRESETS = {
    "images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico"},
    "documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx"},
    "archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "audio": {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"},
    "code": {".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"},
    "midi": {".mid", ".midi"},
    "arc": {".zip", ".map", ".rec", ".png", ".jpg"},  # ARC-specific
    "all": set(),  # Empty = match any extension
}

# Default extensions if none specified
DEFAULT_EXTENSIONS = EXTENSION_PRESETS["archives"] | EXTENSION_PRESETS["images"]


def get_extensions_from_preset(preset_name):
    """Get extension set from a preset name."""
    return EXTENSION_PRESETS.get(preset_name.lower(), set())


def parse_extensions(ext_string):
    """
    Parse extension string into a set.

    Accepts:
        - Preset name: "images", "archives", etc.
        - Comma-separated: ".zip,.png,.jpg"
        - Mixed: "images,.pdf,.doc"

    Returns:
        Set of extensions (lowercase, with dots)
    """
    if not ext_string:
        return DEFAULT_EXTENSIONS

    result = set()
    parts = [p.strip().lower() for p in ext_string.split(",")]

    for part in parts:
        if part in EXTENSION_PRESETS:
            result |= EXTENSION_PRESETS[part]
        elif part.startswith("."):
            result.add(part)
        elif part:
            result.add(f".{part}")

    return result if result else DEFAULT_EXTENSIONS
