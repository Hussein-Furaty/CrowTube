"""
URL input bar — text input with Paste, Analyze buttons and platform badge.
"""

from __future__ import annotations

import re

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QToolTip,
    QWidget,
)

from ui.widgets.animated_button import AnimatedButton
from ui.widgets.platform_badge import PlatformBadge


class UrlInputBar(QFrame):
    """
    URL input widget with paste and analyze buttons.
    Detects the platform (YouTube, Instagram, etc.) and shows a badge.
    """

    analyze_requested = Signal(str)  # Emits validated URL
    cancel_requested = Signal()      # Emits when user clicks Cancel during analysis

    # Pattern to find a URL anywhere in the text
    _URL_PATTERN = re.compile(
        r"(https?://[^\s]+)",
        re.IGNORECASE,
    )
    
    # Fallback pattern for domains without http://
    _DOMAIN_PATTERN = re.compile(
        r"([a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*)",
        re.IGNORECASE,
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("urlInputBar")
        self._is_loading = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Platform badge (hidden by default)
        self._platform_badge = PlatformBadge()
        layout.addWidget(self._platform_badge)

        # URL input field
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("Paste YouTube URL here...")
        self._url_input.setClearButtonEnabled(True)
        self._url_input.setMinimumHeight(40)
        layout.addWidget(self._url_input, 1)

        # Paste button
        self._paste_btn = QPushButton("Paste")
        self._paste_btn.setObjectName("secondaryBtn")
        self._paste_btn.setMinimumHeight(40)
        self._paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._paste_btn)

        # Analyze button
        self._analyze_btn = AnimatedButton("Analyze")
        self._analyze_btn.setMinimumHeight(40)
        self._analyze_btn.setMinimumWidth(120)
        self._analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._analyze_btn)

    def _connect_signals(self) -> None:
        self._paste_btn.clicked.connect(self._paste_from_clipboard)
        self._analyze_btn.clicked.connect(self._on_analyze_clicked)
        self._url_input.returnPressed.connect(self._on_analyze_clicked)
        # Detect platform as user types
        self._url_input.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str) -> None:
        """Detect and show platform badge as user types/pastes a URL."""
        text = text.strip()
        if not text:
            self._platform_badge.clear()
            return

        # Try to extract URL
        match = self._URL_PATTERN.search(text)
        if match:
            self._platform_badge.detect_and_show(match.group(1))
        else:
            domain_match = self._DOMAIN_PATTERN.search(text)
            if domain_match:
                self._platform_badge.detect_and_show("https://" + domain_match.group(1))
            else:
                self._platform_badge.clear()

    def _paste_from_clipboard(self) -> None:
        """Paste text from the system clipboard into the URL field."""
        clipboard = QApplication.clipboard()
        if clipboard:
            text = clipboard.text().strip()
            if text:
                self._url_input.setText(text)

    def _on_analyze_clicked(self) -> None:
        """Validate URL and emit analyze signal."""
        if self._is_loading:
            self.cancel_requested.emit()
            return

        text = self._url_input.text().strip()
        if not text:
            QToolTip.showText(
                self._analyze_btn.mapToGlobal(self._analyze_btn.rect().center()),
                "Please enter a valid video URL",
            )
            return

        # Extract URL if there's extra text (like "Watch this reel! https://...")
        url = None
        match = self._URL_PATTERN.search(text)
        if match:
            url = match.group(1)
        else:
            # Fallback for URLs copied without https:// (e.g. www.instagram.com/...)
            domain_match = self._DOMAIN_PATTERN.search(text)
            if domain_match:
                url = "https://" + domain_match.group(1)

        if not url:
            QToolTip.showText(
                self._url_input.mapToGlobal(self._url_input.rect().center()),
                "Please enter a valid HTTP(s) link",
            )
            return

        # Ensure it's a YouTube link
        if "youtube.com" not in url.lower() and "youtu.be" not in url.lower():
            QToolTip.showText(
                self._url_input.mapToGlobal(self._url_input.rect().center()),
                "Only YouTube links are supported.",
            )
            return

        # Clean the input field to show just the extracted URL
        if url != text:
            self._url_input.setText(url)
            
        self.analyze_requested.emit(url)

    def _validate_url(self, url: str) -> bool:
        """Check if the URL looks like a valid URL."""
        return bool(self._URL_PATTERN.search(url))

    def set_loading(self, loading: bool) -> None:
        """Toggle loading state — disables input and changes button text to Cancel."""
        self._is_loading = loading
        self._url_input.setEnabled(not loading)
        self._paste_btn.setEnabled(not loading)
        
        self._analyze_btn.setText("Cancel" if loading else "Analyze")
        if loading:
            self._analyze_btn.setObjectName("dangerBtn")
        else:
            self._analyze_btn.setObjectName("")
            
        # Re-apply styles
        self._analyze_btn.style().unpolish(self._analyze_btn)
        self._analyze_btn.style().polish(self._analyze_btn)

    def clear(self) -> None:
        """Clear the URL input and platform badge."""
        self._url_input.clear()
        self._platform_badge.clear()

    def get_url(self) -> str:
        """Get the current URL text."""
        return self._url_input.text().strip()

    def set_url(self, url: str) -> None:
        """Set the URL text programmatically."""
        self._url_input.setText(url)
