# 📡 BR JARVIS — Asynchronous Event Bus & Telemetry (`events/`)

> **Document Status**: Production Architecture Specification  
> **Subsystem**: Core Decoupled Event Messaging & Telemetry Audit  
> **Module Path**: `events/`  

---

## 1. Executive Summary

The BR JARVIS **Event System** (`events/`) acts as the central asynchronous communication backbone for the entire AI Operating System. Built with zero tight coupling, it enables components to publish event notifications, record operational audit logs, track execution telemetry, and manage unexpected handler errors via a Dead Letter Queue (DLQ).

---

## 2. Event Topology & Architecture

```mermaid
graph TD
    Publisher[Publisher: Core / Agent / Tools] -->|Publish Event| EventBus[EventBus: events/bus.py]
    
    EventBus -->|Topic Pattern Match| Subscribers[Subscriber Handlers: @subscribe]
    EventBus -->|Persist Audit Log| EventStore[EventStore: workspace/logs/events.jsonl]
    
    Subscribers -->|Execution Success| LogComplete[Telemetry Logged]
    Subscribers -->|Handler Exception| DLQ[Dead-Letter Queue: retry & error inspection]
```

---

## 3. Component Taxonomy

| File | Class / Entity | Responsibility |
|---|---|---|
| [bus.py](file:///d:/BRJARVIS/Br-Jarvis/events/bus.py) | `EventBus` | Thread-safe, async Pub/Sub event dispatcher supporting wildcard topic subscriptions (e.g. `task.*`, `system.error`). Includes Dead Letter Queue management. |
| [handlers.py](file:///d:/BRJARVIS/Br-Jarvis/events/handlers.py) | `@subscribe` | Decorator framework for registering synchronous and asynchronous subscriber functions. |
| [store.py](file:///d:/BRJARVIS/Br-Jarvis/events/store.py) | `EventStore` | High-throughput append-only JSONL persistent store logging system telemetry to `events.jsonl`. |
| [types.py](file:///d:/BRJARVIS/Br-Jarvis/events/types.py) | `Event`, `EventType` | Enums and Pydantic v2 schemas defining event payloads across system lifecycle, tasks, tools, errors, and security audits. |

---

## 4. Standard Event Types

- `SYSTEM_STARTUP` / `SYSTEM_SHUTDOWN`: Lifecycle lifecycle state changes.
- `TASK_CREATED` / `TASK_COMPLETED` / `TASK_FAILED`: Workflow DAG execution events.
- `TOOL_INVOKED` / `TOOL_SUCCESS` / `TOOL_ERROR`: Tool runtime execution metrics.
- `SECURITY_ALERT` / `PERMISSION_DENIED`: Audit trails for permission violations and redteam checks.
