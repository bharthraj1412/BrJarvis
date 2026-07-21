# nvidia_backend.py — Re-export from backends package for backward compatibility
from backends.nvidia import NvidiaBackend

__all__ = ["NvidiaBackend"]
