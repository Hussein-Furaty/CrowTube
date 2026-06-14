"""
Format selector — video/audio mode toggle, format/quality selection, and download options.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.constants import (
    AUDIO_FORMATS,
    AUDIO_QUALITIES,
    DEFAULT_AUDIO_FORMAT,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_DOWNLOAD_DIR,
    DEFAULT_VIDEO_FORMAT,
    DEFAULT_VIDEO_QUALITY,
    VIDEO_FORMATS,
    VIDEO_QUALITIES,
)
from downloader.models import DownloadMode, FormatOptions
from ui.widgets.animated_button import AnimatedButton
from ui.widgets.no_scroll_combo_box import NoScrollComboBox


class FormatSelector(QFrame):
    """
    Format and quality selection panel with video/audio mode toggle.
    Includes download options checkboxes and save location.
    """

    download_requested = Signal(object)  # FormatOptions

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self._current_mode = DownloadMode.VIDEO
        self._save_directory = DEFAULT_DOWNLOAD_DIR
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)

        # ── Mode Toggle ──
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)

        self._video_btn = QPushButton("Video")
        self._video_btn.setObjectName("toggleActive")
        self._video_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._video_btn.setMinimumHeight(38)
        mode_layout.addWidget(self._video_btn)

        self._audio_btn = QPushButton("Audio Only")
        self._audio_btn.setObjectName("toggleInactive")
        self._audio_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._audio_btn.setMinimumHeight(38)
        mode_layout.addWidget(self._audio_btn)

        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        # ── Stacked Panels ──
        self._stack = QStackedWidget()

        # Video panel
        video_panel = QWidget()
        video_layout = QGridLayout(video_panel)
        video_layout.setSpacing(12)

        video_layout.addWidget(QLabel("Format:"), 0, 0)
        self._video_format_combo = NoScrollComboBox()
        self._video_format_combo.addItems(VIDEO_FORMATS)
        self._video_format_combo.setCurrentText(DEFAULT_VIDEO_FORMAT)
        video_layout.addWidget(self._video_format_combo, 0, 1)

        video_layout.addWidget(QLabel("Quality:"), 1, 0)
        self._video_quality_combo = NoScrollComboBox()
        self._video_quality_combo.addItems(VIDEO_QUALITIES)
        self._video_quality_combo.setCurrentText(DEFAULT_VIDEO_QUALITY)
        video_layout.addWidget(self._video_quality_combo, 1, 1)

        video_layout.setColumnStretch(1, 1)
        self._stack.addWidget(video_panel)

        # Audio panel
        audio_panel = QWidget()
        audio_layout = QGridLayout(audio_panel)
        audio_layout.setSpacing(12)

        audio_layout.addWidget(QLabel("Format:"), 0, 0)
        self._audio_format_combo = NoScrollComboBox()
        self._audio_format_combo.addItems(AUDIO_FORMATS)
        self._audio_format_combo.setCurrentText(DEFAULT_AUDIO_FORMAT)
        audio_layout.addWidget(self._audio_format_combo, 0, 1)

        audio_layout.addWidget(QLabel("Quality:"), 1, 0)
        self._audio_quality_combo = NoScrollComboBox()
        self._audio_quality_combo.addItems(AUDIO_QUALITIES)
        self._audio_quality_combo.setCurrentText(DEFAULT_AUDIO_QUALITY)
        audio_layout.addWidget(self._audio_quality_combo, 1, 1)

        audio_layout.setColumnStretch(1, 1)
        self._stack.addWidget(audio_panel)

        main_layout.addWidget(self._stack)

        # ── Options Checkboxes ──
        options_label = QLabel("Options")
        options_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #8888aa;")
        main_layout.addWidget(options_label)

        options_grid = QGridLayout()
        options_grid.setSpacing(8)

        self._cb_download_subs = QCheckBox("Download subtitles")
        options_grid.addWidget(self._cb_download_subs, 0, 0)

        self._cb_embed_subs = QCheckBox("Embed subtitles into video")
        options_grid.addWidget(self._cb_embed_subs, 0, 1)

        self._cb_embed_thumb = QCheckBox("Embed thumbnail")
        options_grid.addWidget(self._cb_embed_thumb, 1, 0)

        self._cb_write_metadata = QCheckBox("Write metadata")
        self._cb_write_metadata.setChecked(True)
        options_grid.addWidget(self._cb_write_metadata, 1, 1)

        self._cb_download_thumb = QCheckBox("Download thumbnail separately")
        options_grid.addWidget(self._cb_download_thumb, 2, 0)

        main_layout.addLayout(options_grid)

        # ── Save Location ──
        save_layout = QHBoxLayout()
        save_layout.setSpacing(8)

        save_label = QLabel("Save to:")
        save_label.setStyleSheet("font-weight: 600;")
        save_layout.addWidget(save_label)

        self._save_path_input = QLineEdit()
        self._save_path_input.setReadOnly(True)
        self._save_path_input.setText(self._save_directory)
        self._save_path_input.setMinimumHeight(36)
        save_layout.addWidget(self._save_path_input, 1)

        self._browse_btn = QPushButton("Browse")
        self._browse_btn.setObjectName("secondaryBtn")
        self._browse_btn.setMinimumHeight(36)
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_layout.addWidget(self._browse_btn)

        main_layout.addLayout(save_layout)

        # ── Download Button ──
        self._download_btn = AnimatedButton("Download")
        self._download_btn.setMinimumHeight(48)
        self._download_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 700;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #7c94f5; }
            QPushButton:pressed { background-color: #4a62d4; }
            QPushButton:disabled { background-color: #2d2d3d; color: #555566; }
        """)
        self._download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(self._download_btn)

    def _connect_signals(self) -> None:
        self._video_btn.clicked.connect(lambda: self._set_mode(DownloadMode.VIDEO))
        self._audio_btn.clicked.connect(lambda: self._set_mode(DownloadMode.AUDIO))
        self._browse_btn.clicked.connect(self._browse_folder)
        self._download_btn.clicked.connect(self._on_download_clicked)

    def _set_mode(self, mode: DownloadMode) -> None:
        """Switch between video and audio mode."""
        self._current_mode = mode
        if mode == DownloadMode.VIDEO:
            self._video_btn.setObjectName("toggleActive")
            self._audio_btn.setObjectName("toggleInactive")
            self._stack.setCurrentIndex(0)
            self._cb_embed_subs.setEnabled(True)
        else:
            self._video_btn.setObjectName("toggleInactive")
            self._audio_btn.setObjectName("toggleActive")
            self._stack.setCurrentIndex(1)
            self._cb_embed_subs.setEnabled(False)
            self._cb_embed_subs.setChecked(False)

        # Force style refresh
        self._video_btn.style().unpolish(self._video_btn)
        self._video_btn.style().polish(self._video_btn)
        self._audio_btn.style().unpolish(self._audio_btn)
        self._audio_btn.style().polish(self._audio_btn)

    def _browse_folder(self) -> None:
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            self._save_directory,
        )
        if folder:
            self._save_directory = folder
            self._save_path_input.setText(folder)

    def _on_download_clicked(self) -> None:
        """Build FormatOptions and emit download signal."""
        options = self.get_format_options()
        self.download_requested.emit(options)

    def get_format_options(self) -> FormatOptions:
        """Build FormatOptions from the current UI state."""
        return FormatOptions(
            mode=self._current_mode,
            video_format=self._video_format_combo.currentText(),
            video_quality=self._video_quality_combo.currentText(),
            audio_format=self._audio_format_combo.currentText(),
            audio_quality=self._audio_quality_combo.currentText(),
            download_subtitles=self._cb_download_subs.isChecked(),
            embed_subtitles=self._cb_embed_subs.isChecked(),
            embed_thumbnail=self._cb_embed_thumb.isChecked(),
            write_metadata=self._cb_write_metadata.isChecked(),
            download_thumbnail=self._cb_download_thumb.isChecked(),
        )

    def set_save_directory(self, path: str) -> None:
        """Set the save directory path."""
        self._save_directory = path
        self._save_path_input.setText(path)

    def get_save_directory(self) -> str:
        """Get the current save directory."""
        return self._save_directory

    def set_defaults(
        self,
        video_quality: str = "",
        audio_quality: str = "",
        video_format: str = "",
        audio_format: str = "",
    ) -> None:
        """Set default selections from settings."""
        if video_quality:
            self._video_quality_combo.setCurrentText(video_quality)
        if audio_quality:
            self._audio_quality_combo.setCurrentText(audio_quality)
        if video_format:
            self._video_format_combo.setCurrentText(video_format)
        if audio_format:
            self._audio_format_combo.setCurrentText(audio_format)
