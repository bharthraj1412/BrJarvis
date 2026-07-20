# backends/__init__.py — JARVIS MK37 Backend Package
"""
Unified AI backend package. Auto-discovers and exports all backend classes.
"""
from __future__ import annotations

from backends.base import BaseBackend
from backends.gemini import GeminiBackend
from backends.openai_compat import OpenAIBackend
from backends.anthropic import ClaudeBackend
from backends.ollama import OllamaBackend
from backends.nvidia import NvidiaBackend
from backends.mistral import MistralBackend

__all__ = [
    "BaseBackend",
    "GeminiBackend",
    "OpenAIBackend",
    "ClaudeBackend",
    "OllamaBackend",
    "NvidiaBackend",
    "MistralBackend",
]
