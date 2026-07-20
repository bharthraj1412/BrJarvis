# nvidia_backend.py — Backward-compatible shim
"""Re-exports NvidiaBackend from the new backends/ package."""
from backends.nvidia import NvidiaBackend  # noqa: F401
