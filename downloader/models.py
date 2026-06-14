"""
Data models for the download engine, queue, and UI.
Uses dataclasses for clean, typed data structures.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DownloadStatus(Enum):
    """Status of a download item in the queue."""
    PENDING = "Pending"
    ANALYZING = "Analyzing"
    DOWNLOADING = "Downloading"
    PAUSED = "Paused"
    MERGING = "Merging"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class DownloadMode(Enum):
    """Whether the user wants video or audio only."""
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class FormatOptions:
    """User-selected format and quality options for a download."""
    mode: DownloadMode = DownloadMode.VIDEO

    # Video options
    video_format: str = "MP4"
    video_quality: str = "1080p"

    # Audio options
    audio_format: str = "MP3"
    audio_quality: str = "192 kbps"

    # Feature flags
    download_subtitles: bool = False
    embed_subtitles: bool = False
    embed_thumbnail: bool = False
    write_metadata: bool = True
    download_thumbnail: bool = False
    subtitle_languages: list[str] = field(default_factory=lambda: ["en"])


@dataclass
class VideoFormat:
    """A single available format from yt-dlp extraction."""
    format_id: str = ""
    extension: str = ""
    resolution: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    fps: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    filesize_approx: Optional[int] = None
    tbr: Optional[float] = None  # total bitrate in kbps
    note: str = ""

    @property
    def is_video_only(self) -> bool:
        return self.vcodec and self.vcodec != "none" and (not self.acodec or self.acodec == "none")

    @property
    def is_audio_only(self) -> bool:
        return self.acodec and self.acodec != "none" and (not self.vcodec or self.vcodec == "none")

    @property
    def size_str(self) -> str:
        size = self.filesize or self.filesize_approx
        if not size:
            return "Unknown"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


@dataclass
class VideoInfo:
    """Metadata extracted from a single video."""
    video_id: str = ""
    title: str = ""
    thumbnail_url: str = ""
    duration: int = 0  # seconds
    channel: str = ""
    channel_url: str = ""
    upload_date: str = ""
    view_count: int = 0
    description: str = ""
    webpage_url: str = ""
    formats: list[VideoFormat] = field(default_factory=list)
    subtitles: dict[str, list] = field(default_factory=dict)
    automatic_captions: dict[str, list] = field(default_factory=dict)
    is_playlist: bool = False

    @property
    def duration_str(self) -> str:
        """Format duration as HH:MM:SS or MM:SS."""
        if self.duration <= 0:
            return "00:00"
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def view_count_str(self) -> str:
        """Format view count with K/M suffixes."""
        if self.view_count <= 0:
            return "0"
        if self.view_count >= 1_000_000_000:
            return f"{self.view_count / 1_000_000_000:.1f}B"
        if self.view_count >= 1_000_000:
            return f"{self.view_count / 1_000_000:.1f}M"
        if self.view_count >= 1_000:
            return f"{self.view_count / 1_000:.1f}K"
        return str(self.view_count)

    @property
    def available_subtitle_languages(self) -> list[str]:
        return list(self.subtitles.keys())

    @property
    def available_auto_caption_languages(self) -> list[str]:
        return list(self.automatic_captions.keys())


@dataclass
class PlaylistEntry:
    """A single entry in a playlist (flat extraction)."""
    video_id: str = ""
    title: str = ""
    duration: int = 0
    url: str = ""
    thumbnail_url: str = ""
    channel: str = ""
    index: int = 0
    selected: bool = True  # for UI checkbox state

    @property
    def duration_str(self) -> str:
        if self.duration <= 0:
            return "00:00"
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


@dataclass
class PlaylistInfo:
    """Metadata for a YouTube playlist."""
    playlist_id: str = ""
    title: str = ""
    channel: str = ""
    description: str = ""
    thumbnail_url: str = ""
    video_count: int = 0
    entries: list[PlaylistEntry] = field(default_factory=list)
    webpage_url: str = ""

    @property
    def total_duration(self) -> int:
        return sum(e.duration for e in self.entries if e.duration > 0)

    @property
    def total_duration_str(self) -> str:
        total = self.total_duration
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def selected_entries(self) -> list[PlaylistEntry]:
        return [e for e in self.entries if e.selected]

    @property
    def selected_count(self) -> int:
        return len(self.selected_entries)


@dataclass
class DownloadProgress:
    """Real-time progress data for an active download."""
    percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0  # bytes/sec
    eta: int = 0  # seconds

    @property
    def speed_str(self) -> str:
        if self.speed <= 0:
            return "—"
        if self.speed >= 1024 * 1024:
            return f"{self.speed / (1024 * 1024):.1f} MB/s"
        if self.speed >= 1024:
            return f"{self.speed / 1024:.1f} KB/s"
        return f"{self.speed:.0f} B/s"

    @property
    def eta_str(self) -> str:
        if self.eta <= 0:
            return "—"
        hours, remainder = divmod(int(self.eta), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    @property
    def downloaded_str(self) -> str:
        return self._format_bytes(self.downloaded_bytes)

    @property
    def total_str(self) -> str:
        return self._format_bytes(self.total_bytes)

    @staticmethod
    def _format_bytes(b: int) -> str:
        if b <= 0:
            return "0 B"
        if b >= 1024 * 1024 * 1024:
            return f"{b / (1024 * 1024 * 1024):.2f} GB"
        if b >= 1024 * 1024:
            return f"{b / (1024 * 1024):.1f} MB"
        if b >= 1024:
            return f"{b / 1024:.1f} KB"
        return f"{b} B"


@dataclass
class DownloadItem:
    """A single download task in the queue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    url: str = ""
    title: str = ""
    thumbnail_url: str = ""
    channel: str = ""
    duration: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    progress: DownloadProgress = field(default_factory=DownloadProgress)
    format_options: FormatOptions = field(default_factory=FormatOptions)
    output_path: str = ""
    save_directory: str = ""
    error_message: str = ""
    file_path: str = ""  # final file path after download

    @property
    def duration_str(self) -> str:
        if self.duration <= 0:
            return "00:00"
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def status_display(self) -> str:
        return self.status.value

    @property
    def format_display(self) -> str:
        if self.format_options.mode == DownloadMode.VIDEO:
            return f"{self.format_options.video_format} • {self.format_options.video_quality}"
        return f"{self.format_options.audio_format} • {self.format_options.audio_quality}"


@dataclass
class HistoryEntry:
    """A record in the download history database."""
    id: int = 0
    filename: str = ""
    url: str = ""
    date: str = ""
    download_type: str = ""  # "video" or "audio"
    save_path: str = ""
    file_size: int = 0
    status: str = "completed"

    @property
    def file_size_str(self) -> str:
        return DownloadProgress._format_bytes(self.file_size)
