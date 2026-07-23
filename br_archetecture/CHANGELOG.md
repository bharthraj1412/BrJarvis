# 📜 BR JARVIS — Architectural Execution Changelog

All major architectural updates, subsystem additions, and core refactorings are recorded in this document.

---

## [37.25.0] — 2026-07-23

### Critical Orchestrator Fix & Context Resolution Engine Upgrade
- **Critical Conversation Context Fix (`orchestrator.chat()`)**:
  - Resolved major conversation memory loss bug where the user message `augmented` string was constructed but never inserted into `WorkingMemory` prior to backend inference calls.
  - Re-established turn recording (`_record_turn("user", user_input)`) before starting the ReAct execution loop.

- **Context-Aware Pronoun & Browser Resolver (`orchestrator._resolve_context_references()`)**:
  - Implemented automatic anaphoric pronoun resolution for queries like `"open it in brave"`, `"open this in chrome"`, or `"show in edge"`.
  - Scans working memory history for recent output URLs (e.g. weather search URLs, RAG search URLs), directly launching the target browser (Brave, Chrome, Edge, Firefox) with the resolved URL.

- **Live OS Vision Target Trace Overlay (`actions/live_os_control.py`)**:
  - Implemented `_save_action_visualization()` drawing a red crosshair and target action footprint directly on target coordinates `(px_x, px_y)` for every executed step action.
  - Saves visual traces to `BR_WORKSPACE/Logs/live_os/step_{step}_action.png`.
  - Integrated dynamic `is_static` frame hash check to alert the vision model when click actions produce no screen change.

- **Zero-Token Intent Engine Expansion (Rounds 8–24)**:
  - Expanded `DeterministicIntentEngine` in `core/intent_engine.py` to 50+ instant 0-token matchers (Git branch, commit log, largest Python file, RAM free / garbage collection, battery, CPU frequency, disk partitions, swap memory, PATH environment, etc.).
  - Added `"brave"` and `"firefox"` to `APP_MAPPINGS` in `intent_engine.py` and `open_app.py`.

---

## [37.6.0] — 2026-07-22

### Verified & Synchronized — Full Architecture Audit & System Alignment
- **Full Codebase Audit & Verification**:
  - Conducted complete repository audit across all 15 architectural subsystems (`core/`, `guardian/`, `evolution/`, `reasoning/`, `workflow/`, `agent/`, `multi_agent/`, `router.py`, `context/`, `memory/`, `computer/`, `vision/`, `voice/`, `tools/`, `events/`).
  - Fixed `ActionType` enum compatibility (`WINDOW_FOCUS`, `APP_FOCUS`) and control flow in `computer/operator.py`.
  - Fixed test mock frame inputs in `tests/test_vision_engine.py`.
  - Achieved **58/58 PASS (100% green)** in PyTest test suite and **42/42 PASS (100% green)** in Deep Audit test suite.

- **Architecture Knowledge Base Synchronization (`br_archetecture/`)**:
  - Updated `br_archetecture/full_repository_audit.md` with complete subsystem audit matrices and test metrics.
  - Updated `br_archetecture/README.md`, `br_archetecture/fullproject.md`, `br_archetecture/planning/FEATURE_MATRIX.md`, `br_archetecture/planning/TECHNICAL_DEBT.md`, and `br_archetecture/architecture/PROJECT_STRUCTURE.md`.

---

## [37.5.0] — 2026-07-21

### Added & Upgraded — Next-Gen Semantic Desktop & Hybrid Vision OS
- **Semantic UI Graph Engine (`vision/types.py`, `vision/engine.py`)**:
  - Implemented `UIRole` Enum (`BUTTON`, `TEXTBOX`, `DROPDOWN`, `DIALOG`, `TREE`, `EDITOR`, `BROWSER`, `WINDOW`, `ICON`, `TOOLBAR`, `SIDEBAR`, `TAB`, `TABLE`, etc.).
  - Implemented `SemanticUINode` tracking node ID, role, name, parent-child links, bounding box, states (`is_focused`, `is_enabled`, `is_clickable`), confidence, and source tier.
  - Implemented `SemanticUIGraph` hierarchy DAG with lookup APIs (`find_by_name`, `find_by_role`).

- **Tier 1 Accessibility API Bridge (`vision/accessibility.py`)**:
  - Implemented `AccessibilityBridge` extracting native OS control trees via Windows UI Automation `ctypes` in under 10ms with zero API token cost.

- **Tier 2 Browser DOM Bridge (`vision/dom_bridge.py`)**:
  - Implemented `CDPBridge` connecting to Chrome/Edge DevTools Protocol debugging port (`localhost:9222`) for web page DOM trees.

- **7-Tier Hybrid Vision Pipeline (`vision/hybrid_pipeline.py`)**:
  - Implemented `HybridVisionPipeline` combining Accessibility APIs, DOM trees, and fast local OCR into a unified `SemanticUIGraph`.

- **Vision Engine Telemetry (`vision/engine.py`)**:
  - Updated `VisionEngine` to run screen captures through the hybrid pipeline and publish `screen.understood` & `graph.updated` events onto `EventBus`.

- **Semantic Computer Operator (`computer/semantic_operator.py`)**:
  - Implemented `SemanticComputerOperator` accepting `SemanticTarget` component specifications and resolving dynamic coordinates at action time.

- **Self-Healing & Recovery Engine (`computer/recovery.py`)**:
  - Implemented `SelfHealingEngine` to intercept unexpected dialogs, auto-dismiss popups, reposition targets, and retry actions without failing master workflows.

- **Event System & Test Suite Upgrades (`events/types.py`, `tests/test_semantic_vision.py`)**:
  - Added `VisionEvent` taxonomy models.
  - Implemented `tests/test_semantic_vision.py` unit test suite (6/6 tests passing 100% green).
  - Total Test Coverage: **64/64 PASS** across Semantic Vision (6), Deep Audit (42), Integration (11), and Smoke (5).

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
