"""
Shimmer loading widget — displays an animated shimmer effect as a placeholder
while content is being loaded (e.g. during URL analysis).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, Property
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QPen
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget


class ShimmerBar(QWidget):
    """A single shimmer bar with animated gradient sweep."""

    def __init__(self, height: int = 16, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(height)
        self._shimmer_pos = 0.0
        self._bar_radius = height // 2

        # Animation (not started until show_loading is called)
        self._animation = QPropertyAnimation(self, b"shimmerPos")
        self._animation.setDuration(1500)
        self._animation.setStartValue(-0.3)
        self._animation.setEndValue(1.3)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.setLoopCount(-1)  # infinite loop
        # Do NOT start here — parent controls start/stop via show_loading/hide_loading

    def get_shimmer_pos(self) -> float:
        return self._shimmer_pos

    def set_shimmer_pos(self, value: float) -> None:
        self._shimmer_pos = value
        self.update()

    shimmerPos = Property(float, get_shimmer_pos, set_shimmer_pos)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Base color
        base_color = QColor("#1e293b")
        shine_color = QColor("#334155")

        # Draw base
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(base_color)
        painter.drawRoundedRect(rect, self._bar_radius, self._bar_radius)

        # Draw shimmer gradient
        gradient = QLinearGradient(rect.left(), 0, rect.right(), 0)
        pos = self._shimmer_pos
        transparent = QColor(0, 0, 0, 0)

        gradient.setColorAt(min(1.0, max(0.0, pos - 0.15)), transparent)
        gradient.setColorAt(min(1.0, max(0.0, pos)), shine_color)
        gradient.setColorAt(min(1.0, max(0.0, pos + 0.15)), transparent)

        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, self._bar_radius, self._bar_radius)

        painter.end()

    def stop(self) -> None:
        self._animation.stop()

    def start(self) -> None:
        self._animation.start()


class ShimmerLoadingCard(QFrame):
    """
    A card that mimics the layout of a VideoInfoCard
    with shimmer placeholder bars while loading.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("videoInfoCard")
        self.setVisible(False)
        self._setup_ui()

    def _setup_ui(self) -> None:
        from PySide6.QtWidgets import QHBoxLayout

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        # Thumbnail placeholder
        self._thumb_shimmer = ShimmerBar(height=158)
        self._thumb_shimmer.setFixedWidth(280)
        layout.addWidget(self._thumb_shimmer)

        # Text placeholders
        text_layout = QVBoxLayout()
        text_layout.setSpacing(12)

        # Title bar (full width)
        self._title_bar = ShimmerBar(height=20)
        self._title_bar.setMinimumWidth(300)
        text_layout.addWidget(self._title_bar)

        # Channel bar (shorter)
        self._channel_bar = ShimmerBar(height=14)
        self._channel_bar.setMaximumWidth(200)
        text_layout.addWidget(self._channel_bar)

        # Stats bar (shorter)
        self._stats_bar = ShimmerBar(height=14)
        self._stats_bar.setMaximumWidth(250)
        text_layout.addWidget(self._stats_bar)

        text_layout.addStretch()
        layout.addLayout(text_layout, 1)

    def show_loading(self) -> None:
        """Show the shimmer card and start animations."""
        self.setVisible(True)
        for bar in [self._thumb_shimmer, self._title_bar, self._channel_bar, self._stats_bar]:
            bar.start()

    def hide_loading(self) -> None:
        """Hide and stop animations."""
        self.setVisible(False)
        for bar in [self._thumb_shimmer, self._title_bar, self._channel_bar, self._stats_bar]:
            bar.stop()
