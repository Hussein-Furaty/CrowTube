"""
Animated button — QPushButton with smooth hover color transitions.
"""

from __future__ import annotations

from PySide6.QtCore import QVariantAnimation, QAbstractAnimation, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QWidget


class AnimatedButton(QPushButton):
    """
    QPushButton with smooth background color animation on hover.
    """

    def __init__(
        self,
        text: str = "",
        normal_color: str = "#667eea",
        hover_color: str = "#7c94f5",
        pressed_color: str = "#4a62d4",
        text_color: str = "#ffffff",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._normal_color = QColor(normal_color)
        self._hover_color = QColor(hover_color)
        self._pressed_color = QColor(pressed_color)
        self._text_color = text_color
        self._current_color = self._normal_color

        # Setup animation
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.valueChanged.connect(self._on_color_changed)

        # Apply initial style
        self._update_style(self._normal_color)

    def _on_color_changed(self, color: QColor) -> None:
        """Called on each animation frame."""
        self._current_color = color
        self._update_style(color)

    def _update_style(self, color: QColor) -> None:
        """Update the button stylesheet with the given background color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                color: {self._text_color};
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 13px;
                min-height: 20px;
            }}
            QPushButton:disabled {{
                background-color: #2d2d3d;
                color: #555566;
            }}
        """)

    def enterEvent(self, event) -> None:
        """Mouse enters — animate to hover color."""
        self._animation.stop()
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(self._hover_color)
        self._animation.setDirection(QAbstractAnimation.Direction.Forward)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Mouse leaves — animate back to normal color."""
        self._animation.stop()
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(self._normal_color)
        self._animation.setDirection(QAbstractAnimation.Direction.Forward)
        self._animation.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """Mouse pressed — jump to pressed color."""
        self._animation.stop()
        self._current_color = self._pressed_color
        self._update_style(self._pressed_color)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Mouse released — animate to hover color."""
        self._animation.stop()
        self._animation.setStartValue(self._pressed_color)
        self._animation.setEndValue(self._hover_color)
        self._animation.start()
        super().mouseReleaseEvent(event)

    def set_colors(
        self,
        normal: str | None = None,
        hover: str | None = None,
        pressed: str | None = None,
    ) -> None:
        """Update the button's colors dynamically."""
        if normal:
            self._normal_color = QColor(normal)
        if hover:
            self._hover_color = QColor(hover)
        if pressed:
            self._pressed_color = QColor(pressed)
        self._update_style(self._normal_color)
