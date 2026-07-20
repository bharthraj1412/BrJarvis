# tools/memory_tools.py — JARVIS MK37 Memory Tools Plugin
"""
Memory control tools plugin for JARVIS MK37.
Exposes storage capabilities via the memory package.
"""
from __future__ import annotations

import math
import time
from datetime import datetime
from tools.registry import register_tool


@register_tool(
    name="memory_save",
    description="Save a persistent memory entry.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string"},
            "description": {"type": "string"},
            "content": {"type": "string"},
            "scope": {"type": "string"},
        },
        "required": ["name", "type", "description", "content"],
    }
)
def tool_memory_save(args: dict) -> str:
    from memory.persistent_store import MemoryEntry, save_memory, check_conflict
    scope = args.get("scope", "user")
    entry = MemoryEntry(
        name=args["name"],
        description=args["description"],
        type=args["type"],
        content=args["content"],
        created=datetime.now().strftime("%Y-%m-%d"),
    )
    conflict = check_conflict(entry, scope=scope)
    save_memory(entry, scope=scope)
    msg = f"Memory saved: '{entry.name}' [{entry.type}/{scope}]"
    if conflict:
        msg += "\n⚠ Replaced conflicting memory."
    return msg


@register_tool(
    name="memory_delete",
    description="Delete a persistent memory entry by name.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "scope": {"type": "string"},
        },
        "required": ["name"],
    }
)
def tool_memory_delete(args: dict) -> str:
    from memory.persistent_store import delete_memory
    delete_memory(args["name"], scope=args.get("scope", "user"))
    return f"Memory deleted: '{args['name']}'"


@register_tool(
    name="memory_search",
    description="Search persistent memories by keyword.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer"},
        },
        "required": ["query"],
    }
)
def tool_memory_search(args: dict) -> str:
    from memory.memory_context import find_relevant_memories
    from memory.persistent_store import touch_last_used
    
    query = args["query"]
    max_results = args.get("max_results", 5)
    results = find_relevant_memories(query, max_results=max_results)
    
    if not results:
        return f"No memories found matching '{query}'."
        
    now = time.time()
    for r in results:
        age_days = max(0, (now - r["mtime_s"]) / 86400)
        r["_rank"] = r.get("confidence", 1.0) * math.exp(-age_days / 30)
        
    results.sort(key=lambda r: r["_rank"], reverse=True)
    results = results[:max_results]
    
    for r in results:
        if r.get("file_path"):
            touch_last_used(r["file_path"])
            
    lines = [f"Found {len(results)} memory/memories for '{query}':", ""]
    for r in results:
        freshness = f"  ⚠ {r['freshness_text']}" if r["freshness_text"] else ""
        lines.append(
            f"[{r['type']}/{r['scope']}] {r['name']}\n"
            f"  {r['description']}\n"
            f"  {r['content'][:200]}{'...' if len(r['content']) > 200 else ''}"
            f"{freshness}"
        )
    return "\n\n".join(lines)


@register_tool(
    name="memory_list",
    description="List all persistent memory entries.",
    parameters={
        "type": "object",
        "properties": {
            "scope": {"type": "string"},
        },
    }
)
def tool_memory_list(args: dict) -> str:
    from memory.persistent_store import load_entries
    scope_filter = args.get("scope", "all")
    scopes = ["user", "project"] if scope_filter == "all" else [scope_filter]
    
    all_entries = []
    for s in scopes:
        all_entries.extend(load_entries(s))
        
    if not all_entries:
        return "No memories stored."
        
    lines = [f"{len(all_entries)} memory/memories:"]
    for e in all_entries:
        tag = f"[{e.type:9s}|{e.scope:7s}]"
        lines.append(f"  {tag} {e.name}")
        if e.description:
            lines.append(f"    {e.description}")
    return "\n".join(lines)
