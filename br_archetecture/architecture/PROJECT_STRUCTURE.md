# 📁 BR JARVIS — Project Structure & Module Responsibilities

```
BrJarvis/
├── guardian/                    # Guardian Safety & Recovery Core
│   ├── core.py                  # Master Guardian core, SHA-256 integrity & kill switch check
│   ├── kill_switch.py           # Pause/Resume execution state controller
│   ├── snapshot.py              # Pre-upgrade SnapshotManager backup & checksum validator
│   ├── rollback.py              # Automated RollbackEngine state recovery
│   └── audit_log.py             # Autonomy audit log persistence
│
├── evolution/                   # Autonomous Self-Upgrade Engine
│   ├── classifier.py            # Blast-radius ChangeClassifier (LOW, MEDIUM, HIGH)
│   ├── proposer.py              # Automated PatchProposer generator
│   ├── sandbox.py               # SandboxRunner execution & isolation validator
│   ├── digest.py                # Architectural ChangeDigest reporter
│   └── deployer.py              # AutoDeployer deployment pipeline
│
├── core/                        # Core Runtime Engine Coordinator & Services
│   ├── bootstrap.py             # System bootstrap & AssistantRuntime backward compatibility
│   ├── config.py                # Pydantic v2 structured settings (JarvisConfig)
│   ├── di.py                    # Thread-safe Dependency Injection Container
│   ├── health.py                # Hardware metrics (CPU/RAM/Disk/Native) & Health checks
│   ├── lifecycle.py             # Async lifecycle manager & OS signal handlers
│   ├── logging.py               # Structured JSON & colorized console logging engine (UTF-8 safe)
│   ├── native_bridge.py         # C/C++ FNV-1a native bridge & fallback wrappers
│   ├── process.py               # Process supervisor & background task runner
│   └── runtime.py               # Unified CoreRuntime coordinator
│
├── reasoning/                   # Advanced Reasoning & Planning Engine
│   ├── __init__.py              # Export interface
│   ├── types.py                 # Data models (TaskNode, PlanGraph, ConfidenceScore, ReasoningTrace)
│   └── engine.py                # ReasoningEngine (CoT ReAct expansion, risk assessment, self-verification)
│
├── workflow/                    # Durable Workflow DAG Scheduler & State Engine
│   ├── __init__.py              # Export interface
│   ├── dag.py                   # WorkflowDAG graph validation & cycle detection
│   ├── scheduler.py             # TaskScheduler (time & interval recurring triggers)
│   └── engine.py                # WorkflowEngine (Durable state persistence in SQLite workflows.db)
│
├── vision/                      # High-Speed Screen Capture & OCR Engine
│   ├── __init__.py              # Export interface
│   ├── engine.py                # VisionEngine master coordinator
│   ├── ocr_engine.py            # OCREngine with SHA-256 LRU caching & PyTesseract bbox extraction
│   ├── screen_analyst.py        # ScreenAnalyst multi-monitor capture & FNV-1a frame hashing
│   └── types.py                 # Pydantic v2 screen report schemas
│
├── computer/                    # Human-Level Computer Operator Subsystem
│   ├── __init__.py              # Export interface
│   ├── operator.py              # ComputerOperator with PyAutoGUI failsafes, win32 window focus & verification
│   └── types.py                 # ComputerAction and ActionResult schemas
│
├── backends/                    # Unified Multi-LLM Provider Engine
│   ├── base.py                  # BaseBackend abstract interface
│   ├── gemini.py                # Primary Gemini backend with grounding & vision
│   ├── anthropic.py             # Anthropic Claude backend (ClaudeBackend / AnthropicBackend alias)
│   ├── openai_compat.py         # OpenAI-compatible proxy backend
│   ├── ollama.py                # Local Ollama private backend
│   ├── nvidia.py                # NVIDIA NIM GPU backend
│   └── mistral.py               # Mistral AI backend
│
├── events/                      # Asynchronous Event Bus & Audit Log
│   ├── bus.py                   # Async Pub/Sub EventBus with DLQ & pattern matching
│   ├── handlers.py              # @subscribe decorator & subscriber registry
│   ├── store.py                 # Persistent Event Store
│   └── types.py                 # Event models (System, Task, Audit, Error, Tool)
│
├── context/                     # Context Engine & Token Budgeting
│   ├── builder.py               # Priority multi-source context assembler
│   ├── compressor.py            # Semantic context compressor
│   ├── engine.py                # Master ContextEngine coordinator
│   └── token_counter.py         # Precise token accounting engine
│
├── memory/                      # Multi-Tier Memory Engine
│   ├── conversation_store.py    # SQLite conversation history database
│   ├── persistent_store.py      # SQLite & Markdown file persistent store
│   ├── vector_store.py          # Vector store (ChromaDB with sentence-transformers fallback)
│   ├── unified_memory.py        # Master UnifiedMemoryManager coordinator
│   └── config_manager.py        # Environment-first API key resolution manager
│
├── agent/                       # Parallel Agent Executor & Planner
│   ├── executor.py              # Parallel AgentExecutor with error recovery
│   ├── planner.py               # Goal decomposition & replanning
│   └── task_queue.py            # Prioritized task queue manager
│
├── multi_agent/                 # SubAgent Orchestra & Task Isolation
│   ├── subagent.py              # 12 SubAgent definitions (coder, reviewer, editor, etc.)
│   └── manager.py               # SubAgentManager & execution context
│
├── tools/                       # Centralized Tool Registry (93 Tool Plugins)
│   ├── registry.py              # Universal decorator-based registry (`@register_tool`)
│   ├── tool_runtime.py          # Universal ToolRuntimeEngine with permissions & caching
│   └── *_tools.py               # 20+ specialized tool plugin modules
│
├── skills/                      # Skill Loader (71 Loaded Skills)
│   ├── loader.py                # Skill discovery and variable substitution
│   └── builtin_*.py             # Built-in editor and automation skills
│
├── voice/                       # Multilingual Voice Subsystem
│   ├── assistant.py             # Hands-free BRVoiceAssistant coordinator with wake-word gating
│   ├── stt.py                   # SounddeviceMicrophone & Google STT fallback
│   ├── whisper_local.py         # Offline OpenAI Whisper local ASR model
│   └── tts.py                   # NeuralTTS & MCI audio player
│
├── web/                         # Glassmorphic Web Dashboard
│   ├── index.html               # Real-time streaming chat dashboard UI
│   ├── style.css                # Custom CSS design tokens & animations
│   └── app.js                   # WebSocket client & streaming renderer
│
├── root shims/                  # Legacy Root Backward Compatibility Shims
│   ├── anthropic_backend.py     # Re-exports backends.anthropic
│   ├── gemini_backend.py        # Re-exports backends.gemini
│   ├── openai_backend.py         # Re-exports backends.openai_compat
│   ├── ollama_backend.py        # Re-exports backends.ollama
│   ├── nvidia_backend.py        # Re-exports backends.nvidia
│   └── mistral_backend.py       # Re-exports backends.mistral
│
├── tests/                       # Verification Suite
│   ├── test_deep_audit.py       # 42 deep audit runtime cross-reference tests (100% pass)
│   └── test_integration.py      # 11 integration test scenarios (100% pass)
│
├── br_archetecture/             # Engineering Knowledge Base
├── healthcheck.py               # Standalone diagnostic report script
├── main_mk37.py                 # Interactive Rich TUI CLI
├── main.py                      # Voice Assistant Entry Point
├── server.py                    # FastAPI Web & WebSocket Server
└── start.py                     # Unified Launcher Menu
```
