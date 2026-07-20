# mistral_backend.py — Backward-compatible shim
"""Re-exports MistralBackend from the new backends/ package."""
from backends.mistral import MistralBackend  # noqa: F401
