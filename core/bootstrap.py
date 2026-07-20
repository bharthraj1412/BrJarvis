from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.runtime import CoreRuntime, get_runtime
from events.bus import EventBus, get_event_bus
from events.types import SystemEvent
from orchestrator import JarvisOrchestrator
from router import AgentRouter, load_available_backends


@dataclass(slots=True)
class AssistantRuntime:
    backends: dict
    router: AgentRouter
    orchestrator: JarvisOrchestrator
    core_runtime: Optional[CoreRuntime] = None
    event_bus: Optional[EventBus] = None


def build_assistant_runtime(*, use_vector_memory: bool = True) -> AssistantRuntime:
    """Create the shared backend/router/orchestrator stack for BR entry points with CoreRuntime & EventBus integration."""
    core_runtime = get_runtime()
    event_bus = get_event_bus()

    backends = load_available_backends()
    router = AgentRouter(backends)
    orchestrator = JarvisOrchestrator(router, use_vector_memory=use_vector_memory)

    # Register components in container
    core_runtime.container.register_instance(AgentRouter, router)
    core_runtime.container.register_instance(JarvisOrchestrator, orchestrator)
    core_runtime.container.register_instance(EventBus, event_bus)

    # Publish system startup event
    event_bus.publish(SystemEvent(topic="system.startup", state="RUNNING", payload={"backends_count": len(backends)}))

    return AssistantRuntime(
        backends=backends,
        router=router,
        orchestrator=orchestrator,
        core_runtime=core_runtime,
        event_bus=event_bus,
    )
