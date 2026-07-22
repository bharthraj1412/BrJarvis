# 🌌 BR JARVIS (Project BR / JARVIS MK37) — Master Architecture Record & Specification

> **System Identity**: BR JARVIS — Local-First, Multi-Modal Cognitive AI Operating System  
> **Target Platform**: Windows / Linux / macOS  
> **Core Architecture**: Decoupled 15-Subsystem Topology, Async Event-Driven, Multi-Backend Adaptive Routing, Guardian Core & Self-Upgrade Engine  
> **Document Purpose**: Master Architecture Specification & Knowledge Base  
> **Master Location**: [fullproject.md](file:///d:/BRJARVIS/Br-Jarvis/br_archetecture/fullproject.md)

---

## 1. Executive Summary & Vision

**BR JARVIS (Project BR / JARVIS MK37)** is a local-first, multi-modal cognitive AI operating system engineered for hands-free computer control, autonomous multi-step execution, multi-backend LLM routing, high-performance screen vision, autonomous self-improvement, and immutable safety governance.

### 🎯 Core Architectural Principles
- **Guardian Core Immutable Governance (`guardian/`)**: Immutable safety core managing file integrity checks, global kill-switch pauses (`kill_switch.py`), pre-upgrade git & DB snapshots (`snapshot.py`), automated rollbacks (`rollback.py`), and autonomy audit logs (`audit_log.py`).
- **Tiered PathPolicy & Cloud Context Exclusion (`permissions.py`)**: 3-tier file access control enforcing cloud-context exclusions for sensitive OS-critical paths, credential stores, and private key files.
- **Autonomous Self-Upgrade Engine (`evolution/`)**: Blast-radius change classification (LOW, MEDIUM, HIGH), isolated sandbox verification testing, human-in-the-loop change digest, and automated deployment.
- **Reflection & Auto-Correction Engine (`memory/reflection.py`, `memory/lessons.py`)**: Captures implicit and explicit user corrections, storing lessons for Priority 6 insertion into prompt context (`context/builder.py`).
- **Zero-Token Instant Execution**: Deterministic regex action router (`core/intent_engine.py`) executing common system commands in 0ms with zero LLM API token overhead.
- **Heterogeneous Multi-Backend LLM Routing**: Dynamic runtime selection across Gemini 2.5/3.5 Flash, Claude 3.5 Sonnet, GPT-4o, local Ollama Llama3, NVIDIA NIM, and Mistral AI with self-healing failover.
- **Deep Desktop Control & 7-Tier Vision**: OS navigation via PyAutoGUI, Win32 window focus handles, Windows UI Automation accessibility trees, Chrome DevTools Protocol (CDP) DOM trees, PyTesseract OCR bounding boxes, and visual target finders (`computer/semantic_operator.py`).
- **Durable Workflow Execution**: Directed Acyclic Graph (DAG) task decomposition (`agent/planner.py`), ReAct Chain-of-Thought reasoning (`reasoning/engine.py`), risk assessment interlocks, and SQLite workflow state persistence (`workflow/engine.py`).

---

## 2. 15-Subsystem Implementation & Verification Matrix

| Subsystem Component | Scope & Primary Modules | Status | Implementation & Verification Notes |
|---|---|---|---|
| **1. Guardian Core** | `guardian/` (`core.py`, `kill_switch.py`, `snapshot.py`, `rollback.py`, `audit_log.py`, `autonomy_policy.yaml`) | `✅ Production-Verified` | Immutable safety core, kill-switch, snapshot retention, automated rollback, audit ledger |
| **2. Self-Upgrade Engine** | `evolution/` (`proposer.py`, `classifier.py`, `sandbox.py`, `deployer.py`, `digest.py`) | `✅ Production-Verified` | Blast-radius classification, sandbox testing, change digest, auto-deployment |
| **3. Tiered Path Policy** | `permissions.py` (`PathPolicy`, `PathTier`) | `✅ Production-Verified` | 3-tier path policy, cloud context exclusion for critical/secrets files |
| **4. Reflection & Lessons** | `memory/` (`reflection.py`, `lessons.py`) | `✅ Production-Verified` | Implicit/explicit correction capture, Priority 6 context insertion |
| **5. Core Runtime** | `core/` (`intent_engine.py`, `di.py`, `runtime.py`, `config.py`, `lifecycle.py`, `compat.py`, `workspace_engine.py`, `native_bridge.py`, `health.py`, `logging.py`, `process.py`, `retry.py`, `timeouts.py`) | `✅ Production-Verified` | Deterministic intent router, Pydantic v2 settings, DI container, process supervisor, native C++ FNV-1a bridge |
| **6. Reasoning & Planning** | `reasoning/` (`engine.py`, `types.py`) | `✅ Production-Verified` | ReAct Chain-of-Thought expansion, confidence scoring, risk assessment, self-verification loop |
| **7. Durable Workflow Engine** | `workflow/` (`dag.py`, `engine.py`, `scheduler.py`) | `✅ Production-Verified` | SQLite-backed durable DAG graph scheduler (`workflows.db`), cycle detection, interval triggers |
| **8. Autonomous Planner & Executor** | `agent/` (`planner.py`, `executor.py`, `task_queue.py`, `error_handler.py`) | `✅ Production-Verified` | GoalGraph DAG node decomposition, parallel multi-worker execution, priority task queue |
| **9. Multi-Agent Subsystem** | `multi_agent/` (`subagent.py`) | `✅ Production-Verified` | 12 specialized subagent definitions (coder, reviewer, editor, planner, auditor, etc.) |
| **10. Multi-LLM Router & Backends** | `router.py`, `orchestrator.py`, `backends/` (`gemini.py`, `anthropic.py`, `openai_compat.py`, `ollama.py`, `nvidia.py`, `mistral.py`) | `✅ Production-Verified` | Task-aware model routing, dynamic failover to Gemini, FNV-1a cache hit bypass |
| **11. Context Engine** | `context/` (`builder.py`, `compressor.py`, `engine.py`, `token_counter.py`, `token_manager.py`, `types.py`) | `✅ Production-Verified` | Priority multi-source prompt assembly across 8 scopes (including Lessons), tiktoken counting, head/tail compression |
| **12. Multi-Tier Memory Engine** | `memory/` (`working.py`, `conversation_store.py`, `persistent_store.py`, `vector_store.py`, `cache.py`, `consolidator.py`, `archiver.py`, `unified_memory.py`) | `✅ Production-Verified` | 5-tier hybrid storage: Working memory, SQLite conversation database, ChromaDB RAG vector store, LessonStore, FNV-1a TTL cache |
| **13. Computer Operator & Recovery** | `computer/` (`operator.py`, `semantic_operator.py`, `recovery.py`, `types.py`) | `✅ Production-Verified` | PyAutoGUI control, Win32 window focus, semantic visual locator, fault recovery loop |
| **14. Vision Engine & Screen Server** | `vision/` (`engine.py`, `screen_analyst.py`, `ocr_engine.py`, `accessibility.py`, `dom_bridge.py`, `hybrid_pipeline.py`), `screen_server/` | `✅ Production-Verified` | Multi-monitor screen capture, PyTesseract OCR with SHA-256 caching, DOM bridge, hybrid visual pipeline |
| **15. Voice Subsystem** | `voice/` (`assistant.py`, `stt.py`, `whisper_local.py`, `tts.py`, `multilingual.py`) | `✅ Production-Verified` | Hands-free voice loop, wake-word gating, local OpenAI Whisper ASR, Neural TTS, multilingual translation |
