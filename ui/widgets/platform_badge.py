"""
Platform badge — shows detected platform name + icon as a styled label.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout, QFrame

from config.constants import SUPPORTED_PLATFORMS
from downloader.download_engine import DownloadEngine


class PlatformBadge(QFrame):
    """
    A badge widget that displays the detected platform name and icon.
    Animates in when a platform is detected, hides when cleared.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("platformBadge")
        self.setVisible(False)
        self._current_platform = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 12, 4)
        layout.setSpacing(6)

        self._icon_label = QLabel()
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        layout.addWidget(self._icon_label)

        self._name_label = QLabel()
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet("font-size: 12px; font-weight: 700; background: transparent; border: none;")
        layout.addWidget(self._name_label)

    def detect_and_show(self, url: str) -> str | None:
        """
        Detect the platform from the URL and update the badge.
        Returns the platform key or None.
        """
        platform = DownloadEngine.detect_platform(url)
        if platform:
            self._show_platform(platform)
        else:
            self.clear()
        return platform

    def _show_platform(self, platform_key: str) -> None:
        """Show the badge with the detected platform info."""
        info = SUPPORTED_PLATFORMS.get(platform_key)
        if not info:
            self.clear()
            return

        self._current_platform = platform_key
        self._icon_label.setText(info["icon"])
        self._name_label.setText(info["name"])

        # Apply platform-specific colors
        color = info["color"]
        bg_color = info["bg_color"]
        self.setStyleSheet(f"""
            QFrame#platformBadge {{
                background-color: {bg_color};
                border: 1px solid {color};
                border-radius: 12px;
                padding: 0px;
            }}
        """)
        self._name_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 700;
            color: {color};
            background: transparent;
            border: none;
        """)
        self._icon_label.setStyleSheet(f"""
            font-size: 14px;
            color: {color};
            background: transparent;
            border: none;
        """)

        if not self.isVisible():
            self.setVisible(True)
            self.setMaximumWidth(0)
            # Stop and clean up any previous animation
            if hasattr(self, '_show_anim') and self._show_anim is not None:
                self._show_anim.stop()
            self._show_anim = QPropertyAnimation(self, b"maximumWidth")
            self._show_anim.setDuration(250)
            self._show_anim.setStartValue(0)
            self._show_anim.setEndValue(200)
            self._show_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._show_anim.start()

    @property
    def current_platform(self) -> str | None:
        return self._current_platform

    @property
    def needs_cookies(self) -> bool:
        """Check if the current platform requires cookies."""
        if not self._current_platform:
            return False
        info = SUPPORTED_PLATFORMS.get(self._current_platform, {})
        return info.get("needs_cookies", False)

    def clear(self) -> None:
        """Hide and reset the badge."""
        self._current_platform = None
        self.setVisible(False)
        self._icon_label.clear()
        self._name_label.clear()
