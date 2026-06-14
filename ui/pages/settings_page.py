"""
Settings page — configuration options for the application.
Includes cookies/authentication for multi-platform support.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QFormLayout,
    QFileDialog,
    QMessageBox,
    QGroupBox,
)

from services.settings_manager import SettingsManager
from config.constants import (
    VIDEO_QUALITIES, AUDIO_QUALITIES, VIDEO_FORMATS, AUDIO_FORMATS,
    COOKIE_BROWSERS,
)
from ui.widgets.animated_button import AnimatedButton
from ui.widgets.no_scroll_combo_box import NoScrollComboBox


class SettingsPage(QWidget):
    """
    Application settings UI organized into tabs.
    """

    settings_changed = Signal()
    theme_changed = Signal(str)

    def __init__(self, settings_manager: SettingsManager, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings_manager
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_general_tab(), "General")
        self._tabs.addTab(self._create_downloads_tab(), "Downloads")
        self._tabs.addTab(self._create_advanced_tab(), "Advanced")
        layout.addWidget(self._tabs, 1)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._reset_btn = QPushButton("Reset to Defaults")
        self._reset_btn.setObjectName("secondaryBtn")
        self._reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(self._reset_btn)

        self._save_btn = AnimatedButton("Save Settings")
        self._save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Download Folder
        folder_layout = QHBoxLayout()
        self._folder_input = QLineEdit()
        self._folder_input.setReadOnly(True)
        folder_layout.addWidget(self._folder_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addRow("Default Save Location:", folder_layout)

        # Theme
        self._theme_combo = NoScrollComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        layout.addRow("Application Theme:", self._theme_combo)

        # Language
        self._lang_combo = NoScrollComboBox()
        self._lang_combo.addItems(["English"])
        layout.addRow("Language:", self._lang_combo)

        return widget

    def _create_downloads_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        self._vid_qual_combo = NoScrollComboBox()
        self._vid_qual_combo.addItems(VIDEO_QUALITIES)
        layout.addRow("Default Video Quality:", self._vid_qual_combo)

        self._vid_fmt_combo = NoScrollComboBox()
        self._vid_fmt_combo.addItems(VIDEO_FORMATS)
        layout.addRow("Default Video Format:", self._vid_fmt_combo)

        self._aud_qual_combo = NoScrollComboBox()
        self._aud_qual_combo.addItems(AUDIO_QUALITIES)
        layout.addRow("Default Audio Quality:", self._aud_qual_combo)

        self._aud_fmt_combo = NoScrollComboBox()
        self._aud_fmt_combo.addItems(AUDIO_FORMATS)
        layout.addRow("Default Audio Format:", self._aud_fmt_combo)

        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 10)
        layout.addRow("Concurrent Downloads:", self._concurrent_spin)

        return widget



    def _create_advanced_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        self._ffmpeg_input = QLineEdit()
        self._ffmpeg_input.setPlaceholderText("Leave empty to use bundled tools")
        layout.addRow("FFmpeg Directory:", self._ffmpeg_input)

        self._ytdlp_input = QLineEdit()
        self._ytdlp_input.setPlaceholderText("Leave empty to use bundled tools")
        layout.addRow("yt-dlp Path:", self._ytdlp_input)

        self._proxy_check = QCheckBox("Enable Proxy")
        self._proxy_input = QLineEdit()
        self._proxy_input.setPlaceholderText("e.g., http://127.0.0.1:8080")
        
        proxy_layout = QHBoxLayout()
        proxy_layout.addWidget(self._proxy_check)
        proxy_layout.addWidget(self._proxy_input)
        layout.addRow("Network Proxy:", proxy_layout)

        return widget

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Default Download Folder", self._folder_input.text())
        if folder:
            self._folder_input.setText(folder)

    def _load_settings(self) -> None:
        """Populate UI from SettingsManager."""
        self._folder_input.setText(self._settings.get_download_folder())
        self._theme_combo.setCurrentText(self._settings.get_theme().capitalize())
        
        self._vid_qual_combo.setCurrentText(self._settings.get_default_video_quality())
        self._vid_fmt_combo.setCurrentText(self._settings.get_default_video_format())
        self._aud_qual_combo.setCurrentText(self._settings.get_default_audio_quality())
        self._aud_fmt_combo.setCurrentText(self._settings.get_default_audio_format())
        self._concurrent_spin.setValue(self._settings.get_concurrent_downloads())
        
        self._ffmpeg_input.setText(self._settings.get("advanced/ffmpeg_path", ""))
        self._ytdlp_input.setText(self._settings.get("advanced/ytdlp_path", ""))
        self._proxy_check.setChecked(self._settings.get("advanced/proxy_enabled", False))
        self._proxy_input.setText(self._settings.get("advanced/proxy_url", ""))

    def _save_settings(self) -> None:
        """Write UI state to SettingsManager."""
        old_theme = self._settings.get_theme()
        new_theme = self._theme_combo.currentText().lower()

        self._settings.set_download_folder(self._folder_input.text())
        self._settings.set_theme(new_theme)
        
        self._settings.set("downloads/default_video_quality", self._vid_qual_combo.currentText())
        self._settings.set("downloads/default_video_format", self._vid_fmt_combo.currentText())
        self._settings.set("downloads/default_audio_quality", self._aud_qual_combo.currentText())
        self._settings.set("downloads/default_audio_format", self._aud_fmt_combo.currentText())
        self._settings.set_concurrent_downloads(self._concurrent_spin.value())
        
        self._settings.set("advanced/ffmpeg_path", self._ffmpeg_input.text())
        self._settings.set("advanced/ytdlp_path", self._ytdlp_input.text())
        self._settings.set("advanced/proxy_enabled", self._proxy_check.isChecked())
        self._settings.set("advanced/proxy_url", self._proxy_input.text())

        self._settings.sync()
        self.settings_changed.emit()
        
        if old_theme != new_theme:
            self.theme_changed.emit(new_theme)
            
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully.")

    def _reset_defaults(self) -> None:
        reply = QMessageBox.question(
            self, "Reset Settings", "Reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._settings.reset_to_defaults()
            self._load_settings()
            self.settings_changed.emit()
