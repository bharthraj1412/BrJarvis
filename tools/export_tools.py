# tools/export_tools.py — JARVIS MK37 Export Tools Plugin
"""
Registers chat log and working memory export tools in the tool registry.
"""
from __future__ import annotations

import json
from tools.registry import register_tool


@register_tool(
    name="export_chat",
    description="Export the current conversation/chat history to a file. Formats: pdf, md (Markdown), html, txt.",
    parameters={
        "type": "object",
        "properties": {
            "format": {"type": "string", "description": "Output file format: 'pdf', 'md', 'html', 'txt' (default: pdf)"},
            "max_turns": {"type": "integer", "description": "Maximum conversation turns to export (default: 100)"},
        },
        "required": ["format"],
    }
)
def tool_export_chat(args: dict) -> str:
    from actions.chat_export import export_chat
    result = export_chat(
        format=args["format"],
        max_turns=args.get("max_turns", 100),
    )
    return json.dumps(result, indent=2, default=str)
