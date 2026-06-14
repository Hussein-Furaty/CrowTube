"""
Settings manager — persistent application settings using QSettings (INI format).
Singleton pattern ensures one instance across the application.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QSettings

from config.constants import (
    DEFAULT_AUDIO_FORMAT,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_CONCURRENT_DOWNLOADS,
    DEFAULT_COOKIE_BROWSER,
    DEFAULT_DOWNLOAD_DIR,
    DEFAULT_VIDEO_FORMAT,
    DEFAULT_VIDEO_QUALITY,
    SETTINGS_FILE_PATH,
    TOOLS_DIR,
)

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    Singleton wrapper around QSettings for persistent configuration.
    Stores settings in INI format for portability.
    """

    _instance: Optional[SettingsManager] = None

    # Default values for all settings
    DEFAULTS: dict[str, Any] = {
        # General
        "general/download_folder": DEFAULT_DOWNLOAD_DIR,
        "general/theme": "dark",
        "general/language": "en",

        # Downloads
        "downloads/default_video_quality": DEFAULT_VIDEO_QUALITY,
        "downloads/default_audio_quality": DEFAULT_AUDIO_QUALITY,
        "downloads/default_video_format": DEFAULT_VIDEO_FORMAT,
        "downloads/default_audio_format": DEFAULT_AUDIO_FORMAT,
        "downloads/concurrent_downloads": DEFAULT_CONCURRENT_DOWNLOADS,

        # Advanced
        "advanced/ffmpeg_path": "",
        "advanced/ytdlp_path": "",
        "advanced/proxy_url": "",
        "advanced/proxy_enabled": False,



        # Features
        "features/embed_subtitles": False,
        "features/embed_thumbnail": False,
        "features/write_metadata": True,
        "features/auto_merge": True,
    }

    def __init__(self) -> None:
        # Ensure the data directory exists
        settings_dir = Path(SETTINGS_FILE_PATH).parent
        settings_dir.mkdir(parents=True, exist_ok=True)

        self._settings = QSettings(SETTINGS_FILE_PATH, QSettings.Format.IniFormat)
        logger.info("Settings loaded from: %s", SETTINGS_FILE_PATH)

    @classmethod
    def instance(cls) -> SettingsManager:
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = SettingsManager()
        return cls._instance

    # ──────────────────────────────────────────
    # Generic get/set
    # ──────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value, falling back to default."""
        fallback = default if default is not None else self.DEFAULTS.get(key)
        value = self._settings.value(key, fallback)

        # QSettings returns strings for booleans — fix that
        if isinstance(fallback, bool):
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if isinstance(fallback, int) and not isinstance(fallback, bool):
            try:
                return int(value)
            except (ValueError, TypeError):
                return fallback

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self._settings.setValue(key, value)
        self._settings.sync()

    # ──────────────────────────────────────────
    # Convenience accessors
    # ──────────────────────────────────────────

    # General
    def get_download_folder(self) -> str:
        path = self.get("general/download_folder", DEFAULT_DOWNLOAD_DIR)
        # Ensure directory exists
        Path(path).mkdir(parents=True, exist_ok=True)
        return str(path)

    def set_download_folder(self, path: str) -> None:
        self.set("general/download_folder", path)

    def get_theme(self) -> str:
        return str(self.get("general/theme", "dark"))

    def set_theme(self, theme: str) -> None:
        self.set("general/theme", theme)

    # Downloads
    def get_default_video_quality(self) -> str:
        return str(self.get("downloads/default_video_quality", DEFAULT_VIDEO_QUALITY))

    def get_default_audio_quality(self) -> str:
        return str(self.get("downloads/default_audio_quality", DEFAULT_AUDIO_QUALITY))

    def get_default_video_format(self) -> str:
        return str(self.get("downloads/default_video_format", DEFAULT_VIDEO_FORMAT))

    def get_default_audio_format(self) -> str:
        return str(self.get("downloads/default_audio_format", DEFAULT_AUDIO_FORMAT))

    def get_concurrent_downloads(self) -> int:
        return int(self.get("downloads/concurrent_downloads", DEFAULT_CONCURRENT_DOWNLOADS))

    def set_concurrent_downloads(self, count: int) -> None:
        self.set("downloads/concurrent_downloads", max(1, min(count, 10)))

    # Advanced
    def get_ffmpeg_dir(self) -> str:
        """Return custom FFmpeg path, or default tools directory."""
        custom = self.get("advanced/ffmpeg_path", "")
        if custom and Path(custom).is_dir():
            return str(custom)
        return str(TOOLS_DIR)

    def get_proxy(self) -> Optional[str]:
        """Return proxy URL if enabled, else None."""
        enabled = self.get("advanced/proxy_enabled", False)
        if enabled:
            url = self.get("advanced/proxy_url", "")
            return str(url) if url else None
        return None



    # Features
    def get_embed_subtitles(self) -> bool:
        return bool(self.get("features/embed_subtitles", False))

    def get_embed_thumbnail(self) -> bool:
        return bool(self.get("features/embed_thumbnail", False))

    def get_write_metadata(self) -> bool:
        return bool(self.get("features/write_metadata", True))

    # ──────────────────────────────────────────
    # Reset / sync
    # ──────────────────────────────────────────

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self._settings.clear()
        for key, value in self.DEFAULTS.items():
            self._settings.setValue(key, value)
        self._settings.sync()
        logger.info("Settings reset to defaults")

    def sync(self) -> None:
        """Force writing settings to disk."""
        self._settings.sync()
