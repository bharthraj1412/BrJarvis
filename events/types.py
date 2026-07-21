# events/types.py — Pydantic v2 Event Models for JARVIS MK37
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = Field(..., description="Topic taxonomy e.g. system.startup, task.created")
    timestamp: float = Field(default_factory=time.time)
    correlation_id: str = Field(default="sys-event", description="Tracing/correlation ID")
    source: str = Field(default="system", description="Event emitter component")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event data body")


class SystemEvent(BaseEvent):
    topic: str = "system.notification"
    state: Optional[str] = None


class TaskEvent(BaseEvent):
    topic: str = "task.created"
    task_id: str
    goal: str
    status: str = "pending"


class AuditEvent(BaseEvent):
    topic: str = "audit.action"
    action_type: str
    target: str
    user_confirmed: bool = True


class ErrorEvent(BaseEvent):
    topic: str = "system.error"
    error_message: str
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None


class VoiceEvent(BaseEvent):
    topic: str = "voice.transcript"
    transcript: str
    confidence: float = 1.0
    speaker: str = "user"


class ToolExecutionEvent(BaseEvent):
    topic: str = "tool.exec.start"
    tool_name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    success: Optional[bool] = None
    result: Optional[Any] = None
    duration_ms: Optional[float] = None


class VisionEvent(BaseEvent):
    topic: str = "screen.understood"
    active_window: Optional[str] = None
    nodes_count: int = 0
    verification_success: Optional[bool] = None
