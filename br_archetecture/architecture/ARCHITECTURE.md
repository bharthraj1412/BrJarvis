# 🏗️ BR JARVIS — Architecture & System Topology Specification

> **Document Status**: Production Architecture Specification  
> **Version**: MK37.25 (Round 24 Voice Upgrades + Round 25 Context Fix)  
> **Coverage**: Subsystems 1 to 15 (Guardian, Self-Upgrade, Tiered Path Policy, Reflection, Core Runtime, Reasoning, Workflow, Autonomous Planner/Executor, Multi-Agent, Multi-LLM Router, Context Engine, Memory Engine, Computer Operator, Vision Engine, Voice Subsystem)

---

## 1. High-Level System Topology

BR JARVIS operates as a decoupled, asynchronous, local-first AI Operating System with a two-tier execution pipeline:

1. **Zero-Token Instant Fast Path**: Immediate 0ms deterministic execution via regex matchers in `core/intent_engine.py` (0 LLM token cost).
2. **ReAct Cognitive Pipeline**: Multi-backend LLM orchestration loop (`orchestrator.py` + `router.py`) with context-aware pronoun resolution, tool execution, memory retrieval, and visual OS control.

```mermaid
graph TD
    User([👤 User Input: Voice / Text / GUI / API]) --> InputRouter{Input Type & Router}

    subgraph FastPath["⚡ Zero-Token Fast Path (0ms, 0 Tokens)"]
        InputRouter -->|Simple Query / System Command| IntentEngine[DeterministicIntentEngine<br/>core/intent_engine.py<br/>50+ Matchers]
        IntentEngine -->|Direct OS Execution| OSExec[OS Native Call / Telemetry]
        OSExec -->|Instant Output| Speaker[TTS / Voice / UI Output]
    end

    subgraph CognitivePath["🧠 Cognitive ReAct Pipeline"]
        InputRouter -->|Complex / Conversational| ContextResolver[_resolve_context_references<br/>Pronoun & History Resolver]
        ContextResolver --> WorkingMemory[Working Memory<br/>memory/working.py<br/>120K Window]
        WorkingMemory --> ReActLoop[ReAct Loop Engine<br/>orchestrator.py<br/>MAX 20 Steps]
        ReActLoop --> ModelRouter[AgentRouter<br/>router.py]
    end

    subgraph LLMBackends["🔀 LLM Backends Tier"]
        ModelRouter --> Gemini[Gemini 2.5 / 3.5 Flash]
        ModelRouter --> Claude[Claude 3.5 Sonnet]
        ModelRouter --> GPT[GPT-4o / OSS 120B]
        ModelRouter --> DeepSeek[DeepSeek R1]
        ModelRouter --> NVIDIA[NVIDIA NIM Llama3]
        ModelRouter --> Ollama[Local Ollama]
    end

    subgraph ExecutionTier["🔧 Execution & Subsystems Tier"]
        ReActLoop -->|Tool Call| ToolRegistry[Tool Registry<br/>tools/registry.py<br/>34 Tool Modules]
        ToolRegistry --> LiveOS[Live OS Controller<br/>actions/live_os_control.py<br/>Red Crosshair Overlay]
        ToolRegistry --> CompOp[Computer Operator<br/>computer/operator.py]
        ToolRegistry --> Vision[Vision Engine<br/>vision/engine.py]
        ToolRegistry --> Memory[Multi-Tier Memory<br/>SQLite + ChromaDB + Markdown]
    end

    ExecutionTier --> Telemetry[EventBus Telemetry<br/>events/bus.py]
```

---

## 2. Conversation & Context Resolution Sequence

```mermaid
sequenceDiagram
    participant User
    participant Orch as JarvisOrchestrator
    participant ContextResolver as Context Resolver
    participant WM as Working Memory
    participant Router as AgentRouter
    participant Tool as Tool Execution

    User->>Orch: User Input: "open it in brave"
    Orch->>ContextResolver: _resolve_context_references(user_input, augmented)
    ContextResolver->>WM: Scan previous assistant response history for URLs
    WM-->>ContextResolver: Found last URL: "https://google.com/search?q=..."
    ContextResolver->>ContextResolver: Spawn Brave with target URL directly
    ContextResolver-->>Orch: Context-injected prompt: "it refers to https://... - opened in Brave"
    Orch->>WM: add("user", augmented_context)
    Orch->>Router: route() & run()
    Router-->>Orch: Confirmation response
    Orch->>WM: add("assistant", response)
    Orch-->>User: "Opened the previous result in Brave browser, sir."
```

---

## 3. Core Architectural Rules & Standards

1. **Zero-Token First**: Always check `DeterministicIntentEngine` before hitting LLM backends.
2. **Context Integrity**: Every incoming user message MUST be pushed to `WorkingMemory` before any LLM inference step.
3. **Pronoun Traceability**: Anaphoric references ("it", "that", "this") are resolved against previous turn artifacts/URLs before execution.
4. **Visual Action Audit**: Every Live OS click/type action saves a red crosshair visual trace file (`step_{n}_action.png`) for debugging and verification.
5. **Guardian Safety Interlocks**: High-risk system operations check `permissions.py` PathPolicy and `guardian/kill_switch.py`.
