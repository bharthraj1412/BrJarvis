# memory/unified_memory.py — Unified Multi-Tier Memory Coordinator for JARVIS MK37
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from core.runtime import get_runtime
from events.bus import get_event_bus
from memory.archiver import MemoryArchiver
from memory.cache import MemoryCache
from memory.working import WorkingMemory

logger = logging.getLogger("JARVIS.UnifiedMemory")


class UnifiedMemoryManager:
    """Master Unified Memory Coordinator bringing together Working, Episodic, Semantic, Cache, and Vector layers."""

    def __init__(self):
        self.working = WorkingMemory(max_tokens=100000)
        self.cache = MemoryCache(default_ttl=300.0)
        self.archiver = MemoryArchiver(max_age_days=30)
        self.runtime = get_runtime()
        self.event_bus = get_event_bus()

        # Register self in DI Container
        self.runtime.container.register_instance(UnifiedMemoryManager, self)
        logger.info("⚡ UnifiedMemoryManager initialized")

    def add_interaction(self, role: str, content: str) -> None:
        """Add turn to active working memory."""
        self.working.add(role, content)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retrieve active conversation history."""
        return self.working.get()

    def cache_tool_result(self, tool_name: str, args: Dict[str, Any], result: Any, ttl: Optional[float] = None) -> None:
        """Cache execution result of a tool call."""
        key = f"tool:{tool_name}:{str(args)}"
        self.cache.set(key, result, ttl=ttl)

    def get_cached_tool_result(self, tool_name: str, args: Dict[str, Any]) -> Optional[Any]:
        """Retrieve cached tool execution result if available."""
        key = f"tool:{tool_name}:{str(args)}"
        return self.cache.get(key)

    def consolidate(self) -> None:
        """Trigger memory consolidation and archiving."""
        history = self.working.get()
        consolidated = self.archiver.consolidate_history(history, max_keep=40)
        self.working.history = consolidated


_global_unified_memory: Optional[UnifiedMemoryManager] = None


def get_unified_memory() -> UnifiedMemoryManager:
    global _global_unified_memory
    if _global_unified_memory is None:
        _global_unified_memory = UnifiedMemoryManager()
    return _global_unified_memory
