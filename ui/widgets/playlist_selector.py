"""
Playlist selector widget — allows selecting specific videos from a playlist.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QPushButton,
)

from downloader.models import PlaylistEntry, PlaylistInfo
from ui.widgets.animated_button import AnimatedButton


class PlaylistSelector(QFrame):
    """
    Shows a list of videos in a playlist and allows selecting which ones to download.
    """

    download_selected = Signal(list)  # list[PlaylistEntry]
    download_all = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setVisible(False)
        self._entries: list[PlaylistEntry] = []
        self._checkboxes: list[QCheckBox] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # ── Header ──
        header_layout = QHBoxLayout()
        
        self._title_label = QLabel()
        self._title_label.setObjectName("titleLabel")
        header_layout.addWidget(self._title_label)

        self._count_label = QLabel()
        self._count_label.setObjectName("subtitleLabel")
        header_layout.addWidget(self._count_label)
        
        header_layout.addStretch()

        self._select_all_btn = QPushButton("Select All")
        self._select_all_btn.setObjectName("smallBtn")
        self._select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._select_all_btn.clicked.connect(self._on_select_all)
        header_layout.addWidget(self._select_all_btn)

        self._deselect_all_btn = QPushButton("Deselect All")
        self._deselect_all_btn.setObjectName("smallBtn")
        self._deselect_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._deselect_all_btn.clicked.connect(self._on_deselect_all)
        header_layout.addWidget(self._deselect_all_btn)

        layout.addLayout(header_layout)

        # ── Scroll Area ──
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMinimumHeight(200)
        self._scroll_area.setMaximumHeight(350)
        
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setSpacing(8)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self._scroll_area.setWidget(self._list_widget)
        layout.addWidget(self._scroll_area)

        # ── Actions ──
        actions_layout = QHBoxLayout()
        
        self._download_all_btn = QPushButton("Download All")
        self._download_all_btn.setObjectName("secondaryBtn")
        self._download_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._download_all_btn.setMinimumHeight(40)
        self._download_all_btn.clicked.connect(self._on_download_all)
        actions_layout.addWidget(self._download_all_btn)

        self._download_selected_btn = AnimatedButton("Download Selected")
        self._download_selected_btn.setMinimumHeight(40)
        self._download_selected_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._download_selected_btn.clicked.connect(self._on_download_selected)
        actions_layout.addWidget(self._download_selected_btn)

        layout.addLayout(actions_layout)

    def set_playlist(self, info: PlaylistInfo) -> None:
        self._entries = info.entries
        self._title_label.setText(info.title)
        self._count_label.setText(f"({info.video_count} videos)")
        
        # Clear existing
        for i in reversed(range(self._list_layout.count())): 
            widget = self._list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self._checkboxes.clear()

        # Add checkboxes
        for entry in self._entries:
            cb = QCheckBox(f"{entry.index}. {entry.title} [{entry.duration_str}]")
            cb.setChecked(True)
            cb.stateChanged.connect(self._update_button_text)
            self._list_layout.addWidget(cb)
            self._checkboxes.append(cb)

        self._update_button_text()
        self.setVisible(True)

    def _on_select_all(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(True)

    def _on_deselect_all(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(False)

    def _update_button_text(self) -> None:
        selected_count = sum(1 for cb in self._checkboxes if cb.isChecked())
        self._download_selected_btn.setText(f"Download Selected ({selected_count})")
        self._download_selected_btn.setEnabled(selected_count > 0)

    def _on_download_all(self) -> None:
        for entry in self._entries:
            entry.selected = True
        self.download_all.emit()

    def _on_download_selected(self) -> None:
        selected_entries = []
        for cb, entry in zip(self._checkboxes, self._entries):
            entry.selected = cb.isChecked()
            if entry.selected:
                selected_entries.append(entry)
        
        self.download_selected.emit(selected_entries)

    def clear(self) -> None:
        self._entries.clear()
        self.setVisible(False)
