"""
Thumbnail loader — async thumbnail fetching with bounded LRU cache.
Uses QNetworkAccessManager for non-blocking HTTP requests.
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Optional

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

logger = logging.getLogger(__name__)

# Maximum number of thumbnails to keep in memory cache
MAX_CACHE_SIZE = 50


class ThumbnailLoader(QObject):
    """
    Asynchronously loads thumbnail images from URLs.
    Caches loaded thumbnails in a bounded LRU cache to prevent
    unbounded memory growth.
    """

    thumbnail_ready = Signal(str, QPixmap)   # (url, pixmap)
    thumbnail_error = Signal(str, str)       # (url, error_message)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        # Bounded LRU cache: OrderedDict lets us pop oldest entries
        self._cache: OrderedDict[str, QPixmap] = OrderedDict()
        self._pending: dict[str, QNetworkReply] = {}

    def load(self, url: str) -> None:
        """
        Load a thumbnail from the given URL.
        Emits thumbnail_ready if cached, otherwise starts async fetch.
        """
        if not url:
            return

        # Check cache first (move to end = recently used)
        if url in self._cache:
            self._cache.move_to_end(url)
            self.thumbnail_ready.emit(url, self._cache[url])
            return

        # Don't duplicate requests
        if url in self._pending:
            return

        # Start async request
        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(15000)  # 15 second timeout
        reply = self._manager.get(request)
        self._pending[url] = reply

        # Connect finished signal — use partial to avoid lambda closure leaks
        from functools import partial
        reply.finished.connect(partial(self._on_reply_finished, reply, url))

    def _on_reply_finished(self, reply: QNetworkReply, url: str) -> None:
        """Handle completed network reply."""
        # Remove from pending
        self._pending.pop(url, None)

        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_msg = reply.errorString()
            logger.warning("Thumbnail fetch failed for %s: %s", url, error_msg)
            self.thumbnail_error.emit(url, error_msg)
            reply.deleteLater()
            return

        # Read image data
        data = reply.readAll()
        reply.deleteLater()

        if data.isEmpty():
            self.thumbnail_error.emit(url, "Empty response")
            return

        # Convert to QPixmap — scale down large images to save memory
        image = QImage()
        if not image.loadFromData(data.data()):
            self.thumbnail_error.emit(url, "Failed to decode image data")
            return

        # Downscale to max 640px wide to save memory (thumbnails don't need full res)
        if image.width() > 640:
            image = image.scaledToWidth(640, mode=Qt.TransformationMode.SmoothTransformation)

        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            self.thumbnail_error.emit(url, "Decoded pixmap is null")
            return

        # Evict oldest entries if cache is full
        while len(self._cache) >= MAX_CACHE_SIZE:
            self._cache.popitem(last=False)

        # Cache and emit
        self._cache[url] = pixmap
        self.thumbnail_ready.emit(url, pixmap)
        logger.debug("Thumbnail loaded and cached (%d/%d): %s",
                      len(self._cache), MAX_CACHE_SIZE, url[:80])

    def get_cached(self, url: str) -> Optional[QPixmap]:
        """Get a cached thumbnail without triggering a load."""
        if url in self._cache:
            self._cache.move_to_end(url)
            return self._cache[url]
        return None

    def clear_cache(self) -> None:
        """Clear the in-memory thumbnail cache."""
        self._cache.clear()
        logger.debug("Thumbnail cache cleared")

    def cancel_all(self) -> None:
        """Cancel all pending thumbnail requests."""
        for reply in self._pending.values():
            reply.abort()
            reply.deleteLater()
        self._pending.clear()


# Need Qt import for transformation mode
from PySide6.QtCore import Qt
