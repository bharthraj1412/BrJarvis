# memory/reflection.py — Behavioral & Code Reflection Engine
"""
ReflectionEngine for analyzing user feedback, implicit re-prompts, and failed steps,
writing extracted lessons to LessonStore.
"""
from __future__ import annotations

import re
import time
from memory.lessons import LessonStore


class ReflectionEngine:
    """Monitors turns and task outcomes to automatically extract lessons."""

    def __init__(self, lesson_store: LessonStore | None = None):
        self.lesson_store = lesson_store or LessonStore()

    def process_turn(
        self, user_input: str, previous_output: str, elapsed_since_last_sec: float = 0
    ) -> dict | None:
        """
        Analyze dialogue turn for explicit or implicit user corrections.
        """
        clean_in = user_input.strip().lower()

        # 1. Explicit correction patterns
        explicit_patterns = [
            r"no,?\s+(?:don't|do not|instead)\s+(.+)",
            r"wrong,?\s+(.+)",
            r"stop\s+doing\s+(.+)",
            r"always\s+(?:use|do|make)\s+(.+)",
            r"never\s+(?:use|do|make)\s+(.+)",
        ]

        for pat in explicit_patterns:
            m = re.search(pat, clean_in)
            if m:
                correction = user_input.strip()
                topic = m.group(1).strip()
                lesson_id = self.lesson_store.add_lesson(
                    topic=topic,
                    correction=correction,
                    source="explicit",
                    weight=2.0,
                )
                return {
                    "type": "explicit_correction",
                    "lesson_id": lesson_id,
                    "topic": topic,
                    "correction": correction,
                }

        # 2. Implicit correction (user re-prompts immediately after turn within 45s)
        if 0 < elapsed_since_last_sec <= 45 and ("redo" in clean_in or "try again" in clean_in or "fix this" in clean_in):
            topic = user_input[:50]
            lesson_id = self.lesson_store.add_lesson(
                topic=topic,
                correction=f"User requested re-do within {int(elapsed_since_last_sec)}s: '{user_input}'",
                source="implicit",
                weight=1.0,
            )
            return {
                "type": "implicit_correction",
                "lesson_id": lesson_id,
                "topic": topic,
            }

        return None
