# 📜 BR JARVIS — Architectural Execution Changelog

All major architectural updates, subsystem additions, and core refactorings are recorded in this document.

---

## [37.4.0] — 2026-07-21

### Added & Upgraded
- **Reasoning Engine Subsystem (`reasoning/`)**:
  - Implemented `reasoning/types.py` data models (`TaskNode`, `PlanGraph`, `ConfidenceScore`, `ReasoningTrace`).
  - Implemented `reasoning/engine.py` master `ReasoningEngine` with Chain-of-Thought (CoT) ReAct expansion, risk confidence scoring, and self-verification trace checks.

- **Workflow Engine Subsystem (`workflow/`)**:
  - Implemented `workflow/dag.py` `WorkflowDAG` graph with dependency tracking and cycle detection.
  - Implemented `workflow/scheduler.py` background `TaskScheduler` supporting time/interval triggers.
  - Implemented `workflow/engine.py` durable `WorkflowEngine` managing state transitions (`PENDING`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`) with SQLite state persistence (`workflows.db`).

- **Vision Engine Subsystem Upgrades (`vision/`)**:
  - Upgraded `vision/ocr_engine.py` with LRU caching, SHA-256 frame hash check, and PyTesseract bounding box extractions with clean fallback.
  - Upgraded `vision/screen_analyst.py` with multi-monitor selection (`get_monitors()`) and FNV-1a frame hashing.
  - Upgraded `vision/engine.py` with multi-monitor analysis and `vision.screen.analyzed` event publishing.

- **Computer Operator Subsystem Upgrades (`computer/`)**:
  - Upgraded `computer/operator.py` with PyAutoGUI mouse-corner security failsafes (`pyautogui.FAILSAFE = True`), async execution wrapper (`async_execute_action`), native win32 window focus matching, and action verification.

- **Voice Engine & Router Upgrades (`voice/`, `router.py`)**:
  - Upgraded `voice/stt.py` & `voice/whisper_local.py` for offline speech recognition.
  - Upgraded `voice/assistant.py` with wake-word gating and vocabulary correction.
  - Upgraded `router.py` adaptive complexity routing and token budgeting.

- **Backward Compatibility & Logging Resilience**:
  - Re-created 6 root backend compatibility shims (`anthropic_backend.py`, `gemini_backend.py`, `openai_backend.py`, `ollama_backend.py`, `nvidia_backend.py`, `mistral_backend.py`).
  - Fixed Windows standard stream logging encoding (`cp1252` `UnicodeEncodeError`) in `core/logging.py`.
  - Audited `actions/` modules to check `os.environ` (`GEMINI_API_KEY` / `GOOGLE_API_KEY`) before reading JSON configuration files.

- **Verification Results**:
  - 42/42 Deep Audit tests passing (`python test_deep_audit.py`).
  - 11/11 Integration tests passing (`python test_integration.py`).
  - 5/5 Startup Smoke checks passing (`python scripts/smoke_startup.py`).

---

## [37.3.0] — 2026-07-20

### Added
- **Subsystem 1: Core Runtime Engine (`core/`)**
  - Implemented `core/config.py` using Pydantic v2 `BaseSettings`.
  - Implemented `core/logging.py` with structured JSON & console formatting.
  - Implemented `core/di.py` for thread-safe Dependency Injection.
  - Implemented `core/lifecycle.py` for async startup & shutdown signal management.
  - Implemented `core/process.py` for background process supervision.
  - Implemented `core/health.py` for hardware metrics & service health checks.
  - Implemented `core/runtime.py` coordinator.

- **Subsystem 2: Asynchronous Event Bus (`events/`)**
  - Implemented `events/types.py` Pydantic v2 event models.
  - Implemented `events/bus.py` with Pub/Sub wildcard routing & Dead Letter Queue (DLQ).
  - Implemented `events/store.py` for event persistence & audit replay.
  - Implemented `events/handlers.py` with `@subscribe` decorator.

- **Subsystem 3: Context Engine (`context/`)**
  - Implemented `context/token_counter.py` for precise token accounting.
  - Implemented `context/compressor.py` for semantic context compression.
  - Implemented `context/builder.py` for priority multi-source context assembly.
  - Implemented `context/engine.py` coordinator.

- **Subsystem 4: Advanced Memory Engine (`memory/`)**
  - Implemented `memory/cache.py` with fast FNV-1a frame hashing & TTL decay.
  - Implemented `memory/archiver.py` for memory aging & disk JSONL archiving.
  - Implemented `memory/unified_memory.py` coordinator.

- **Subsystem 5: Autonomous Planner Engine (`agent/planner_engine.py`)**
  - Implemented `GoalGraph` DAG goal decomposition.
  - Implemented risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and approval interlocks.
  - Implemented dynamic failure replanning (`replan_failed_step()`).

- **Subsystem 6: Parallel Execution Engine (`agent/executor_engine.py`)**
  - Implemented multi-worker parallel task execution engine with emergency stop `cancel_all()`.

- **Subsystem 7: Tool Runtime Engine (`tools/tool_runtime.py`)**
  - Implemented universal `ToolRuntimeEngine` with sandboxed execution, permissions interlock (`permissions.py`), result caching for read-only tools, and event telemetry.

- **Subsystem 8: Plugin Runtime Platform (`plugins/plugin_manager.py`)**
  - Implemented dynamic `PluginManager` supporting community plugin discovery (`plugin.json`), lifecycle hooks (`on_load`), capability tool registration, and crash isolation.

- **Subsystem 9: Vision Engine (`vision/`)**
  - Implemented `vision/types.py` Pydantic v2 data models.
  - Implemented `vision/screen_analyst.py` high-speed frame capture with FNV-1a frame hashing.
  - Implemented `vision/ocr_engine.py` OCR text extractor and UI element locator.
  - Implemented `vision/engine.py` master coordinator.

- **Subsystem 10: Computer Operator (`computer/`)**
  - Implemented `computer/types.py` Pydantic v2 action schemas.
  - Implemented `computer/operator.py` desktop automation controller with permissions checking and interlocks.
