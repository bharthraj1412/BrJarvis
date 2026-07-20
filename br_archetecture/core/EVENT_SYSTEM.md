# ⚡ BR JARVIS — Asynchronous Event Bus System (`events/`)

## Overview
BR JARVIS uses an asynchronous Pub/Sub Event Bus for all system communication, telemetry, audit logging, and task lifecycle tracking.

---

## 📢 Event Taxonomy

| Topic Pattern | Event Model | Description |
|---|---|---|
| `system.startup` | `SystemEvent` | System runtime boot & shutdown state |
| `task.plan.created` | `TaskEvent` | Autonomous Planner created a GoalGraph DAG |
| `task.step.start` | `TaskEvent` | ExecutionEngine started a task step |
| `task.step.completed` | `TaskEvent` | ExecutionEngine completed a task step |
| `task.step.failed` | `TaskEvent` | Task step failed |
| `tool.exec.start` | `ToolExecutionEvent` | ToolRuntime started tool invocation |
| `tool.exec.completed` | `ToolExecutionEvent` | ToolRuntime finished tool invocation |
| `audit.action` | `AuditEvent` | Audit record of OS actions |

---

## 📭 Dead-Letter Queue (DLQ) & Persistence
Failed subscriber handlers do not crash the system. Unhandled handler exceptions are moved to the `EventBus` Dead-Letter Queue (`DLQ`) and recorded to `workspace/logs/events.jsonl`.
