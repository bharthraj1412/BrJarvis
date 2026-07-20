# context/token_counter.py — Token Count Estimator & Accounting Engine for JARVIS MK37
from __future__ import annotations

import logging
from typing import Any, Union

logger = logging.getLogger("JARVIS.TokenCounter")

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
    _encoder = tiktoken.get_encoding("cl100k_base")
except Exception:
    _TIKTOKEN_AVAILABLE = False
    _encoder = None


class TokenCounter:
    """Estimates and counts token consumption with tiktoken or fast char-ratio fallback."""

    @staticmethod
    def count(text: Union[str, Any]) -> int:
        """Calculate token length for a string or object representation."""
        if not text:
            return 0
        if not isinstance(text, str):
            text = str(text)

        if _TIKTOKEN_AVAILABLE and _encoder:
            try:
                return len(_encoder.encode(text))
            except Exception:
                pass

        # Fallback estimation: average 3.8 characters per token for English/Code
        return max(1, int(len(text) / 3.8))

    @staticmethod
    def is_tiktoken_enabled() -> bool:
        return _TIKTOKEN_AVAILABLE
