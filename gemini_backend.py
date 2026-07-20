# gemini_backend.py — Backward-compatible shim
"""Re-exports GeminiBackend from the new backends/ package."""
from backends.gemini import GeminiBackend  # noqa: F401
