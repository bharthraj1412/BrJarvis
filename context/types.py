# context/types.py — Pydantic v2 Data Models for JARVIS MK37 Context Engine
from __future__ import annotations

import enum
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextScope(str, enum.Enum):
    SYSTEM_STATE = "SYSTEM_STATE"
    CONVERSATION = "CONVERSATION"
    ACTIVE_WINDOW = "ACTIVE_WINDOW"
    CLIPBOARD = "CLIPBOARD"
    MEMORY = "MEMORY"
    PROJECT_FILES = "PROJECT_FILES"
    USER_PREFERENCES = "USER_PREFERENCES"


class ContextItem(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scope: ContextScope
    title: str
    content: str
    token_count: int = 0
    priority: int = Field(default=5, ge=1, le=10, description="Priority scale 1 (lowest) to 10 (highest)")
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TokenBudget(BaseModel):
    max_tokens: int = Field(default=8192, description="Maximum total tokens allowed for prompt context")
    reserve_response_tokens: int = Field(default=2048, description="Reserved tokens for AI output generation")

    @property
    def available_context_tokens(self) -> int:
        return max(500, self.max_tokens - self.reserve_response_tokens)


class AssembledContext(BaseModel):
    system_prompt: str
    context_str: str
    items: List[ContextItem] = Field(default_factory=list)
    total_tokens: int = 0
    budget: TokenBudget
    budget_used_percent: float = 0.0
