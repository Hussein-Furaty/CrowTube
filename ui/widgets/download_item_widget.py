"""
Download item widget — displays progress and status for a single download.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from downloader.models import DownloadItem, DownloadStatus


class DownloadItemWidget(QFrame):
    """
    Widget representing a single download item in the queue.
    Shows thumbnail, title, format, progress bar, stats, and control buttons.
    """

    pause_clicked = Signal(str)
    resume_clicked = Signal(str)
    cancel_clicked = Signal(str)
    open_folder_clicked = Signal(str)
    retry_clicked = Signal(str)

    def __init__(self, download_item: DownloadItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("elevatedCard")
        self._item = download_item
        self._setup_ui()
        self._populate_initial_data()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ── Thumbnail ──
        self._thumbnail = QLabel()
        self._thumbnail.setFixedSize(60, 60)
        self._thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumbnail.setStyleSheet("""
            QLabel {
                background-color: #252547;
                border-radius: 6px;
            }
        """)
        self._thumbnail.setScaledContents(False)
        layout.addWidget(self._thumbnail)

        # ── Center Content ──
        center_layout = QVBoxLayout()
        center_layout.setSpacing(4)

        # Title and format row
        title_row = QHBoxLayout()
        self._title = QLabel()
        self._title.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        title_row.addWidget(self._title, 1)

        self._format_info = QLabel()
        self._format_info.setStyleSheet("font-size: 12px; color: #8888aa;")
        title_row.addWidget(self._format_info)
        center_layout.addLayout(title_row)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("thinProgress")
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        center_layout.addWidget(self._progress_bar)

        # Stats row
        stats_row = QHBoxLayout()
        self._status = QLabel()
        self._status.setStyleSheet("font-size: 12px; font-weight: 600;")
        stats_row.addWidget(self._status)

        self._speed = QLabel()
        self._speed.setStyleSheet("font-size: 12px; color: #8888aa;")
        stats_row.addWidget(self._speed)

        self._eta = QLabel()
        self._eta.setStyleSheet("font-size: 12px; color: #8888aa;")
        stats_row.addWidget(self._eta)

        stats_row.addStretch()

        self._size_info = QLabel()
        self._size_info.setStyleSheet("font-size: 12px; color: #8888aa;")
        stats_row.addWidget(self._size_info)

        center_layout.addLayout(stats_row)
        layout.addLayout(center_layout, 1)

        # ── Actions Right ──
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        # Top action row (Pause / Retry / Folder)
        self._action_btn1 = QPushButton()
        self._action_btn1.setObjectName("smallBtn")
        self._action_btn1.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(self._action_btn1)

        # Bottom action row (Cancel)
        self._action_btn2 = QPushButton("Cancel")
        self._action_btn2.setObjectName("smallBtn")
        self._action_btn2.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_btn2.setStyleSheet("color: #ef5350;")
        self._action_btn2.setToolTip("Cancel")
        actions_layout.addWidget(self._action_btn2)

        layout.addLayout(actions_layout)

        # Connect action buttons
        self._action_btn1.clicked.connect(self._on_action_btn1_clicked)
        self._action_btn2.clicked.connect(lambda: self.cancel_clicked.emit(self._item.id))

    def _populate_initial_data(self) -> None:
        title = self._item.title
        # Elide long titles
        metrics = self._title.fontMetrics()
        elided_title = metrics.elidedText(title, Qt.TextElideMode.ElideRight, 400)
        self._title.setText(elided_title)
        self._title.setToolTip(title)

        self._format_info.setText(self._item.format_display)
        self.update_status(self._item.status)

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                60, 60,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._thumbnail.setPixmap(scaled)

    def update_progress(self, percent: float, speed_str: str, eta_str: str, downloaded_str: str, total_str: str) -> None:
        self._progress_bar.setValue(int(percent))
        self._speed.setText(speed_str)
        self._eta.setText(f"ETA: {eta_str}")
        self._size_info.setText(f"{downloaded_str} / {total_str}")

    def update_status(self, status: DownloadStatus, error_msg: str = "") -> None:
        self._item.status = status
        self._status.setText(status.value)

        # Default hidden
        self._speed.setVisible(False)
        self._eta.setVisible(False)

        # Style based on status
        if status == DownloadStatus.DOWNLOADING:
            self._status.setStyleSheet("font-size: 12px; font-weight: 600; color: #4fc3f7;")
            self._speed.setVisible(True)
            self._eta.setVisible(True)
            self._action_btn1.setText("Pause")
            self._action_btn1.setToolTip("Pause (Not supported natively, will cancel)")
            self._action_btn1.setVisible(True)
            self._action_btn2.setVisible(True)

        elif status == DownloadStatus.COMPLETED:
            self._status.setStyleSheet("font-size: 12px; font-weight: 600; color: #4caf50;")
            self._progress_bar.setValue(100)
            self._action_btn1.setText("Folder")
            self._action_btn1.setToolTip("Open Folder")
            self._action_btn1.setVisible(True)
            self._action_btn2.setVisible(False)  # hide cancel

        elif status == DownloadStatus.FAILED:
            self._status.setStyleSheet("font-size: 12px; font-weight: 600; color: #ef5350;")
            if error_msg:
                self._status.setToolTip(error_msg)
            self._action_btn1.setText("Retry")
            self._action_btn1.setToolTip("Retry")
            self._action_btn1.setVisible(True)
            self._action_btn2.setVisible(True)

        elif status == DownloadStatus.CANCELLED:
            self._status.setStyleSheet("font-size: 12px; font-weight: 600; color: #ffb74d;")
            self._action_btn1.setText("Retry")
            self._action_btn1.setToolTip("Retry")
            self._action_btn1.setVisible(True)
            self._action_btn2.setVisible(False)

        elif status == DownloadStatus.MERGING:
            self._status.setStyleSheet("font-size: 12px; font-weight: 600; color: #b388ff;")
            self._action_btn1.setVisible(False)
            self._action_btn2.setVisible(False)

        elif status == DownloadStatus.PENDING:
            self._status.setStyleSheet("font-size: 12px; font-weight: 600; color: #8888aa;")
            self._action_btn1.setVisible(False)
            self._action_btn2.setVisible(True)

    def _on_action_btn1_clicked(self) -> None:
        status = self._item.status
        if status == DownloadStatus.DOWNLOADING:
            self.pause_clicked.emit(self._item.id)
        elif status == DownloadStatus.COMPLETED:
            self.open_folder_clicked.emit(self._item.id)
        elif status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            self.retry_clicked.emit(self._item.id)
