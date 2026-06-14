"""
Download queue manager — manages concurrent downloads with QThread workers.
Handles queuing, starting, pausing, cancelling, and cleanup.
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot

from downloader.download_engine import DownloadEngine
from downloader.download_worker import DownloadWorker
from downloader.models import (
    DownloadItem,
    DownloadProgress,
    DownloadStatus,
)

logger = logging.getLogger(__name__)

# Maximum completed items to keep in memory
MAX_COMPLETED_ITEMS = 100


class DownloadQueueManager(QObject):
    """
    Manages a queue of downloads with configurable concurrency.
    Starts downloads automatically as slots become available.
    """

    # Signals
    item_added = Signal(object)            # DownloadItem
    item_updated = Signal(str, object)     # (item_id, DownloadItem)
    item_removed = Signal(str)             # item_id
    item_finished = Signal(str, str)       # (item_id, file_path)
    item_failed = Signal(str, str)         # (item_id, error_message)
    active_count_changed = Signal(int)     # number of active downloads

    def __init__(self, engine: DownloadEngine, max_concurrent: int = 3) -> None:
        super().__init__()
        self._engine = engine
        self._max_concurrent = max_concurrent

        # Ordered dict preserves insertion order
        self._items: OrderedDict[str, DownloadItem] = OrderedDict()

        # Active threads/workers: item_id -> (QThread, DownloadWorker)
        self._active: dict[str, tuple[QThread, DownloadWorker]] = {}

        logger.info("DownloadQueueManager initialized (max_concurrent=%d)", max_concurrent)

    # ──────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────

    @property
    def items(self) -> OrderedDict[str, DownloadItem]:
        return self._items

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def pending_count(self) -> int:
        return sum(1 for item in self._items.values() if item.status == DownloadStatus.PENDING)

    @property
    def total_count(self) -> int:
        return len(self._items)

    # ──────────────────────────────────────────
    # Queue operations
    # ──────────────────────────────────────────

    def add_item(self, item: DownloadItem) -> None:
        """Add a download item to the queue."""
        item.status = DownloadStatus.PENDING
        self._items[item.id] = item
        self.item_added.emit(item)
        logger.info("Item added to queue: %s (%s)", item.title, item.id)
        self._start_next()

    def cancel_item(self, item_id: str) -> None:
        """Cancel an active or pending download."""
        if item_id not in self._items:
            return

        item = self._items[item_id]

        if item_id in self._active:
            # Cancel the active download
            thread, worker = self._active[item_id]
            worker.cancel()
            logger.info("Cancelling active download: %s", item.title)
        else:
            # Just mark as cancelled if pending
            item.status = DownloadStatus.CANCELLED
            self.item_updated.emit(item_id, item)
            logger.info("Cancelled pending download: %s", item.title)

    def remove_item(self, item_id: str) -> None:
        """Remove an item from the queue entirely."""
        if item_id in self._active:
            self.cancel_item(item_id)
            return  # Will be removed after cancellation completes

        if item_id in self._items:
            del self._items[item_id]
            self.item_removed.emit(item_id)
            logger.info("Removed item from queue: %s", item_id)

    def retry_item(self, item_id: str) -> None:
        """Retry a failed or cancelled download."""
        if item_id not in self._items:
            return

        item = self._items[item_id]
        if item.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            item.status = DownloadStatus.PENDING
            item.progress = DownloadProgress()
            item.error_message = ""
            self.item_updated.emit(item_id, item)
            logger.info("Retrying download: %s", item.title)
            self._start_next()

    def clear_completed(self) -> None:
        """Remove all completed, failed, and cancelled items."""
        remove_ids = [
            item_id for item_id, item in self._items.items()
            if item.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED)
        ]
        for item_id in remove_ids:
            del self._items[item_id]
            self.item_removed.emit(item_id)
        logger.info("Cleared %d completed/failed items", len(remove_ids))

    def _auto_evict_old_items(self) -> None:
        """Automatically remove oldest completed/failed items if over the limit."""
        terminal_statuses = (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED)
        terminal_ids = [
            item_id for item_id, item in self._items.items()
            if item.status in terminal_statuses
        ]
        while len(terminal_ids) > MAX_COMPLETED_ITEMS:
            oldest_id = terminal_ids.pop(0)
            if oldest_id in self._items:
                del self._items[oldest_id]
                self.item_removed.emit(oldest_id)
                logger.debug("Auto-evicted old queue item: %s", oldest_id)

    def cancel_all(self) -> None:
        """Cancel all active and pending downloads."""
        for item_id in list(self._active.keys()):
            self.cancel_item(item_id)
        for item in self._items.values():
            if item.status == DownloadStatus.PENDING:
                item.status = DownloadStatus.CANCELLED
                self.item_updated.emit(item.id, item)

    def set_max_concurrent(self, n: int) -> None:
        """Update the maximum number of concurrent downloads."""
        self._max_concurrent = max(1, min(n, 10))
        logger.info("Max concurrent downloads set to: %d", self._max_concurrent)
        self._start_next()

    # ──────────────────────────────────────────
    # Internal — thread management
    # ──────────────────────────────────────────

    def _start_next(self) -> None:
        """Start the next pending download if under the concurrency limit."""
        while len(self._active) < self._max_concurrent:
            # Find the next pending item
            next_item: Optional[DownloadItem] = None
            for item in self._items.values():
                if item.status == DownloadStatus.PENDING:
                    next_item = item
                    break

            if next_item is None:
                break

            self._start_download(next_item)

    def _start_download(self, item: DownloadItem) -> None:
        """Spawn a QThread + DownloadWorker for the given item."""
        thread = QThread()
        worker = DownloadWorker(item, self._engine)
        worker.moveToThread(thread)

        # Connect signals
        thread.started.connect(worker.run)

        worker.progress_updated.connect(self._on_progress_updated)
        worker.download_finished.connect(self._on_download_finished)
        worker.download_error.connect(self._on_download_error)
        worker.status_changed.connect(self._on_status_changed)

        # Cleanup connections — use a helper to avoid lambda closure leaks
        item_id = item.id  # capture the string, not the whole item

        def _on_status_quit(sid, status):
            if status == DownloadStatus.CANCELLED:
                thread.quit()

        worker.download_finished.connect(thread.quit)
        worker.download_error.connect(thread.quit)
        worker.status_changed.connect(_on_status_quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda id_=item_id: self._cleanup_thread(id_))

        # Track and start
        self._active[item.id] = (thread, worker)
        item.status = DownloadStatus.DOWNLOADING
        self.item_updated.emit(item.id, item)
        self.active_count_changed.emit(len(self._active))

        thread.start()
        logger.info("Started download thread for: %s (%s)", item.title, item.id)

    def _cleanup_thread(self, item_id: str) -> None:
        """Remove thread/worker reference after completion."""
        if item_id in self._active:
            del self._active[item_id]
            self.active_count_changed.emit(len(self._active))
            # Start next queued download
            self._start_next()

    # ──────────────────────────────────────────
    # Signal handlers
    # ──────────────────────────────────────────

    @Slot(str, float, float, int, int, int)
    def _on_progress_updated(
        self,
        item_id: str,
        percent: float,
        speed: float,
        eta: int,
        downloaded: int,
        total: int,
    ) -> None:
        """Update the item's progress data."""
        if item_id not in self._items:
            return

        item = self._items[item_id]
        item.progress = DownloadProgress(
            percent=percent,
            downloaded_bytes=downloaded,
            total_bytes=total,
            speed=speed,
            eta=eta,
        )
        self.item_updated.emit(item_id, item)

    @Slot(str, str)
    def _on_download_finished(self, item_id: str, file_path: str) -> None:
        """Handle successful download completion."""
        if item_id not in self._items:
            return

        item = self._items[item_id]
        item.status = DownloadStatus.COMPLETED
        item.file_path = file_path
        item.progress.percent = 100.0
        self.item_updated.emit(item_id, item)
        self.item_finished.emit(item_id, file_path)
        logger.info("Download completed: %s -> %s", item.title, file_path)
        # Auto-evict old completed items to prevent memory buildup
        self._auto_evict_old_items()

    @Slot(str, str)
    def _on_download_error(self, item_id: str, error_msg: str) -> None:
        """Handle download error."""
        if item_id not in self._items:
            return

        item = self._items[item_id]
        item.status = DownloadStatus.FAILED
        item.error_message = error_msg
        self.item_updated.emit(item_id, item)
        self.item_failed.emit(item_id, error_msg)
        logger.error("Download failed: %s — %s", item.title, error_msg)

    @Slot(str, object)
    def _on_status_changed(self, item_id: str, status: DownloadStatus) -> None:
        """Handle status change from worker."""
        if item_id not in self._items:
            return

        item = self._items[item_id]
        # Don't overwrite COMPLETED/FAILED set by other handlers
        if item.status not in (DownloadStatus.COMPLETED, DownloadStatus.FAILED):
            item.status = status
            self.item_updated.emit(item_id, item)
