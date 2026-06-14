"""
History page — displays completed downloads history table.
"""

from __future__ import annotations

import os
import subprocess
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

from services.history_manager import HistoryManager


class HistoryPage(QWidget):
    """
    Displays the download history in a searchable table.
    """

    def __init__(self, history_manager: HistoryManager, parent=None) -> None:
        super().__init__(parent)
        self._history = history_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Download History")
        title.setObjectName("sectionTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search history...")
        self._search_input.setMaximumWidth(250)
        self._search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self._search_input)

        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.setObjectName("dangerBtn")
        self._clear_btn.clicked.connect(self._clear_all)
        header_layout.addWidget(self._clear_btn)

        layout.addLayout(header_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["File Name", "Date", "Type", "Location", "Size", "Actions"])
        
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(50)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setShowGrid(False)

        layout.addWidget(self._table, 1)

    def showEvent(self, event) -> None:
        """Refresh data when page becomes visible."""
        self.refresh()
        super().showEvent(event)

    def refresh(self) -> None:
        """Reload table data from database."""
        entries = self._history.get_all()
        self._populate_table(entries)

    def _on_search(self, text: str) -> None:
        if not text:
            self.refresh()
        else:
            entries = self._history.search(text)
            self._populate_table(entries)

    def _populate_table(self, entries) -> None:
        self._table.setRowCount(0)
        for row, entry in enumerate(entries):
            self._table.insertRow(row)
            
            self._table.setItem(row, 0, QTableWidgetItem(entry.filename))
            self._table.setItem(row, 1, QTableWidgetItem(entry.date))
            self._table.setItem(row, 2, QTableWidgetItem(entry.download_type.upper()))
            
            # Shorten location path for display
            path_item = QTableWidgetItem(entry.save_path)
            path_item.setToolTip(entry.save_path)
            self._table.setItem(row, 3, path_item)
            
            self._table.setItem(row, 4, QTableWidgetItem(entry.file_size_str))
            
            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn_play = QPushButton("▶ Play")
            btn_play.setObjectName("smallBtn")
            btn_play.setToolTip("Open File")
            btn_play.clicked.connect(lambda checked, p=entry.save_path: self._open_file(p))
            actions_layout.addWidget(btn_play)
            
            btn_folder = QPushButton("📂 Folder")
            btn_folder.setObjectName("smallBtn")
            btn_folder.setToolTip("Open Folder")
            btn_folder.clicked.connect(lambda checked, p=entry.save_path: self._open_folder(p))
            actions_layout.addWidget(btn_folder)

            btn_delete = QPushButton("✕ Delete")
            btn_delete.setObjectName("smallBtn")
            btn_delete.setStyleSheet("color: #ef4444; font-weight: bold; background-color: rgba(239, 68, 68, 0.1);")
            btn_delete.setToolTip("Remove from History")
            btn_delete.clicked.connect(lambda checked, id=entry.id, r=row: self._delete_entry(id, r))
            actions_layout.addWidget(btn_delete)
            
            self._table.setCellWidget(row, 5, actions_widget)

    def _open_file(self, path: str) -> None:
        if os.path.exists(path):
            os.startfile(os.path.normpath(path))
        else:
            QMessageBox.warning(self, "Not Found", f"The file no longer exists at:\n{path}")

    def _open_folder(self, path: str) -> None:
        if os.path.exists(path):
            subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
        else:
            QMessageBox.warning(self, "Not Found", "The folder no longer exists.")

    def _delete_entry(self, entry_id: int, row: int) -> None:
        self._history.delete_entry(entry_id)
        self._table.removeRow(row)

    def _clear_all(self) -> None:
        reply = QMessageBox.question(
            self, "Clear History", 
            "Are you sure you want to clear all download history?\nThis will not delete the actual files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._history.clear_all()
            self.refresh()
