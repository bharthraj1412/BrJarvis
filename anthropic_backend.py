# anthropic_backend.py — Backward-compatible shim
"""Re-exports ClaudeBackend from the new backends/ package."""
from backends.anthropic import ClaudeBackend  # noqa: F401
