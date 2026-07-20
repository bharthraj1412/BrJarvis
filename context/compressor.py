# context/compressor.py — Semantic Context Compressor & Noise Eliminator for JARVIS MK37
from __future__ import annotations

import re
from typing import List
from context.token_counter import TokenCounter


class ContextCompressor:
    """Compresses context strings to reduce token cost while preserving semantic meaning."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove redundant whitespace and empty lines."""
        if not text:
            return ""
        # Collapse multiple blank lines to a single newline
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join([line for line in lines if line])
        return cleaned

    @classmethod
    def compress(cls, text: str, max_tokens: int) -> str:
        """Compress text to fit within target token count."""
        cleaned = cls.clean_text(text)
        current_tokens = TokenCounter.count(cleaned)

        if current_tokens <= max_tokens:
            return cleaned

        # Strategy: Truncate lines from middle or keep head + tail
        lines = cleaned.splitlines()
        if len(lines) <= 4:
            # Short text but long lines: truncate characters
            max_chars = int(max_tokens * 3.5)
            return cleaned[:max_chars] + "\n... [truncated]"

        # Keep first 40% and last 40% of lines
        num_keep = max(2, int(len(lines) * 0.4))
        head = lines[:num_keep]
        tail = lines[-num_keep:]

        summary = f"\n... [{len(lines) - (num_keep * 2)} lines omitted for token optimization] ...\n"
        compressed_text = "\n".join(head) + summary + "\n".join(tail)

        # Safety check
        if TokenCounter.count(compressed_text) > max_tokens:
            max_chars = int(max_tokens * 3.5)
            return compressed_text[:max_chars] + "..."

        return compressed_text
