# tools/registry.py — JARVIS MK37 Universal Tool Registry
"""
Universal tool registry and executor for JARVIS MK37.
Uses a decorator-based plugin system to register and execute tools.
"""
from __future__ import annotations

import asyncio
import json
import traceback
import sys
import importlib
from pathlib import Path
from typing import Callable, Any

# Ensure project root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Global registry mappings
TOOL_SCHEMAS: list[dict] = []
TOOL_REGISTRY: dict[str, Callable[[dict], Any]] = {}

# Cache references
_orchestrator_ref: Any = None


def register_tool(name: str, description: str, parameters: dict | None = None) -> Callable:
    """Decorator to register a tool function in the JARVIS registry."""
    def decorator(func: Callable[[dict], Any]) -> Callable[[dict], Any]:
        schema = {
            "name": name,
            "description": description,
            "parameters": parameters or {}
        }
        # Avoid duplicate schemas
        if not any(s["name"] == name for s in TOOL_SCHEMAS):
            TOOL_SCHEMAS.append(schema)
        TOOL_REGISTRY[name] = func

        # Also register in the unified ToolRuntimeEngine
        try:
            from tools.tool_runtime import get_tool_runtime
            get_tool_runtime().register_tool(
                name=name,
                description=description,
                handler=func,
                parameters=parameters
            )
        except Exception:
            pass

        return func
    return decorator


def _run_async(coro):
    """
    Helper to run asynchronous coroutines safely, even inside a running loop.
    Falls back to run_coroutine_threadsafe if an event loop is already running.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        import concurrent.futures
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=30)
    else:
        return asyncio.run(coro)


def get_tool_prompt_block() -> str:
    """Generate the system prompt block defining all available tools."""
    schema_text = json.dumps(TOOL_SCHEMAS, indent=2)
    return f"""
## Available Tools

To use a tool, output EXACTLY this JSON block on its own line:

```tool_call
{{"tool": "<tool_name>", "args": {{<arguments>}}}}
```

After you output a tool_call block, execution pauses while the tool runs.
You will then receive the tool result and can continue.

If you do NOT need a tool, just respond normally with text.
NEVER fabricate tool results. Always call the tool if you need real data.

**AUTO-ALLOW MODE**: All tools execute immediately without confirmation.

### Tool Definitions
{schema_text}
"""


def execute_tool(name: str, args: dict) -> str:
    """Execute a registered tool by name. All errors are caught and returned as strings."""
    # Ensure all plugins are imported/registered
    _import_plugins()

    if name not in TOOL_REGISTRY:
        return f"ERROR: Unknown tool '{name}'"

    try:
        func = TOOL_REGISTRY[name]
        result = func(args)
        if inspect_is_coroutine(result):
            result = _run_async(result)
        return str(result)
    except PermissionError as e:
        return f"SCOPE VIOLATION: {e}"
    except Exception as e:
        tb = traceback.format_exc()
        return f"TOOL ERROR ({name}): {e}\n{tb}"


def inspect_is_coroutine(obj) -> bool:
    """Check if object is a coroutine or future."""
    import inspect
    return inspect.iscoroutine(obj) or asyncio.iscoroutine(obj)


def set_orchestrator_ref(orchestrator: Any):
    """Set global reference to active orchestrator."""
    global _orchestrator_ref
    _orchestrator_ref = orchestrator


def get_orchestrator_ref() -> Any:
    """Get active orchestrator reference."""
    return _orchestrator_ref


def parse_tool_call(text: str) -> tuple[str | None, dict | None]:
    """Parse a tool_call JSON block from LLM output."""
    import re
    
    # 1. Look for ```tool_call ... ``` format
    pattern = r'```tool_call\s*\n\s*(\{.*?\})\s*\n\s*```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            # Clean comments or trailing commas if any
            cleaned_json = re.sub(r'//.*', '', match.group(1))
            data = json.loads(cleaned_json)
            return data.get("tool"), data.get("args", {})
        except json.JSONDecodeError:
            pass

    # 2. Relaxed match for any {"tool": "...", "args": ...} block
    pattern2 = r'(\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{.*?\}\s*\})'
    match2 = re.search(pattern2, text, re.DOTALL)
    if match2:
        try:
            data = json.loads(match2.group(1))
            return data.get("tool"), data.get("args", {})
        except json.JSONDecodeError:
            pass

    return None, None


# Dynamic import list to populate TOOL_REGISTRY
_plugins_loaded = False

def _import_plugins():
    """Import all tool plugin files to register their decorators."""
    global _plugins_loaded
    if _plugins_loaded:
        return

    plugins = [
        "tools.web_tools",
        "tools.file_tools",
        "tools.code_tools",
        "tools.pc_tools",
        "tools.memory_tools",
        "tools.agent_tools",
        "tools.redteam_tools",
        "tools.system_tools",
        "tools.skills_tools",
        "tools.legacy_actions_tools",
        "actions.clipboard_history",
        "actions.scheduler",
        "actions.email_assistant",
        "tools.image_tools",
        "tools.video_tools",
        "tools.rag_tools",
        "tools.transcription_tools",
        "tools.custom_command_tools",
        "tools.export_tools",
        "tools.live_os_tools",
        "tools.excel_tools",
        "tools.process_tools",
        "tools.audit_tools",
    ]

    for p in plugins:
        try:
            importlib.import_module(p)
        except Exception as e:
            print(f"[JARVIS] Tool Plugin Error: Failed to load '{p}' — {e}")
            traceback.print_exc()

    # Load custom plugins
    try:
        from plugins import load_custom_plugins
        load_custom_plugins()
    except Exception as e:
        print(f"[JARVIS] Custom plugins loader warning: {e}")

    _plugins_loaded = True


def get_tool_prompt_block() -> str:
    """Return JSON string formatted block of all tool schemas."""
    _import_plugins()
    return json.dumps(TOOL_SCHEMAS, indent=2)


def get_pruned_tool_prompt_block(user_prompt: str = "") -> str:
    """
    Antigravity Dynamic Tool Signature Pruning.
    Filters the tool registry so only tools relevant to the user prompt are included in system instructions.
    Reduces system prompt size by ~85%!
    """
    _import_plugins()
    if not TOOL_SCHEMAS:
        return ""

    if not user_prompt:
        selected = TOOL_SCHEMAS[:6]
    else:
        prompt_lower = user_prompt.lower()
        selected = []
        for schema in TOOL_SCHEMAS:
            name = schema["name"].lower()
            desc = schema["description"].lower()
            name_parts = name.split("_")
            if any(part in prompt_lower for part in name_parts if len(part) > 2) or any(w in desc for w in prompt_lower.split() if len(w) > 4):
                selected.append(schema)

        if len(selected) < 3:
            selected = TOOL_SCHEMAS[:6]

    formatted_tools = []
    for s in selected:
        formatted_tools.append(f"- **{s['name']}**: {s['description']}")

    return "### Relevant Tools:\n" + "\n".join(formatted_tools)

