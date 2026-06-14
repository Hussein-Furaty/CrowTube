"""
No-scroll Combo Box - A QComboBox that ignores mouse wheel events.
"""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox
from PySide6.QtGui import QWheelEvent


class NoScrollComboBox(QComboBox):
    """
    A QComboBox that ignores mouse wheel events.
    This prevents the selected item from accidentally changing when the user 
    is scrolling the page.
    """

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Ignore the event to let it propagate to the parent (e.g. QScrollArea)
        event.ignore()
