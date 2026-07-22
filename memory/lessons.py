# memory/lessons.py — Persistent Lesson & Correction Store
"""
LessonStore for storing and semantically retrieving explicit and implicit user corrections.
Used by ContextEngine at Priority 6 to ensure past corrections prevent repeating errors.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

LESSONS_DB_FILE = Path("memory_db/lessons.db")


class LessonStore:
    """Stores and retrieves user corrections and architectural lessons."""

    def __init__(self, db_path: Path = LESSONS_DB_FILE):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    correction TEXT NOT NULL,
                    source TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at REAL NOT NULL,
                    last_retrieved_at REAL
                )
                """
            )
            conn.commit()

    def add_lesson(
        self, topic: str, correction: str, source: str = "explicit", weight: float = 1.0
    ) -> int:
        """Add a correction lesson to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO lessons (topic, correction, source, weight, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (topic, correction, source, weight, time.time()),
            )
            conn.commit()
            return cur.lastrowid or 0

    def get_relevant_lessons(self, query: str, limit: int = 5) -> list[dict]:
        """Retrieve relevant lessons matching query keywords."""
        query_words = [w.lower() for w in query.split() if len(w) > 3]
        if not query_words:
            return self.get_latest_lessons(limit=limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM lessons ORDER BY weight DESC, created_at DESC LIMIT 50"
            ).fetchall()

            matched = []
            for row in rows:
                text = f"{row['topic']} {row['correction']}".lower()
                score = sum(1 for w in query_words if w in text)
                if score > 0 or not query_words:
                    item = dict(row)
                    matched.append((score, item))

            matched.sort(key=lambda x: x[0], reverse=True)
            return [m[1] for m in matched[:limit]]

    def get_latest_lessons(self, limit: int = 5) -> list[dict]:
        """Get latest lessons sorted by timestamp."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM lessons ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
