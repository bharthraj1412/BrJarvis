# tests/test_tool_runtime.py — Unit Tests for Priority 7 Tool Runtime Engine
from __future__ import annotations

import pytest
from tools.tool_runtime import ToolRuntimeEngine, get_tool_runtime


@pytest.mark.asyncio
async def test_tool_runtime_registration_and_execution():
    runtime_engine = get_tool_runtime()

    def sample_tool(args: dict) -> str:
        return f"Hello {args.get('name', 'World')}"

    runtime_engine.register_tool(
        name="test_greeting",
        description="Returns greeting",
        handler=sample_tool,
        is_read_only=True,
    )

    result = await runtime_engine.execute_tool_async("test_greeting", {"name": "JARVIS"})
    assert result == "Hello JARVIS"

    # Test caching for read-only tool
    cached_result = await runtime_engine.execute_tool_async("test_greeting", {"name": "JARVIS"})
    assert cached_result == "Hello JARVIS"


def test_tool_runtime_list_tools():
    runtime_engine = get_tool_runtime()
    tools = runtime_engine.list_tools()
    assert isinstance(tools, list)
    assert any(t.name == "test_greeting" for t in tools)
