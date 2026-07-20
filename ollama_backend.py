# ollama_backend.py — Backward-compatible shim
"""Re-exports OllamaBackend from the new backends/ package."""
from backends.ollama import OllamaBackend  # noqa: F401
