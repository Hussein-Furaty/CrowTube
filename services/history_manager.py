"""
History manager — SQLite-backed download history storage.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.constants import HISTORY_DB_PATH
from downloader.models import HistoryEntry

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Manages download history using a local SQLite database.
    Thread-safe via per-call connections.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or HISTORY_DB_PATH
        # Ensure the directory exists
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_table()
        logger.info("HistoryManager initialized: %s", self._db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_table(self) -> None:
        """Create the downloads table if it doesn't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    url TEXT NOT NULL,
                    date TEXT NOT NULL,
                    download_type TEXT NOT NULL DEFAULT 'video',
                    save_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed'
                )
            """)
            conn.commit()

    def add_entry(self, entry: HistoryEntry) -> int:
        """Insert a new history record. Returns the new row ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO downloads (filename, url, date, download_type, save_path, file_size, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.filename,
                    entry.url,
                    entry.date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    entry.download_type,
                    entry.save_path,
                    entry.file_size,
                    entry.status,
                ),
            )
            conn.commit()
            row_id = cursor.lastrowid
            logger.info("History entry added: %s (id=%d)", entry.filename, row_id)
            return row_id

    def get_all(self) -> list[HistoryEntry]:
        """Get all history entries, newest first."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM downloads ORDER BY date DESC"
            ).fetchall()
            return [self._row_to_entry(row) for row in rows]

    def search(self, query: str) -> list[HistoryEntry]:
        """Search history by filename (case-insensitive partial match)."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM downloads WHERE filename LIKE ? ORDER BY date DESC",
                (f"%{query}%",),
            ).fetchall()
            return [self._row_to_entry(row) for row in rows]

    def delete_entry(self, entry_id: int) -> None:
        """Delete a single history entry by ID."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM downloads WHERE id = ?", (entry_id,))
            conn.commit()
            logger.info("History entry deleted: id=%d", entry_id)

    def clear_all(self) -> None:
        """Delete all history records."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM downloads")
            conn.commit()
            logger.info("All history cleared")

    def get_total_count(self) -> int:
        """Get total number of history entries."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()
            return row[0] if row else 0

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> HistoryEntry:
        """Convert a database row to a HistoryEntry."""
        return HistoryEntry(
            id=row["id"],
            filename=row["filename"],
            url=row["url"],
            date=row["date"],
            download_type=row["download_type"],
            save_path=row["save_path"],
            file_size=row["file_size"],
            status=row["status"],
        )
