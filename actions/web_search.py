# actions/web_search.py — JARVIS MK37 Web Search (Gemini-Powered)
"""
Web search powered by Gemini's Google Search grounding.
Falls back to DuckDuckGo if grounding is unavailable.
Supports: search, compare, deep research.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _get_gemini():
    from gemini_backend import GeminiBackend
    return GeminiBackend()


def _gemini_search(query: str) -> str:
    """Use Gemini's Google Search grounding for real-time web results."""
    try:
        gemini = _get_gemini()
        return gemini.complete_with_search(
            query=query,
            system="You are a helpful research assistant. Provide accurate, up-to-date information with source citations when available. Be concise and factual."
        )
    except Exception as e:
        print(f"[WebSearch] Gemini grounding failed: {e} — trying DDG")
        return _ddg_search_fmt(query)


def _ddg_search_fmt(query: str, max_results: int = 6) -> str:
    """DuckDuckGo fallback search."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for: {query}"

        lines = [f"Search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            if r.get("title"):   lines.append(f"{i}. {r['title']}")
            if r.get("body"):    lines.append(f"   {r['body'][:200]}")
            if r.get("href"):    lines.append(f"   {r['href']}")
            lines.append("")
        return "\n".join(lines).strip()

    except Exception as e:
        return f"Search unavailable: {e}. Query was: {query}"


def _compare(items: list[str], aspect: str) -> str:
    """Compare multiple items using Gemini."""
    query = f"Compare {', '.join(items)} in terms of {aspect}. Be specific with data and facts."
    return _gemini_search(query)


def web_search(
    parameters:    dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    query  = params.get("query", "").strip()
    mode   = params.get("mode", "search").lower().strip()
    items  = params.get("items", [])
    aspect = params.get("aspect", "general").strip() or "general"

    if not query and not items:
        return "Please provide a search query."

    if items and mode != "compare":
        mode = "compare"

    if player:
        player.write_log(f"[Search] {query or ', '.join(items)}")

    print(f"[WebSearch] 🔍 '{query or items}' mode={mode}")

    try:
        if mode == "compare" and items:
            return _compare(items, aspect)
        return _gemini_search(query)
    except Exception as e:
        return f"Search error: {e}"
