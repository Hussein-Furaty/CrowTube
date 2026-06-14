"""
About dialog — displays application information, academic description, and credits.
"""

from __future__ import annotations

import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)

from config.constants import APP_NAME, APP_VERSION, APP_AUTHOR, APP_ORGANIZATION, ASSETS_DIR


class AboutDialog(QDialog):
    """An academically and professionally styled modal dialog displaying application info."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About CrowTube")
        self.resize(480, 500)
        self.setMinimumSize(450, 480)
        
        # Standardize window flags to fix movement/drag issues on Windows
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowTitleHint | 
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Ensure it centers properly over the main window
        if parent:
            self.setWindowModality(Qt.WindowModality.WindowModal)
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Elevated Card Frame
        card = QFrame()
        card.setObjectName("elevatedCard")
        card.setStyleSheet("""
            QFrame#elevatedCard {
                background-color: transparent;
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 16px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        card_layout.setSpacing(16)
        
        # 1. Application Logo
        icon_label = QLabel()
        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            # Large, prominent logo
            pixmap = pixmap.scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)
        
        card_layout.addSpacing(5)

        # 2. Application Name & Version
        app_name = QLabel(APP_NAME)
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet("""
            font-size: 28px; 
            font-weight: 800; 
            color: #6366f1;
            letter-spacing: 1px;
        """)
        card_layout.addWidget(app_name)

        version = QLabel(f"Build Version {APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("""
            font-size: 12px; 
            font-weight: 600;
            color: #8b9bb4;
            letter-spacing: 2px;
            text-transform: uppercase;
        """)
        card_layout.addWidget(version)

        card_layout.addSpacing(10)
        
        # Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: rgba(99, 102, 241, 0.2); border: none; height: 1px;")
        card_layout.addWidget(line)

        card_layout.addSpacing(10)
        
        # 3. Academic & Professional Description
        academic_desc = (
            "A comprehensive media acquisition architecture "
            "designed to facilitate the seamless extraction and archival of high-fidelity "
            "digital content.\n\n"
            "Engineered with a robust, asynchronous processing pipeline, this tool "
            "natively supports automated format resolution and high-speed processing "
            "for YouTube ecosystems."
        )
        desc_label = QLabel(academic_desc)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignJustify)
        desc_label.setStyleSheet("""
            font-size: 13px; 
            line-height: 1.6;
            padding: 0 10px;
        """)
        card_layout.addWidget(desc_label)
        
        card_layout.addSpacing(15)

        # 4. Credits & Architecture
        tech_stack = QLabel(
            "<b>Core Architecture:</b> Python 3.10+, PySide6 (Qt framework)<br>"
            "<b>Extraction Engine:</b> yt-dlp integrated wrapper<br>"
            "<b>Multimedia Processing:</b> FFmpeg algorithmic integration"
        )
        tech_stack.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_stack.setStyleSheet("font-size: 12px; line-height: 1.5; opacity: 0.8;")
        card_layout.addWidget(tech_stack)

        card_layout.addSpacing(15)

        # 5. Author Information
        author_info = QLabel(
            f"<span style='color: #6366f1; font-weight: bold;'>Principal Investigator:</span> {APP_AUTHOR}<br>"
            f"<span style='color: #6366f1; font-weight: bold;'>Research & Development:</span> {APP_ORGANIZATION}"
        )
        author_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_info.setStyleSheet("font-size: 12px;")
        card_layout.addWidget(author_info)

        # Bottom stretch to push copyright down
        card_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # 6. Copyright
        year = datetime.datetime.now().year
        copyright_info = QLabel(f"© {year} {APP_ORGANIZATION}. All rights reserved.")
        copyright_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_info.setStyleSheet("font-size: 11px; opacity: 0.6;")
        card_layout.addWidget(copyright_info)

        main_layout.addWidget(card)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Acknowledge & Close")
        close_btn.setFixedSize(180, 42)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        btn_layout.addStretch()
        
        main_layout.addLayout(btn_layout)
