"""
Video info card — displays video metadata (thumbnail, title, channel, duration).
Supports all platforms with platform-specific styling.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from downloader.models import VideoInfo
from downloader.download_engine import DownloadEngine
from config.constants import SUPPORTED_PLATFORMS


class VideoInfoCard(QFrame):
    """
    Displays video metadata in a card layout:
    thumbnail on the left, title/channel/duration on the right.
    Shows platform badge for non-YouTube sources.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("videoInfoCard")
        self.setVisible(False)
        self._show_animation = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        # Thumbnail
        self._thumbnail_label = QLabel()
        self._thumbnail_label.setFixedSize(280, 158)
        self._thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)
        self._thumbnail_label.setScaledContents(False)
        layout.addWidget(self._thumbnail_label)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # Platform + Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self._platform_label = QLabel()
        self._platform_label.setVisible(False)
        self._platform_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._platform_label.setFixedHeight(24)
        title_row.addWidget(self._platform_label)

        title_row.addStretch()
        info_layout.addLayout(title_row)

        # Title
        self._title_label = QLabel()
        self._title_label.setObjectName("titleLabel")
        self._title_label.setWordWrap(True)
        self._title_label.setMaximumWidth(500)
        self._title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        info_layout.addWidget(self._title_label)

        # Channel
        self._channel_label = QLabel()
        self._channel_label.setStyleSheet("font-size: 13px; color: #94a3b8;")
        info_layout.addWidget(self._channel_label)

        # Duration + Views row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self._duration_label = QLabel()
        self._duration_label.setStyleSheet("font-size: 13px; color: #818cf8; font-weight: 600;")
        stats_layout.addWidget(self._duration_label)

        self._views_label = QLabel()
        self._views_label.setStyleSheet("font-size: 13px; color: #94a3b8;")
        stats_layout.addWidget(self._views_label)

        stats_layout.addStretch()
        info_layout.addLayout(stats_layout)

        info_layout.addStretch()
        layout.addLayout(info_layout, 1)

    def set_info(self, info: VideoInfo) -> None:
        """Populate the card with video metadata."""
        self._title_label.setText(info.title)
        self._channel_label.setText(info.channel)
        self._duration_label.setText(info.duration_str)
        
        if info.view_count > 0:
            self._views_label.setText(f"{info.view_count_str} views")
            self._views_label.setVisible(True)
        else:
            self._views_label.setVisible(False)

        # Detect platform from URL and show badge
        if info.webpage_url:
            platform = DownloadEngine.detect_platform(info.webpage_url)
            if platform:
                pinfo = SUPPORTED_PLATFORMS.get(platform, {})
                icon = pinfo.get("icon", "")
                name = pinfo.get("name", "")
                color = pinfo.get("color", "#818cf8")
                bg = pinfo.get("bg_color", "rgba(99, 102, 241, 0.15)")
                self._platform_label.setText(f" {icon} {name} ")
                self._platform_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {bg};
                        color: {color};
                        border: 1px solid {color};
                        border-radius: 10px;
                        padding: 2px 10px;
                        font-size: 11px;
                        font-weight: 700;
                    }}
                """)
                self._platform_label.setVisible(True)
            else:
                self._platform_label.setVisible(False)
        else:
            self._platform_label.setVisible(False)

        self.show_with_animation()

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        """Set the thumbnail image, scaled to fit."""
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                280, 158,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._thumbnail_label.setPixmap(scaled)

    def show_with_animation(self) -> None:
        """Show the card with a slide-in animation."""
        self.setVisible(True)
        self.setMaximumHeight(0)

        animation = QPropertyAnimation(self, b"maximumHeight")
        animation.setDuration(300)
        animation.setStartValue(0)
        animation.setEndValue(220)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

        # Store reference to prevent garbage collection
        self._show_animation = animation

    def clear(self) -> None:
        """Reset and hide the card."""
        self._title_label.clear()
        self._channel_label.clear()
        self._duration_label.clear()
        self._views_label.clear()
        self._thumbnail_label.clear()
        self._platform_label.clear()
        self._platform_label.setVisible(False)
        self.setVisible(False)
        # Release animation reference
        self._show_animation = None
