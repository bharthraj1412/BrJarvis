# context/token_manager.py — BR JARVIS Token & Context Manager
"""
Token Budget Manager & Sliding Window History Trimmer.
Monitors token usage, enforces context window caps (default 12,000 tokens),
and tracks real-time token savings from Antigravity optimizations.
"""
from __future__ import annotations

import time


class TokenBudgetManager:
    """Singleton tracker for token consumption and Antigravity savings telemetry."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.tokens_consumed = 0
            cls._instance.tokens_saved = 0
            cls._instance.bypassed_calls = 0
            cls._instance.start_time = time.time()
        return cls._instance

    def record_usage(self, consumed: int, saved: int = 0, is_bypassed: bool = False):
        """Record token usage and savings for telemetry."""
        self.tokens_consumed += consumed
        self.tokens_saved += saved
        if is_bypassed:
            self.bypassed_calls += 1

    def get_telemetry(self) -> dict:
        """Return real-time token efficiency metrics."""
        elapsed = max(1.0, time.time() - self.start_time)
        total_attempted = self.tokens_consumed + self.tokens_saved
        efficiency_pct = round((self.tokens_saved / total_attempted * 100), 1) if total_attempted > 0 else 0.0

        return {
            "consumed": self.tokens_consumed,
            "saved": self.tokens_saved,
            "efficiency_pct": efficiency_pct,
            "bypassed_calls": self.bypassed_calls,
            "uptime_sec": round(elapsed, 1),
        }


class ContextTokenTrimmer:
    """Sliding Window Context Trimmer to prevent context bloat."""

    MAX_HISTORY_TOKENS = 12000

    @classmethod
    def trim_history(cls, history: list[dict], max_tokens: int = 12000) -> list[dict]:
        """
        Trim conversation history to stay within max_tokens while preserving recent turns.
        Estimate 1 token ~= 4 chars.
        """
        if not history:
            return []

        trimmed = []
        accumulated_chars = 0
        char_limit = max_tokens * 4

        # Iterate from most recent to oldest
        for msg in reversed(history):
            content = str(msg.get("content", ""))
            msg_chars = len(content)

            if accumulated_chars + msg_chars <= char_limit:
                trimmed.append(msg)
                accumulated_chars += msg_chars
            else:
                break

        return list(reversed(trimmed))
