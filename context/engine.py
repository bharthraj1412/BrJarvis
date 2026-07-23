# context/engine.py — Core Context Engine Coordinator for JARVIS MK37
from __future__ import annotations

import logging
from typing import Optional
from context.builder import ContextBuilder
from context.types import AssembledContext, ContextItem, ContextScope, TokenBudget
from core.runtime import get_runtime
from events.bus import get_event_bus
from events.types import BaseEvent

logger = logging.getLogger("JARVIS.ContextEngine")


class ContextEngine:
    """Master Context Engine managing system prompt generation and token-efficient context construction."""

    def __init__(self, default_budget: Optional[TokenBudget] = None):
        self.default_budget: TokenBudget = default_budget or TokenBudget()
        self.runtime = get_runtime()
        self.event_bus = get_event_bus()

        # Register self in DI container
        self.runtime.container.register_instance(ContextEngine, self)
        logger.info("⚡ ContextEngine initialized")

    def create_builder(
        self,
        max_tokens: Optional[int] = None,
        profile: Optional[Any] = None
    ) -> ContextBuilder:
        """Create a ContextBuilder with optional token budget or profile override."""
        if profile:
            profile_str = profile.value if hasattr(profile, "value") else str(profile)
            budget = TokenBudget.from_profile(profile_str)
            if max_tokens is not None:
                budget.max_tokens = max_tokens
        elif max_tokens is not None:
            budget = TokenBudget(max_tokens=max_tokens)
        else:
            budget = self.default_budget
        return ContextBuilder(budget=budget)

    def assemble_system_context(
        self,
        conversation_history: Optional[list] = None,
        active_goal: Optional[str] = None,
        max_tokens: Optional[int] = None,
        profile: Optional[Any] = None,
    ) -> AssembledContext:
        """Convenience method to construct full system context payload."""
        builder = self.create_builder(max_tokens=max_tokens, profile=profile)

        # 1. System Health & Hardware State
        report = self.runtime.health.generate_report()
        sys_info = (
            f"Assistant: {self.runtime.config.assistant.name} | "
            f"CPU: {report.hardware.cpu_percent:.1f}% | "
            f"RAM: {report.hardware.memory_used_percent:.1f}% | "
            f"Status: {report.overall_status}"
        )
        builder.add_item(ContextItem(
            scope=ContextScope.SYSTEM_STATE,
            title="System Environment",
            content=sys_info,
            priority=10
        ))

        # 2. Active Goal Context
        if active_goal:
            builder.add_item(ContextItem(
                scope=ContextScope.CONVERSATION,
                title="Active Task Goal",
                content=active_goal,
                priority=9
            ))

        # 3. Conversation History
        if conversation_history:
            recent_turns = conversation_history[-6:]
            conv_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in recent_turns])
            builder.add_item(ContextItem(
                scope=ContextScope.CONVERSATION,
                title="Recent Conversation History",
                content=conv_str,
                priority=8
            ))

        return builder.assemble()


_global_context_engine: Optional[ContextEngine] = None


def get_context_engine() -> ContextEngine:
    global _global_context_engine
    if _global_context_engine is None:
        _global_context_engine = ContextEngine()
    return _global_context_engine
