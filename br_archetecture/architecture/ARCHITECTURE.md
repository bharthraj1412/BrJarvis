# 🏗️ BR JARVIS — Core Architecture & System Topology

> **Document Status**: Production Architecture Specification  
> **Subsystems Covered**: Subsystems 1 to 8 (Core Runtime, Event Bus, Context Engine, Memory Engine, Planner, Executor, Tool Runtime, Plugin Platform)

---

## 1. High-Level Architecture Topology

BR JARVIS operates as a decoupled, asynchronous, event-driven Local AI Operating System. 

```mermaid
graph TD
    User([User Voice / Text Input]) -->|Goal Request| Interface[Dual Interface Layer: CLI / Voice GUI]
    Interface -->|Assemble Context| ContextEngine[Context Engine: Token Accounting & Compression]
    
    ContextEngine -->|System Context| Planner[Autonomous Planner Engine: GoalGraph DAG]
    Planner -->|Assess Risk| RiskInterlock{High Risk Operation?}
    
    RiskInterlock -->|Yes| SafetyApproval[Human-in-the-Loop Approval Interlock]
    RiskInterlock -->|No / Approved| Executor[Parallel Execution Engine: 3 Workers]
    
    Executor -->|Dispatch Step| ToolRuntime[Tool Runtime Engine: Sandboxed Execution]
    ToolRuntime -->|Read-Only Cache Check| MemoryCache[(TTL Cache: FNV-1a Hashing)]
    ToolRuntime -->|Permission Check| Permissions[Permissions Policy: check_permission]
    
    ToolRuntime -->|Execute OS Action| DesktopOS[OS Automation & Hardware Controls]
    
    Executor -->|Publish Telemetry| EventBus[Asynchronous EventBus: Pub/Sub & DLQ]
    EventBus -->|Store Audit| EventStore[(Event Store: events.jsonl)]
    EventBus -->|Update State| UnifiedMemory[Unified Memory Manager: Working, Episodic, RAG]
```

---

## 2. Core Subsystems Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as main_mk37 (CLI)
    participant Core as CoreRuntime
    participant Context as ContextEngine
    participant Planner as PlannerEngine
    participant Executor as ExecutionEngine
    participant Bus as EventBus

    User->>CLI: "/run search AI news | format document"
    CLI->>Core: Get Runtime Context & Container
    CLI->>Context: assemble_system_context(history, goal)
    Context-->>CLI: AssembledContext (Token Budget Validated)
    CLI->>Planner: create_goal_graph(goal, steps)
    Planner->>Bus: Publish "task.plan.created"
    Planner-->>CLI: GoalGraph (DAG Nodes + Risk Assessment)
    CLI->>Executor: execute_graph(graph)
    loop Each DAG Step
        Executor->>Bus: Publish "task.step.start"
        Executor->>Executor: Execute step with tool_resolver
        Executor->>Bus: Publish "task.step.completed"
    end
    Executor-->>CLI: ExecutionReport (Status: SUCCESS)
    CLI-->>User: Present Summary
```

---

## 3. Core Operational Principles

1. **Dependency Injection**: Services register interfaces in `CoreRuntime.container` (`Container`).
2. **Event-Driven Telemetry**: Every state change publishes Pydantic v2 event models on `EventBus`.
3. **Strict Token Budgeting**: Prompts are passed through `ContextEngine` to ensure token counts stay within model limits.
4. **Zero Duplicate Computations**: Read-only tools check `MemoryCache` using fast FNV-1a hashing before invocation.
