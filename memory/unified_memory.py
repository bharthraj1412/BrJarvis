# memory/unified_memory.py — Master Multi-Tier Memory Coordinator for JARVIS MK37
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from core.runtime import get_runtime
from events.bus import get_event_bus
from memory.archiver import MemoryArchiver
from memory.cache import MemoryCache
from memory.working import WorkingMemory
from memory.persistent_store import MemoryEntry, save_memory, search_memory, delete_memory, load_index
from memory.vector_store import VectorMemory
from memory.conversation_store import ConversationStore
from memory.lessons import LessonStore
from memory.reflection import ReflectionEngine

logger = logging.getLogger("JARVIS.UnifiedMemory")


class UnifiedMemoryManager:
    """
    Master Unified Memory Coordinator bringing together:
      1. Working Memory (Short-term context window)
      2. Persistent Memory (Markdown files + SQLite metadata)
      3. Semantic Vector Memory (ChromaDB / TF-IDF)
      4. Lesson & Reflection Memory (Self-correction learning)
      5. Conversation History (Session/turn history)
      6. Result Cache (Tool call caching with TTL)
    """

    def __init__(self):
        self.working = WorkingMemory(max_tokens=100000)
        self.cache = MemoryCache(default_ttl=300.0)
        self.archiver = MemoryArchiver(max_age_days=30)
        self.vector = VectorMemory()
        self.conversations = ConversationStore()
        self.lessons = LessonStore()
        self.reflection = ReflectionEngine(self.lessons)

        self.runtime = get_runtime()
        self.event_bus = get_event_bus()

        # Register self in DI Container
        self.runtime.container.register_instance(UnifiedMemoryManager, self)
        logger.info("⚡ UnifiedMemoryManager fully initialized across 6 memory tiers")

    # ── Tier 1: Working Memory ─────────────────────────────────────────────

    def add_interaction(self, role: str, content: str) -> None:
        """Add turn to active working memory."""
        self.working.add(role, content)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retrieve active conversation history."""
        return self.working.get()

    def add_user_message(self, content: str) -> None:
        """Add user message to active working memory."""
        self.add_interaction("user", content)

    def add_assistant_message(self, content: str) -> None:
        """Add assistant message to active working memory."""
        self.add_interaction("assistant", content)

    # ── Tier 2: Persistent & Semantic Vector Memory ──────────────────────

    def remember(
        self,
        name: str,
        content: str,
        description: str = "",
        mem_type: str = "user",
        scope: str = "user",
        confidence: float = 1.0,
    ) -> MemoryEntry:
        """Save a new memory entry across persistent storage and vector index."""
        from datetime import datetime
        entry = MemoryEntry(
            name=name,
            description=description or name,
            type=mem_type,
            content=content,
            created=datetime.now().strftime("%Y-%m-%d"),
            scope=scope,
            confidence=confidence,
            source="user",
        )
        save_memory(entry, scope=scope)
        self.vector.store(text=f"{name}: {content}", metadata={"name": name, "type": mem_type})
        logger.info(f"💾 Unified Memory saved: [{scope}] {name}")
        return entry

    def forget(self, name: str, scope: str = "user") -> None:
        """Delete a memory from persistent storage and vector index."""
        delete_memory(name, scope=scope)
        logger.info(f"🗑️ Unified Memory deleted: [{scope}] {name}")

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search all memory tiers for query relevant context."""
        results = []

        # 1. Search Persistent Markdown/SQLite memory
        persistent_hits = search_memory(query)
        for p in persistent_hits[:limit]:
            results.append({
                "source": "persistent",
                "name": p.name,
                "description": p.description,
                "content": p.content,
                "type": p.type,
                "confidence": p.confidence,
            })

        # 2. Search Vector store
        vector_hits = self.vector.recall(query, n=limit)
        for v_text in vector_hits:
            if not any(r["content"] in v_text for r in results):
                results.append({
                    "source": "vector",
                    "name": "Semantic Vector Memory",
                    "content": v_text,
                    "confidence": 0.85,
                })

        # 3. Search Lesson store
        lesson_hits = self.lessons.get_relevant_lessons(query, limit=3)
        for l in lesson_hits:
            results.append({
                "source": "lesson",
                "name": f"Lesson: {l['topic']}",
                "content": l['correction'],
                "confidence": 0.9,
            })

        return results[:limit]

    # ── Tier 3: Tool Result Caching ────────────────────────────────────────

    def cache_tool_result(self, tool_name: str, args: Dict[str, Any], result: Any, ttl: Optional[float] = None) -> None:
        """Cache execution result of a tool call."""
        key = f"tool:{tool_name}:{str(args)}"
        self.cache.set(key, result, ttl=ttl)

    def get_cached_tool_result(self, tool_name: str, args: Dict[str, Any]) -> Optional[Any]:
        """Retrieve cached tool execution result if available."""
        key = f"tool:{tool_name}:{str(args)}"
        return self.cache.get(key)

    # ── Tier 4: Lessons & Reflection ──────────────────────────────────────

    def process_turn_reflection(self, user_input: str, previous_output: str, elapsed_sec: float = 0) -> Optional[Dict[str, Any]]:
        """Process turn for automatic self-correction and lesson learning."""
        return self.reflection.process_turn(user_input, previous_output, elapsed_sec)

    # ── Tier 5: Session Consolidation ─────────────────────────────────────

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
