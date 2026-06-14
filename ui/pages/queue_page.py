"""
Queue page — displays active and pending downloads.
"""

from __future__ import annotations

import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QPushButton,
)

from ui.widgets.download_item_widget import DownloadItemWidget
from downloader.models import DownloadItem, DownloadStatus

logger = logging.getLogger(__name__)


class QueuePage(QWidget):
    """
    Displays the current download queue with filter tabs and action buttons.
    """

    def __init__(self, queue_manager, thumbnail_loader, parent=None) -> None:
        super().__init__(parent)
        self._queue = queue_manager
        self._thumbnail_loader = thumbnail_loader
        self._widgets: dict[str, DownloadItemWidget] = {}
        self._current_filter = "All"
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Download Queue")
        title.setObjectName("sectionTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Toolbar
        self._clear_btn = QPushButton("Clear Completed")
        self._clear_btn.setObjectName("secondaryBtn")
        self._clear_btn.clicked.connect(self._queue.clear_completed)
        header_layout.addWidget(self._clear_btn)

        self._pause_all_btn = QPushButton("Pause All")
        self._pause_all_btn.setObjectName("secondaryBtn")
        header_layout.addWidget(self._pause_all_btn)

        self._cancel_all_btn = QPushButton("Cancel All")
        self._cancel_all_btn.setObjectName("dangerBtn")
        self._cancel_all_btn.clicked.connect(self._queue.cancel_all)
        header_layout.addWidget(self._cancel_all_btn)

        layout.addLayout(header_layout)

        # Filters
        filter_layout = QHBoxLayout()
        self._filter_btns = {}
        for f in ["All", "Active", "Pending", "Completed", "Failed"]:
            btn = QPushButton(f)
            btn.setObjectName("filterBtnActive" if f == "All" else "filterBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, text=f: self._set_filter(text))
            self._filter_btns[f] = btn
            filter_layout.addWidget(btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Scroll Area
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll_area.setStyleSheet("background: transparent;")

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(12)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Empty State
        self._empty_state = QLabel("No downloads yet. Paste a URL to get started!")
        self._empty_state.setObjectName("emptyState")
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setMinimumHeight(200)
        self._list_layout.addWidget(self._empty_state)

        self._scroll_area.setWidget(self._list_widget)
        layout.addWidget(self._scroll_area, 1)

    def _connect_signals(self) -> None:
        self._queue.item_added.connect(self._on_item_added)
        self._queue.item_updated.connect(self._on_item_updated)
        self._queue.item_removed.connect(self._on_item_removed)
        self._thumbnail_loader.thumbnail_ready.connect(self._on_thumbnail_ready)

    def _set_filter(self, filter_name: str) -> None:
        self._current_filter = filter_name
        for name, btn in self._filter_btns.items():
            btn.setObjectName("filterBtnActive" if name == filter_name else "filterBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        self._apply_filter()

    def _apply_filter(self) -> None:
        visible_count = 0
        for item_id, widget in self._widgets.items():
            item = widget._item
            visible = False
            
            if self._current_filter == "All":
                visible = True
            elif self._current_filter == "Active" and item.status in (DownloadStatus.DOWNLOADING, DownloadStatus.MERGING):
                visible = True
            elif self._current_filter == "Pending" and item.status in (DownloadStatus.PENDING, DownloadStatus.ANALYZING):
                visible = True
            elif self._current_filter == "Completed" and item.status == DownloadStatus.COMPLETED:
                visible = True
            elif self._current_filter == "Failed" and item.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
                visible = True
                
            widget.setVisible(visible)
            if visible:
                visible_count += 1
                
        self._empty_state.setVisible(len(self._widgets) == 0)

    def _on_item_added(self, item: DownloadItem) -> None:
        self._empty_state.setVisible(False)
        widget = DownloadItemWidget(item)
        
        # Connect actions
        widget.pause_clicked.connect(self._queue.cancel_item) # Native pause hard, map to cancel
        widget.cancel_clicked.connect(self._queue.cancel_item)
        widget.retry_clicked.connect(self._queue.retry_item)
        
        # Open folder logic 
        widget.open_folder_clicked.connect(self._open_folder)
        
        self._widgets[item.id] = widget
        self._list_layout.insertWidget(0, widget)  # Add at top
        
        if item.thumbnail_url:
            self._thumbnail_loader.load(item.thumbnail_url)
            
        self._apply_filter()

    def _on_item_updated(self, item_id: str, item: DownloadItem) -> None:
        if item_id in self._widgets:
            widget = self._widgets[item_id]
            widget.update_status(item.status, item.error_message)
            if item.status == DownloadStatus.DOWNLOADING:
                widget.update_progress(
                    item.progress.percent,
                    item.progress.speed_str,
                    item.progress.eta_str,
                    item.progress.downloaded_str,
                    item.progress.total_str
                )
            self._apply_filter()

    def _on_item_removed(self, item_id: str) -> None:
        if item_id in self._widgets:
            widget = self._widgets.pop(item_id)
            self._list_layout.removeWidget(widget)
            widget.deleteLater()
            self._apply_filter()

    def _on_thumbnail_ready(self, url: str, pixmap) -> None:
        for widget in self._widgets.values():
            if widget._item.thumbnail_url == url:
                widget.set_thumbnail(pixmap)

    def _open_folder(self, item_id: str) -> None:
        import os
        import subprocess
        if item_id in self._widgets:
            path = self._widgets[item_id]._item.file_path
            if os.path.exists(path):
                # Select file in explorer (Windows specific)
                subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
