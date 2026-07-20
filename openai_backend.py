# openai_backend.py — Backward-compatible shim
"""Re-exports OpenAIBackend from the new backends/ package."""
from backends.openai_compat import OpenAIBackend  # noqa: F401
