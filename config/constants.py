"""
Application-wide constants, quality maps, and format configurations.
"""

import os
import sys
from pathlib import Path

# ──────────────────────────────────────────────
# Application Identity
# ──────────────────────────────────────────────
APP_NAME = "CrowTube"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Hussein Al-Fourati"
APP_ORGANIZATION = "Crow-Dev Team"

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────

def get_base_dir() -> Path:
    """Get the application base directory for bundled assets (works for dev and frozen)."""
    if getattr(sys, 'frozen', False):
        # When running as a PyInstaller --onefile exe, assets are extracted to sys._MEIPASS
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def get_data_dir() -> Path:
    """Get the directory for persistent data (in AppData/Local for Windows)."""
    # Use standard AppData/Local on Windows, or ~/.crowtube on other OS
    if os.name == 'nt':
        local_app_data = os.environ.get('LOCALAPPDATA', str(Path.home() / "AppData" / "Local"))
        return Path(local_app_data) / APP_NAME
    else:
        return Path.home() / f".{APP_NAME.lower()}"

BASE_DIR = get_base_dir()
DATA_ROOT = get_data_dir()

ASSETS_DIR = BASE_DIR / "assets"
TOOLS_DIR = BASE_DIR / "tools"
STYLES_DIR = BASE_DIR / "ui" / "styles"

LOGS_DIR = DATA_ROOT / "logs"
DATA_DIR = DATA_ROOT / "data"

# Ensure runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default download location
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")

# Database
HISTORY_DB_PATH = str(DATA_DIR / "history.db")
SETTINGS_FILE_PATH = str(DATA_DIR / "settings.ini")

# Tools
FFMPEG_PATH = str(TOOLS_DIR / "ffmpeg.exe")
FFPROBE_PATH = str(TOOLS_DIR / "ffprobe.exe")
YTDLP_PATH = str(TOOLS_DIR / "yt-dlp.exe")

# ──────────────────────────────────────────────
# Video Quality Map → yt-dlp format strings
# ──────────────────────────────────────────────
VIDEO_QUALITY_MAP: dict[str, str] = {
    "Best Available": "bv*+ba/b",
    "2160p (4K)":     "bv*[height<=2160]+ba/b[height<=2160]",
    "1440p":          "bv*[height<=1440]+ba/b[height<=1440]",
    "1080p":          "bv*[height<=1080]+ba/b[height<=1080]",
    "720p":           "bv*[height<=720]+ba/b[height<=720]",
    "480p":           "bv*[height<=480]+ba/b[height<=480]",
    "360p":           "bv*[height<=360]+ba/b[height<=360]",
}

VIDEO_QUALITIES: list[str] = list(VIDEO_QUALITY_MAP.keys())

# ──────────────────────────────────────────────
# Video Container Formats
# ──────────────────────────────────────────────
VIDEO_FORMATS: list[str] = ["MP4", "MKV", "WEBM"]

VIDEO_FORMAT_MAP: dict[str, str] = {
    "MP4": "mp4",
    "MKV": "mkv",
    "WEBM": "webm",
}

# ──────────────────────────────────────────────
# Audio Formats & Quality
# ──────────────────────────────────────────────
AUDIO_FORMATS: list[str] = ["MP3", "M4A", "AAC", "WAV", "FLAC"]

AUDIO_FORMAT_MAP: dict[str, str] = {
    "MP3":  "mp3",
    "M4A":  "m4a",
    "AAC":  "aac",
    "WAV":  "wav",
    "FLAC": "flac",
}

AUDIO_QUALITIES: list[str] = ["128 kbps", "192 kbps", "256 kbps", "320 kbps"]

AUDIO_QUALITY_MAP: dict[str, str] = {
    "128 kbps": "128",
    "192 kbps": "192",
    "256 kbps": "256",
    "320 kbps": "320",
}

# ──────────────────────────────────────────────
# Download Defaults
# ──────────────────────────────────────────────
DEFAULT_VIDEO_QUALITY = "1080p"
DEFAULT_VIDEO_FORMAT = "MP4"
DEFAULT_AUDIO_FORMAT = "MP3"
DEFAULT_AUDIO_QUALITY = "192 kbps"
DEFAULT_CONCURRENT_DOWNLOADS = 3
MAX_CONCURRENT_DOWNLOADS = 5

# ──────────────────────────────────────────────
# UI Constants
# ──────────────────────────────────────────────
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1100
WINDOW_DEFAULT_HEIGHT = 750
SIDEBAR_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 64

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
LOG_FILE_PATH = str(LOGS_DIR / "app.log")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3

# ──────────────────────────────────────────────
# Network
# ──────────────────────────────────────────────
DEFAULT_SOCKET_TIMEOUT = 30
DEFAULT_RETRIES = 10
DEFAULT_FRAGMENT_RETRIES = 10

# ──────────────────────────────────────────────
# Supported Platforms
# ──────────────────────────────────────────────
SUPPORTED_PLATFORMS: dict[str, dict] = {
    "youtube": {
        "name": "YouTube",
        "icon": "▶",
        "color": "#FF0000",
        "bg_color": "rgba(255, 0, 0, 0.15)",
        "domains": ["youtube.com", "youtu.be", "youtube-nocookie.com", "m.youtube.com"],
        "needs_cookies": False,
    },
    "instagram": {
        "name": "Instagram",
        "icon": "",
        "color": "#E1306C",
        "bg_color": "rgba(225, 48, 108, 0.15)",
        "domains": ["instagram.com", "www.instagram.com", "m.instagram.com"],
        "needs_cookies": True,
    },
    "facebook": {
        "name": "Facebook",
        "icon": "",
        "color": "#1877F2",
        "bg_color": "rgba(24, 119, 242, 0.15)",
        "domains": ["facebook.com", "www.facebook.com", "m.facebook.com", "fb.watch", "fb.com"],
        "needs_cookies": True,
    },
    "twitter": {
        "name": "X / Twitter",
        "icon": "𝕏",
        "color": "#1DA1F2",
        "bg_color": "rgba(29, 161, 242, 0.15)",
        "domains": ["twitter.com", "x.com", "t.co", "mobile.twitter.com"],
        "needs_cookies": True,
    },
    "tiktok": {
        "name": "TikTok",
        "icon": "♪",
        "color": "#00F2EA",
        "bg_color": "rgba(0, 242, 234, 0.15)",
        "domains": ["tiktok.com", "www.tiktok.com", "vm.tiktok.com", "m.tiktok.com"],
        "needs_cookies": False,
    },
    "reddit": {
        "name": "Reddit",
        "icon": "",
        "color": "#FF4500",
        "bg_color": "rgba(255, 69, 0, 0.15)",
        "domains": ["reddit.com", "www.reddit.com", "old.reddit.com", "v.redd.it"],
        "needs_cookies": False,
    },
    "twitch": {
        "name": "Twitch",
        "icon": "",
        "color": "#9146FF",
        "bg_color": "rgba(145, 70, 255, 0.15)",
        "domains": ["twitch.tv", "www.twitch.tv", "clips.twitch.tv"],
        "needs_cookies": False,
    },
}

# Browsers supported for cookie import
COOKIE_BROWSERS: list[str] = ["chrome", "firefox", "edge", "brave", "opera", "vivaldi"]
DEFAULT_COOKIE_BROWSER = "chrome"
