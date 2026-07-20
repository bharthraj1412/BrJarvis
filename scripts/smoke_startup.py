"""Non-destructive startup smoke checks for JARVIS MK37.

This script validates core imports and lightweight runtime invariants without
calling external APIs or opening UI windows.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _check(name: str, fn):
    try:
        fn()
        print(f"[PASS] {name}")
        return True
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        return False


def main() -> int:
    root = _repo_root()
    sys.path.insert(0, str(root))

    results: list[bool] = []

    def check_permissions_module():
        from permissions import PERMISSIONS, PermissionMode

        assert PERMISSIONS.mode in (
            PermissionMode.ALLOW_ALL,
            PermissionMode.CONFIRM_ALL,
            PermissionMode.DENY_ALL,
        )
        assert PERMISSIONS.check("web_search") in (True, False)

    def check_router_empty_backend_behavior():
        from router import AgentRouter, AgentProfile

        router = AgentRouter({})
        try:
            router.run(AgentProfile.GEMINI, [], "")
            raise AssertionError("Expected RuntimeError when no backends are configured")
        except RuntimeError as err:
            assert "no backends available" in str(err).lower()

    def check_skills_registry():
        from skills import load_skills

        skills = load_skills()
        assert len(skills) >= 10

    def check_tools_registry():
        from tools.registry import TOOL_SCHEMAS, _import_plugins

        _import_plugins()
        assert len(TOOL_SCHEMAS) >= 30

    def check_scope_json_format():
        scope_path = root / "current_scope.json"
        assert scope_path.exists()
        payload = json.loads(scope_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        assert isinstance(payload.get("permissions", {}), dict)

    checks = [
        ("permissions module", check_permissions_module),
        ("router empty backend behavior", check_router_empty_backend_behavior),
        ("skills registry", check_skills_registry),
        ("tools registry", check_tools_registry),
        ("scope file format", check_scope_json_format),
    ]

    for name, fn in checks:
        results.append(_check(name, fn))

    passed = sum(1 for ok in results if ok)
    total = len(results)
    print(f"\nSmoke summary: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
