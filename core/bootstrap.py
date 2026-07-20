from __future__ import annotations

from dataclasses import dataclass

from orchestrator import JarvisOrchestrator
from router import AgentRouter, load_available_backends


@dataclass(slots=True)
class AssistantRuntime:
    backends: dict
    router: AgentRouter
    orchestrator: JarvisOrchestrator


def build_assistant_runtime(*, use_vector_memory: bool = True) -> AssistantRuntime:
    """Create the shared backend/router/orchestrator stack for BR entry points."""
    backends = load_available_backends()
    router = AgentRouter(backends)
    orchestrator = JarvisOrchestrator(router, use_vector_memory=use_vector_memory)
    return AssistantRuntime(backends=backends, router=router, orchestrator=orchestrator)
