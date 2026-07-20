"""Permission policy compatibility layer for JARVIS MK37.

This module keeps the historical top-level ``permissions`` import working for
the integration tests and older skill/tool code. The policy is intentionally
small and conservative:

- ``ALLOW_ALL`` permits every tool except explicit deny-list entries.
- ``CONFIRM_ALL`` only permits tools in ``ALWAYS_ALLOWED``.
- ``DENY_ALL`` blocks everything except explicit allow-list entries.

The default mode is read from ``JARVIS_PERMISSION_MODE`` and falls back to the
``current_scope.json`` permissions block when available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path
from typing import FrozenSet


class PermissionMode(str, Enum):
    ALLOW_ALL = "allow_all"
    CONFIRM_ALL = "confirm_all"
    DENY_ALL = "deny_all"


ALWAYS_ALLOWED: FrozenSet[str] = frozenset(
    {
        "help",
        "status",
        "memory_list",
        "memory_search",
        "file_read",
        "fetch_page",
        "fetch_raw",
        "web_search",
        "open_app",
        "browser_control",
        "keyboard_type",
        "keyboard_hotkey",
        "keyboard_press",
        "cursor_move",
        "cursor_click",
        "mouse_scroll",
        "focus_window",
        "screen_find",
        "screen_click",
        "smart_click",
        "run_code",
        "nmap_scan",
    }
)


def _normalize_mode(value: str | None) -> PermissionMode:
    if not value:
        return PermissionMode.ALLOW_ALL
    try:
        return PermissionMode(value.strip().lower())
    except Exception:
        return PermissionMode.ALLOW_ALL


def _load_scope_defaults() -> dict[str, object]:
    scope_path = Path(__file__).resolve().parent / "current_scope.json"
    if not scope_path.exists():
        return {}
    try:
        with scope_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            permissions = payload.get("permissions", {})
            return permissions if isinstance(permissions, dict) else {}
    except Exception:
        pass
    return {}


@dataclass(slots=True)
class PermissionPolicy:
    mode: PermissionMode = PermissionMode.ALLOW_ALL
    deny_names: FrozenSet[str] = field(default_factory=frozenset)
    allow_names: FrozenSet[str] = field(default_factory=frozenset)

    def check(self, tool_name: str) -> bool:
        name = (tool_name or "").strip()
        if not name:
            return False
        if name in self.deny_names:
            return False
        if self.mode == PermissionMode.ALLOW_ALL:
            return True
        if self.mode == PermissionMode.CONFIRM_ALL:
            return name in ALWAYS_ALLOWED or name in self.allow_names
        if self.mode == PermissionMode.DENY_ALL:
            return name in self.allow_names
        return False


def _build_global_policy() -> PermissionPolicy:
    scope_defaults = _load_scope_defaults()
    env_value = os.environ.get("JARVIS_PERMISSION_MODE")
    env_mode = _normalize_mode(env_value)
    scope_mode = _normalize_mode(scope_defaults.get("mode") if isinstance(scope_defaults.get("mode"), str) else None)
    mode = env_mode if env_value else scope_mode

    deny_tools = scope_defaults.get("deny_tools", [])
    if not isinstance(deny_tools, list):
        deny_tools = []

    allow_tools = scope_defaults.get("allow_tools", [])
    if not isinstance(allow_tools, list):
        allow_tools = []

    return PermissionPolicy(
        mode=mode,
        deny_names=frozenset(str(name) for name in deny_tools),
        allow_names=frozenset(str(name) for name in allow_tools),
    )


PERMISSIONS = _build_global_policy()


def check_permission(tool_name: str, args: dict | None = None) -> bool:
    """Check if tool execution is permitted under global policy."""
    return PERMISSIONS.check(tool_name)

