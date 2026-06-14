"""
Download engine — wraps yt-dlp for metadata extraction and downloading.
Handles format selection, postprocessors, and FFmpeg integration.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse

import yt_dlp

from config.constants import (
    AUDIO_FORMAT_MAP,
    AUDIO_QUALITY_MAP,
    DEFAULT_FRAGMENT_RETRIES,
    DEFAULT_RETRIES,
    DEFAULT_SOCKET_TIMEOUT,
    SUPPORTED_PLATFORMS,
    TOOLS_DIR,
    VIDEO_FORMAT_MAP,
    VIDEO_QUALITY_MAP,
)
from downloader.models import (
    DownloadItem,
    DownloadMode,
    FormatOptions,
    PlaylistEntry,
    PlaylistInfo,
    VideoFormat,
    VideoInfo,
)

logger = logging.getLogger(__name__)


class DownloadEngine:
    """Core wrapper around yt-dlp for extraction and download operations."""

    def __init__(
        self,
        ffmpeg_dir: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> None:
        self._ffmpeg_dir = ffmpeg_dir or str(TOOLS_DIR)
        self._proxy = proxy
        logger.info("DownloadEngine initialized (ffmpeg=%s, proxy=%s)",
                    self._ffmpeg_dir, self._proxy)

    # ──────────────────────────────────────────
    # FFmpeg path resolution
    # ──────────────────────────────────────────

    def get_ffmpeg_dir(self) -> str:
        """Return the directory containing ffmpeg/ffprobe binaries."""
        if self._ffmpeg_dir and os.path.isdir(self._ffmpeg_dir):
            return self._ffmpeg_dir
        return str(TOOLS_DIR)

    def set_ffmpeg_dir(self, path: str) -> None:
        self._ffmpeg_dir = path

    def set_proxy(self, proxy: Optional[str]) -> None:
        self._proxy = proxy



    # ──────────────────────────────────────────
    # Base options
    # ──────────────────────────────────────────

    def _base_opts(self, url: str = "") -> dict[str, Any]:
        """Base yt-dlp options shared by all operations."""
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "continuedl": True,
            "retries": DEFAULT_RETRIES,
            "fragment_retries": DEFAULT_FRAGMENT_RETRIES,
            "socket_timeout": DEFAULT_SOCKET_TIMEOUT,
            "ignoreerrors": False,
            "noprogress": True,
        }
        ffmpeg_dir = self.get_ffmpeg_dir()
        if ffmpeg_dir and os.path.isdir(ffmpeg_dir):
            opts["ffmpeg_location"] = ffmpeg_dir
        if self._proxy:
            opts["proxy"] = self._proxy



        # Apply platform-specific options
        if url:
            platform = self.detect_platform(url)
            if platform:
                self._apply_platform_opts(opts, platform)

        return opts

    # ──────────────────────────────────────────
    # Metadata extraction
    # ──────────────────────────────────────────

    def extract_info(self, url: str) -> VideoInfo | PlaylistInfo:
        """
        Extract metadata from a URL without downloading.
        Returns VideoInfo for single videos, PlaylistInfo for playlists.
        """
        opts = self._base_opts(url)
        opts["noplaylist"] = False  # allow playlist detection

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                raw = ydl.extract_info(url, download=False)
                if raw is None:
                    raise ValueError("No info returned for URL")

                # Check if playlist
                if "entries" in raw and raw.get("_type") in ("playlist", "multi_video"):
                    return self._parse_playlist_info(raw)
                elif "entries" in raw:
                    # Sometimes a single-video playlist wrapper
                    entries = list(raw.get("entries", []))
                    if len(entries) == 1 and entries[0]:
                        return self._parse_video_info(entries[0])
                    return self._parse_playlist_info(raw)
                else:
                    return self._parse_video_info(raw)
        except Exception as e:
            logger.error("Failed to extract info from %s: %s", url, e)
            # Enhance error message with platform-specific advice
            enhanced = self._enhance_error_message(url, str(e))
            raise RuntimeError(enhanced) from e

    def extract_playlist_flat(self, url: str) -> PlaylistInfo:
        """Fast playlist scan using flat extraction (metadata only, no format resolution)."""
        opts = self._base_opts(url)
        opts["extract_flat"] = True
        opts["noplaylist"] = False

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                raw = ydl.extract_info(url, download=False)
                if raw is None:
                    raise ValueError("No playlist info returned")
                return self._parse_playlist_info(raw)
        except Exception as e:
            logger.error("Failed to extract playlist from %s: %s", url, e)
            enhanced = self._enhance_error_message(url, str(e))
            raise RuntimeError(enhanced) from e

    # ──────────────────────────────────────────
    # Parsing helpers
    # ──────────────────────────────────────────

    def _parse_video_info(self, raw: dict) -> VideoInfo:
        """Parse raw yt-dlp info dict into VideoInfo model."""
        formats = []
        for f in raw.get("formats", []):
            formats.append(VideoFormat(
                format_id=f.get("format_id", ""),
                extension=f.get("ext", ""),
                resolution=f.get("resolution"),
                height=f.get("height"),
                width=f.get("width"),
                fps=f.get("fps"),
                vcodec=f.get("vcodec"),
                acodec=f.get("acodec"),
                filesize=f.get("filesize"),
                filesize_approx=f.get("filesize_approx"),
                tbr=f.get("tbr"),
                note=f.get("format_note", ""),
            ))

        return VideoInfo(
            video_id=raw.get("id", ""),
            title=raw.get("title", "Unknown"),
            thumbnail_url=raw.get("thumbnail", ""),
            duration=raw.get("duration") or 0,
            channel=raw.get("channel") or raw.get("uploader", "Unknown"),
            channel_url=raw.get("channel_url", ""),
            upload_date=raw.get("upload_date", ""),
            view_count=raw.get("view_count") or 0,
            description=raw.get("description", ""),
            webpage_url=raw.get("webpage_url", ""),
            formats=formats,
            subtitles=raw.get("subtitles", {}),
            automatic_captions=raw.get("automatic_captions", {}),
            is_playlist=False,
        )

    def _parse_playlist_info(self, raw: dict) -> PlaylistInfo:
        """Parse raw yt-dlp playlist dict into PlaylistInfo model."""
        entries: list[PlaylistEntry] = []
        for idx, entry in enumerate(raw.get("entries", []), start=1):
            if entry is None:
                continue
            entries.append(PlaylistEntry(
                video_id=entry.get("id", ""),
                title=entry.get("title", f"Video {idx}"),
                duration=entry.get("duration") or 0,
                url=entry.get("url") or entry.get("webpage_url", ""),
                thumbnail_url=entry.get("thumbnail", ""),
                channel=entry.get("channel") or entry.get("uploader", ""),
                index=idx,
                selected=True,
            ))

        return PlaylistInfo(
            playlist_id=raw.get("id", ""),
            title=raw.get("title", "Unknown Playlist"),
            channel=raw.get("channel") or raw.get("uploader", ""),
            description=raw.get("description", ""),
            thumbnail_url=raw.get("thumbnail", ""),
            video_count=raw.get("playlist_count") or len(entries),
            entries=entries,
            webpage_url=raw.get("webpage_url", ""),
        )

    # ──────────────────────────────────────────
    # Download options builder
    # ──────────────────────────────────────────

    def build_ydl_opts(
        self,
        item: DownloadItem,
        progress_hook: Optional[Callable] = None,
        postprocessor_hook: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """Build yt-dlp options dict from a DownloadItem's format options."""
        opts = self._base_opts(item.url)
        fmt = item.format_options
        save_dir = item.save_directory or os.path.expanduser("~/Downloads")

        # Output template
        opts["outtmpl"] = os.path.join(save_dir, "%(title)s.%(ext)s")
        opts["noplaylist"] = True

        if fmt.mode == DownloadMode.VIDEO:
            self._apply_video_opts(opts, fmt)
        else:
            self._apply_audio_opts(opts, fmt)

        # Postprocessors list
        postprocessors: list[dict] = opts.get("postprocessors", [])

        # Embed subtitles
        if fmt.download_subtitles:
            opts["writesubtitles"] = True
            opts["subtitleslangs"] = fmt.subtitle_languages or ["en"]
            opts["subtitlesformat"] = "srt/best"
        if fmt.embed_subtitles and fmt.mode == DownloadMode.VIDEO:
            opts["writesubtitles"] = True
            opts["subtitleslangs"] = fmt.subtitle_languages or ["en"]
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})

        # Embed thumbnail
        if fmt.embed_thumbnail:
            opts["writethumbnail"] = True
            postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

        # Download thumbnail separately
        if fmt.download_thumbnail:
            opts["writethumbnail"] = True

        # Write metadata
        if fmt.write_metadata:
            postprocessors.append({
                "key": "FFmpegMetadata",
                "add_metadata": True,
                "add_chapters": True,
            })

        opts["postprocessors"] = postprocessors

        # Hooks
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]
        if postprocessor_hook:
            opts["postprocessor_hooks"] = [postprocessor_hook]

        return opts

    def _apply_video_opts(self, opts: dict, fmt: FormatOptions) -> None:
        """Apply video-specific download options."""
        base_format_str = VIDEO_QUALITY_MAP.get(fmt.video_quality, "bv*+ba/b")
        merge_format = VIDEO_FORMAT_MAP.get(fmt.video_format, "mp4")

        # Ensure compatibility for MP4 containers on Windows by preferring m4a (AAC) audio
        if merge_format == "mp4":
            # Attempt to get m4a audio first, fallback to original format string if unavailable
            prefer_m4a_str = base_format_str.replace("+ba", "+ba[ext=m4a]")
            opts["format"] = f"{prefer_m4a_str}/{base_format_str}"
        else:
            opts["format"] = base_format_str

        opts["merge_output_format"] = merge_format

    def _apply_audio_opts(self, opts: dict, fmt: FormatOptions) -> None:
        """Apply audio-only download options."""
        opts["format"] = "bestaudio/best"

        codec = AUDIO_FORMAT_MAP.get(fmt.audio_format, "mp3")
        quality = AUDIO_QUALITY_MAP.get(fmt.audio_quality, "192")

        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": codec,
            "preferredquality": quality,
        }]

    # ──────────────────────────────────────────
    # Download execution
    # ──────────────────────────────────────────

    def download(
        self,
        item: DownloadItem,
        progress_hook: Optional[Callable] = None,
        postprocessor_hook: Optional[Callable] = None,
    ) -> str:
        """
        Execute download for a DownloadItem.
        Returns the final file path.
        """
        opts = self.build_ydl_opts(item, progress_hook, postprocessor_hook)
        logger.info("Starting download: %s (format: %s)", item.title, item.format_options.mode.value)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(item.url, download=True)
                if info is None:
                    raise RuntimeError("Download returned no info")

                # Determine the final file path
                file_path = info.get("requested_downloads", [{}])[0].get("filepath", "")
                if not file_path:
                    # Fallback: construct from template
                    file_path = ydl.prepare_filename(info)

                logger.info("Download completed: %s -> %s", item.title, file_path)
                return file_path
        except Exception as e:
            logger.error("Download failed for %s: %s", item.title, e)
            enhanced = self._enhance_error_message(item.url, str(e))
            raise RuntimeError(enhanced) from e

    # ──────────────────────────────────────────
    # Platform detection & helpers
    # ──────────────────────────────────────────

    @staticmethod
    def detect_platform(url: str) -> str | None:
        """
        Detect which platform a URL belongs to.
        Returns the platform key (e.g. 'youtube', 'instagram') or None.
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Strip www. for matching
            clean_domain = domain.replace("www.", "")

            for platform_key, platform_info in SUPPORTED_PLATFORMS.items():
                for d in platform_info["domains"]:
                    check = d.replace("www.", "")
                    if clean_domain == check or clean_domain.endswith("." + check):
                        return platform_key
        except Exception:
            pass
        return None

    @staticmethod
    def _apply_platform_opts(opts: dict, platform: str) -> None:
        """Apply platform-specific yt-dlp options."""
        if platform == "instagram":
            # Instagram-specific settings
            opts.setdefault("http_headers", {})
            opts["http_headers"].update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.instagram.com/",
            })
        elif platform == "twitter":
            opts.setdefault("http_headers", {})
            opts["http_headers"].update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            })
        elif platform == "facebook":
            opts.setdefault("http_headers", {})
            opts["http_headers"].update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            })

    def _enhance_error_message(self, url: str, original_error: str) -> str:
        """Clean ANSI codes from error messages."""
        return re.sub(r'\x1b\[[0-9;]*m', '', original_error)
