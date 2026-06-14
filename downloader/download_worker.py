"""
Download workers — QObject-based workers for background download and info extraction.
Uses the Worker Object pattern (moveToThread) for thread-safe operation.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from downloader.download_engine import DownloadEngine
from downloader.models import (
    DownloadItem,
    DownloadStatus,
    PlaylistInfo,
    VideoInfo,
)

logger = logging.getLogger(__name__)


class DownloadWorker(QObject):
    """
    Worker that runs a single download in a background QThread.
    Communicates progress back to the main thread via signals.
    """

    # Signals: (item_id, ...)
    progress_updated = Signal(str, float, float, int, int, int)
    # (item_id, percent, speed_bytes_per_sec, eta_seconds, downloaded_bytes, total_bytes)

    download_finished = Signal(str, str)   # (item_id, file_path)
    download_error = Signal(str, str)      # (item_id, error_message)
    status_changed = Signal(str, object)   # (item_id, DownloadStatus)

    def __init__(self, download_item: DownloadItem, engine: DownloadEngine) -> None:
        super().__init__()
        self._item = download_item
        self._engine = engine
        self._cancelled = False

    @Slot()
    def run(self) -> None:
        """Execute the download. Called when the thread starts."""
        item_id = self._item.id
        try:
            self.status_changed.emit(item_id, DownloadStatus.DOWNLOADING)
            file_path = self._engine.download(
                self._item,
                progress_hook=self._progress_hook,
                postprocessor_hook=self._postprocessor_hook,
            )
            if self._cancelled:
                self.status_changed.emit(item_id, DownloadStatus.CANCELLED)
                return
            self.status_changed.emit(item_id, DownloadStatus.COMPLETED)
            self.download_finished.emit(item_id, file_path)
        except _CancelledError:
            logger.info("Download cancelled: %s", self._item.title)
            self.status_changed.emit(item_id, DownloadStatus.CANCELLED)
        except Exception as e:
            error_msg = str(e)
            # Clean up ANSI codes from yt-dlp error messages
            error_msg = re.sub(r'\x1b\[[0-9;]*m', '', error_msg)
            logger.error("Download error for %s: %s", self._item.title, error_msg)
            self.status_changed.emit(item_id, DownloadStatus.FAILED)
            self.download_error.emit(item_id, error_msg)

    @Slot()
    def cancel(self) -> None:
        """Request cancellation of the running download."""
        self._cancelled = True
        logger.info("Cancel requested for: %s", self._item.title)

    def _progress_hook(self, d: dict) -> None:
        """yt-dlp progress hook — parses progress dict and emits signal."""
        if self._cancelled:
            raise _CancelledError("Download cancelled by user")

        status = d.get("status", "")

        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0) or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            speed = d.get("speed") or 0.0
            eta = d.get("eta") or 0

            if total > 0:
                percent = (downloaded / total) * 100.0
            else:
                percent = 0.0

            self.progress_updated.emit(
                self._item.id,
                percent,
                float(speed),
                int(eta),
                int(downloaded),
                int(total),
            )

        elif status == "finished":
            total = d.get("total_bytes") or d.get("downloaded_bytes", 0) or 0
            self.progress_updated.emit(
                self._item.id,
                100.0,
                0.0,
                0,
                int(total),
                int(total),
            )

    def _postprocessor_hook(self, d: dict) -> None:
        """yt-dlp postprocessor hook — emits MERGING status during post-processing."""
        status = d.get("status", "")
        if status == "started":
            pp_name = d.get("postprocessor", "")
            logger.debug("Post-processing started: %s", pp_name)
            self.status_changed.emit(self._item.id, DownloadStatus.MERGING)
        elif status == "finished":
            logger.debug("Post-processing finished: %s", d.get("filepath", ""))


class InfoExtractWorker(QObject):
    """
    Worker that extracts video/playlist info in a background QThread.
    """

    info_ready = Signal(object)  # VideoInfo or PlaylistInfo
    error = Signal(str)          # error message

    def __init__(self, url: str, engine: DownloadEngine) -> None:
        super().__init__()
        self._url = url
        self._engine = engine
        self._cancelled = False

    @Slot()
    def cancel(self) -> None:
        """Request cancellation of info extraction."""
        self._cancelled = True
        logger.info("Info extraction cancelled for: %s", self._url)

    @Slot()
    def run(self) -> None:
        """Extract info from the URL."""
        try:
            logger.info("Extracting info for: %s", self._url)
            info = self._engine.extract_info(self._url)
            if not self._cancelled:
                self.info_ready.emit(info)
        except Exception as e:
            if not self._cancelled:
                error_msg = str(e)
                error_msg = re.sub(r'\x1b\[[0-9;]*m', '', error_msg)
                logger.error("Info extraction failed for %s: %s", self._url, error_msg)
                self.error.emit(error_msg)


class _CancelledError(Exception):
    """Internal exception raised when a download is cancelled."""
    pass
