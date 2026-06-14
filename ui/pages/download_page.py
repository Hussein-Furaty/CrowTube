"""
Download page — handles URL input, info extraction, and format selection.
Supports all platforms (YouTube, Instagram, Facebook, X, TikTok, etc.).
"""

from __future__ import annotations

import logging
from PySide6.QtCore import Qt, Signal, QThread, QUrl, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QMessageBox,
    QPushButton,
)

from ui.widgets.url_input_bar import UrlInputBar
from ui.widgets.video_info_card import VideoInfoCard
from ui.widgets.format_selector import FormatSelector
from ui.widgets.playlist_selector import PlaylistSelector
from ui.widgets.shimmer_widget import ShimmerLoadingCard

from downloader.download_worker import InfoExtractWorker
from downloader.models import DownloadItem, VideoInfo, PlaylistInfo

logger = logging.getLogger(__name__)


class DownloadPage(QWidget):
    """
    Main download page. Combines URL input, video info display,
    and format selection. Emits signals to add items to the queue.
    """

    add_to_queue = Signal(object)  # DownloadItem

    def __init__(self, download_engine, settings_manager, thumbnail_loader, parent=None) -> None:
        super().__init__(parent)
        self._engine = download_engine
        self._settings = settings_manager
        self._thumbnail_loader = thumbnail_loader
        self._current_info = None
        self._current_url = ""

        # Track active extraction thread to prevent leaks
        self._thread: QThread | None = None
        self._worker: InfoExtractWorker | None = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("New Download")
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        # URL Input
        self._url_input = UrlInputBar()
        layout.addWidget(self._url_input)

        # Scroll Area for dynamic content
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll_area.setStyleSheet("background: transparent;")

        scroll_widget = QWidget()
        self._scroll_layout = QVBoxLayout(scroll_widget)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_layout.setSpacing(20)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Shimmer loading placeholder (shown during analysis)
        self._shimmer_card = ShimmerLoadingCard()
        self._scroll_layout.addWidget(self._shimmer_card)

        # Components
        self._video_info = VideoInfoCard()
        self._scroll_layout.addWidget(self._video_info)

        self._playlist_selector = PlaylistSelector()
        self._scroll_layout.addWidget(self._playlist_selector)

        self._format_selector = FormatSelector()
        self._format_selector.setVisible(False)
        self._scroll_layout.addWidget(self._format_selector)

        self._scroll_area.setWidget(scroll_widget)
        layout.addWidget(self._scroll_area, 1)

        # Set defaults from settings
        self._format_selector.set_save_directory(self._settings.get_download_folder())
        self._format_selector.set_defaults(
            video_quality=self._settings.get_default_video_quality(),
            audio_quality=self._settings.get_default_audio_quality(),
            video_format=self._settings.get_default_video_format(),
            audio_format=self._settings.get_default_audio_format(),
        )

    def _connect_signals(self) -> None:
        self._url_input.analyze_requested.connect(self._on_analyze_requested)
        self._url_input.cancel_requested.connect(self._on_cancel_analysis)
        self._format_selector.download_requested.connect(self._on_download_requested)
        self._thumbnail_loader.thumbnail_ready.connect(self._on_thumbnail_ready)
        
        self._playlist_selector.download_all.connect(self._on_playlist_download_all)
        self._playlist_selector.download_selected.connect(self._on_playlist_download_selected)

    def _on_analyze_requested(self, url: str) -> None:
        """Handle URL analysis request."""
        self._current_url = url
        self._url_input.set_loading(True)
        self._video_info.clear()
        self._playlist_selector.clear()
        self._format_selector.setVisible(False)

        # Show shimmer loading
        self._shimmer_card.show_loading()

        # Start worker thread locally so it cleans itself up
        thread = QThread()
        worker = InfoExtractWorker(url, self._engine)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.info_ready.connect(self._on_info_ready)
        worker.error.connect(self._on_info_error)

        worker.info_ready.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Store a fire-and-forget reference temporarily if needed, 
        # but QObject tree manages it via deleteLater.
        # Actually we must keep a reference so Python GC doesn't destroy it.
        # Store in a list to handle multiple rapid clicks if any (though UI disables it).
        if not hasattr(self, '_active_threads'):
            self._active_threads = []
        if not hasattr(self, '_active_workers'):
            self._active_workers = []
            
        self._active_threads.append(thread)
        self._active_workers.append(worker)
        
        # Cleanup from our list when finished
        def cleanup(t=thread, w=worker):
            if t in self._active_threads:
                self._active_threads.remove(t)
            if w in self._active_workers:
                self._active_workers.remove(w)
                
        thread.finished.connect(cleanup)

        thread.start()

    def _on_info_ready(self, info: VideoInfo | PlaylistInfo) -> None:
        """Handle successful info extraction."""
        # If url doesn't match current url (meaning it was cancelled and a new one might be running or empty), ignore
        if not self._current_url:
            return
            
        self._url_input.set_loading(False)
        self._shimmer_card.hide_loading()
        self._current_info = info

        if isinstance(info, PlaylistInfo):
            self._playlist_selector.set_playlist(info)
            self._format_selector.setVisible(True)
            if info.thumbnail_url:
                self._thumbnail_loader.load(info.thumbnail_url)
        else:
            self._video_info.set_info(info)
            self._format_selector.setVisible(True)
            if info.thumbnail_url:
                self._thumbnail_loader.load(info.thumbnail_url)

    def _on_cancel_analysis(self) -> None:
        """Cancel the current analysis."""
        if hasattr(self, '_active_workers'):
            for worker in self._active_workers:
                worker.cancel()
        
        self._reset_ui()

    def _on_info_error(self, error_msg: str) -> None:
        """Handle info extraction error."""
        # Ignore if cancelled
        if not self._current_url:
            return
            
        self._url_input.set_loading(False)
        self._shimmer_card.hide_loading()

        # Delay the message box to allow the thread to cleanly exit
        QTimer.singleShot(0, lambda: self._show_error_dialog(error_msg))

    def _show_error_dialog(self, error_msg: str) -> None:
        """Show error dialog safely outside the signal handler."""
        QMessageBox.critical(self, "Analysis Failed", f"Could not analyze URL:\n\n{error_msg}")

    def _on_thumbnail_ready(self, url: str, pixmap) -> None:
        """Apply loaded thumbnail to the UI."""
        if isinstance(self._current_info, VideoInfo) and self._current_info.thumbnail_url == url:
            self._video_info.set_thumbnail(pixmap)

    def _on_download_requested(self, format_options) -> None:
        """Handle single video download request."""
        if not isinstance(self._current_info, VideoInfo):
            return

        item = DownloadItem(
            url=self._current_url,
            title=self._current_info.title,
            thumbnail_url=self._current_info.thumbnail_url,
            channel=self._current_info.channel,
            duration=self._current_info.duration,
            format_options=format_options,
            save_directory=self._format_selector.get_save_directory()
        )
        self.add_to_queue.emit(item)
        self._reset_ui()

    def _on_playlist_download_all(self) -> None:
        """Handle playlist download request (all videos)."""
        if not isinstance(self._current_info, PlaylistInfo):
            return
        self._enqueue_playlist_entries(self._current_info.entries)

    def _on_playlist_download_selected(self, selected_entries) -> None:
        """Handle playlist download request (selected videos)."""
        self._enqueue_playlist_entries(selected_entries)

    def _enqueue_playlist_entries(self, entries) -> None:
        """Add multiple playlist entries to the queue."""
        format_options = self._format_selector.get_format_options()
        save_dir = self._format_selector.get_save_directory()
        
        for entry in entries:
            item = DownloadItem(
                url=entry.url,
                title=entry.title,
                thumbnail_url=entry.thumbnail_url,
                channel=entry.channel,
                duration=entry.duration,
                format_options=format_options,
                save_directory=save_dir
            )
            self.add_to_queue.emit(item)
            
        self._reset_ui()

    def _reset_ui(self) -> None:
        """Reset the UI after adding to queue."""
        self._url_input.set_loading(False)
        self._url_input.clear()
        self._video_info.clear()
        self._playlist_selector.clear()
        self._format_selector.setVisible(False)
        self._shimmer_card.hide_loading()
        self._current_info = None
        self._current_url = ""
