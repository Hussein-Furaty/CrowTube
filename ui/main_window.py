"""
Main window — application shell with sidebar navigation and stacked pages.
"""

from __future__ import annotations

import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QPushButton,
    QStackedWidget,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QSystemTrayIcon,
    QMenu,
    QApplication,
)

from config.constants import (
    APP_NAME, 
    APP_VERSION, 
    WINDOW_DEFAULT_WIDTH, 
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    SIDEBAR_WIDTH
)

from ui.pages.download_page import DownloadPage
from ui.pages.queue_page import QueuePage
from ui.pages.history_page import HistoryPage
from ui.pages.settings_page import SettingsPage
from ui.dialogs.about_dialog import AboutDialog

from services.settings_manager import SettingsManager
from services.history_manager import HistoryManager
from services.thumbnail_loader import ThumbnailLoader
from downloader.download_engine import DownloadEngine
from downloader.download_queue import DownloadQueueManager
from downloader.models import DownloadItem, HistoryEntry, DownloadStatus

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application shell. Contains the sidebar navigation and a stacked
    widget to switch between different pages.
    """

    def __init__(self) -> None:
        super().__init__()
        self._setup_managers()
        self._setup_window()
        self._setup_ui()
        self._setup_tray()
        self._connect_signals()
        
        # Start on download page
        self._switch_page(0)

    def _setup_managers(self) -> None:
        """Initialize all backend managers."""
        self.settings_manager = SettingsManager.instance()
        self.history_manager = HistoryManager()
        self.thumbnail_loader = ThumbnailLoader(self)
        
        # Create download engine using settings
        self.download_engine = DownloadEngine(
            ffmpeg_dir=self.settings_manager.get_ffmpeg_dir(),
            proxy=self.settings_manager.get_proxy(),
        )
        
        # Create queue manager
        self.queue_manager = DownloadQueueManager(
            self.download_engine, 
            max_concurrent=self.settings_manager.get_concurrent_downloads()
        )

    def _setup_tray(self) -> None:
        """Initialize the system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        icon = QApplication.instance().windowIcon()
        self.tray_icon.setIcon(icon)
        
        # Create tray menu
        tray_menu = QMenu(self)
        show_action = tray_menu.addAction("Show Application")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def quit_app(self) -> None:
        """Force quit the application."""
        logger.info("Application force shutting down...")
        self.queue_manager.cancel_all()
        QApplication.quit()

    def _setup_window(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        
        # Center on screen
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 30, 10, 30)
        sidebar_layout.setSpacing(8)

        # App Logo/Name
        logo_label = QLabel(APP_NAME)
        logo_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 0 10px;")
        sidebar_layout.addWidget(logo_label)
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("font-size: 12px; padding: 0 10px;")
        sidebar_layout.addWidget(version_label)
        
        sidebar_layout.addSpacing(30)

        # Navigation Buttons
        self._nav_buttons = []
        nav_items = [
            ("Download", 0),
            ("Queue", 1),
            ("History", 2),
            ("Settings", 3)
        ]
        
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self._switch_page(idx))
            self._nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # About button
        about_btn = QPushButton("About")
        about_btn.setObjectName("navButton")
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.clicked.connect(self._show_about)
        sidebar_layout.addWidget(about_btn)

        main_layout.addWidget(sidebar)

        # ── Stacked Pages ──
        self._stack = QStackedWidget()
        
        # Create pages
        self._download_page = DownloadPage(
            self.download_engine, 
            self.settings_manager, 
            self.thumbnail_loader
        )
        self._queue_page = QueuePage(
            self.queue_manager,
            self.thumbnail_loader
        )
        self._history_page = HistoryPage(self.history_manager)
        self._settings_page = SettingsPage(self.settings_manager)

        self._stack.addWidget(self._download_page)
        self._stack.addWidget(self._queue_page)
        self._stack.addWidget(self._history_page)
        self._stack.addWidget(self._settings_page)

        main_layout.addWidget(self._stack, 1)

    def _connect_signals(self) -> None:
        # Cross-component connections
        self._download_page.add_to_queue.connect(self._on_add_to_queue)
        self._queue_page._queue.active_count_changed.connect(self._update_queue_badge)
        self._queue_page._queue.item_finished.connect(self._on_download_finished)
        self._settings_page.settings_changed.connect(self._on_settings_changed)
        self._settings_page.theme_changed.connect(self._on_theme_changed)

    def _switch_page(self, index: int) -> None:
        """Switch stacked widget and update nav button styling."""
        self._stack.setCurrentIndex(index)
        
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.setObjectName("navButtonActive")
            else:
                btn.setObjectName("navButton")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _update_queue_badge(self, count: int) -> None:
        """Update the queue button text with active count."""
        btn = self._nav_buttons[1]
        if count > 0:
            btn.setText(f"Queue ({count})")
        else:
            btn.setText("Queue")

    def _on_add_to_queue(self, item: DownloadItem) -> None:
        """Handle new download request."""
        self.queue_manager.add_item(item)
        # Auto switch to queue page
        self._switch_page(1)

    def _on_download_finished(self, item_id: str, file_path: str) -> None:
        """Record completed download in history."""
        item = self.queue_manager.items.get(item_id)
        if item:
            entry = HistoryEntry(
                filename=item.title,
                url=item.url,
                download_type=item.format_options.mode.value,
                save_path=file_path,
                file_size=item.progress.total_bytes,
                status="completed"
            )
            self.history_manager.add_entry(entry)

    def _on_settings_changed(self) -> None:
        """Apply new settings to engines."""
        self.download_engine.set_ffmpeg_dir(self.settings_manager.get_ffmpeg_dir())
        self.download_engine.set_proxy(self.settings_manager.get_proxy())
        self.queue_manager.set_max_concurrent(self.settings_manager.get_concurrent_downloads())

    def _on_theme_changed(self, theme_name: str) -> None:
        """Apply the selected theme."""
        from ui.styles.theme import ThemeManager
        from PySide6.QtWidgets import QApplication
        ThemeManager.apply_theme(QApplication.instance(), theme_name)

    def _show_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()

    def closeEvent(self, event) -> None:
        """Hide to tray instead of closing."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            APP_NAME,
            "Application minimized to tray. Downloads will continue.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
