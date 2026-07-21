# anthropic_backend.py — Re-export from backends package for backward compatibility
from backends.anthropic import ClaudeBackend, AnthropicBackend

__all__ = ["ClaudeBackend", "AnthropicBackend"]
