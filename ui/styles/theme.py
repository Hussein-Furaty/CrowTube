"""
Theme manager — loads and applies QSS themes to the application.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from config.constants import STYLES_DIR

logger = logging.getLogger(__name__)


class ThemeManager:
    """Manages application themes (dark/light)."""

    @staticmethod
    def apply_dark_theme(app: QApplication) -> None:
        """Apply the dark theme stylesheet to the application."""
        app.setStyle("Fusion")

        qss_path = Path(STYLES_DIR) / "dark_theme.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
            app.setStyleSheet(stylesheet)
            logger.info("Dark theme applied from: %s", qss_path)
        else:
            logger.warning("Dark theme QSS not found at: %s", qss_path)
            # Apply a basic dark palette as fallback
            ThemeManager._apply_dark_palette(app)

    @staticmethod
    def apply_light_theme(app: QApplication) -> None:
        """Apply a light theme to the application."""
        app.setStyle("Fusion")

        qss_path = Path(STYLES_DIR) / "light_theme.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
            app.setStyleSheet(stylesheet)
            logger.info("Light theme applied from: %s", qss_path)
        else:
            # Apply system default light palette
            app.setStyleSheet("")
            app.setPalette(app.style().standardPalette())
            logger.info("Light theme applied (system default)")

    @staticmethod
    def apply_theme(app: QApplication, theme_name: str) -> None:
        """Apply a theme by name."""
        if theme_name == "dark":
            ThemeManager.apply_dark_theme(app)
        elif theme_name == "light":
            ThemeManager.apply_light_theme(app)
        else:
            logger.warning("Unknown theme: %s, falling back to dark", theme_name)
            ThemeManager.apply_dark_theme(app)

    @staticmethod
    def _apply_dark_palette(app: QApplication) -> None:
        """Fallback: apply a dark QPalette when QSS file is not found."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0f0f1a"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#e8e8f0"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e32"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#252547"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#252547"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e8e8f0"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#e8e8f0"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#1e1e32"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e8e8f0"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#667eea"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#667eea"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

        # Disabled colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#555566"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#555566"))

        app.setPalette(palette)
        logger.info("Dark palette applied as fallback")
