# 📁 BR JARVIS — Project Structure & Module Responsibilities

```
BrJarvis/
├── core/                        # Subsystem Priority 1: Core Runtime Engine
│   ├── bootstrap.py             # System bootstrap & AssistantRuntime backward compatibility
│   ├── config.py                # Pydantic v2 structured settings (JarvisConfig)
│   ├── di.py                    # Thread-safe Dependency Injection Container
│   ├── health.py                # Hardware metrics (CPU/RAM/Disk/Native) & Health checks
│   ├── lifecycle.py             # Async lifecycle manager & OS signal handlers
│   ├── logging.py               # Structured JSON & colorized console logging engine
│   ├── native_bridge.py         # C/C++ FNV-1a native bridge & fallback wrappers
│   ├── process.py               # Process supervisor & background task runner
│   └── runtime.py               # Unified CoreRuntime coordinator
│
├── events/                      # Subsystem Priority 2: Asynchronous Event Bus
│   ├── __init__.py              # Export interface
│   ├── bus.py                   # Async Pub/Sub EventBus with DLQ & pattern matching
│   ├── handlers.py              # @subscribe decorator & subscriber registry
│   ├── store.py                 # In-memory & JSONL persistent Event Store
│   └── types.py                 # Pydantic v2 event models (System, Task, Audit, Error, Tool)
│
├── context/                     # Subsystem Priority 3: Context Engine
│   ├── __init__.py              # Export interface
│   ├── builder.py               # Priority multi-source context assembler
│   ├── compressor.py            # Context compressor & noise reduction
│   ├── engine.py                # Master ContextEngine coordinator
│   ├── token_counter.py         # Token counter & accounting engine
│   └── types.py                 # Pydantic v2 schemas (ContextItem, AssembledContext, TokenBudget)
│
├── memory/                      # Subsystem Priority 4: Advanced Memory Engine
│   ├── __init__.py              # Export interface
│   ├── archiver.py              # Memory aging, consolidation, & JSONL archiver
│   ├── cache.py                 # High-performance TTL Cache with FNV-1a hashing
│   ├── unified_memory.py        # Master UnifiedMemoryManager coordinator
│   └── working.py               # Working memory buffer
│
├── agent/                       # Subsystem Priority 5 & 6: Planner & Execution Engines
│   ├── __init__.py              # Export interface
│   ├── executor_engine.py       # ParallelExecutionEngine (3 multi-worker threads)
│   ├── planner_engine.py        # PlannerEngine (DAG GoalGraph decomposition & risk interlocks)
│   └── types.py                 # Pydantic v2 schemas (TaskStepNode, GoalGraph, RiskLevel)
│
├── tools/                       # Subsystem Priority 7: Tool Runtime Engine
│   ├── registry.py              # Legacy tool schemas
│   └── tool_runtime.py          # Universal ToolRuntimeEngine with permissions & caching
│
├── plugins/                     # Subsystem Priority 8: Plugin Runtime Platform
│   ├── __init__.py              # Export interface & backward compatibility wrapper
│   └── plugin_manager.py        # PluginManager dynamic loader & crash isolation
│
├── tests/                       # Subsystem Unit Test Suite
│   ├── test_core_runtime.py     # 6 tests for Core Runtime
│   ├── test_event_bus.py        # 3 tests for Event Bus
│   ├── test_context_engine.py   # 4 tests for Context Engine
│   ├── test_memory_engine.py    # 3 tests for Memory Engine
│   ├── test_planner_engine.py   # 2 tests for Autonomous Planner
│   ├── test_executor_engine.py  # 2 tests for Parallel Execution Engine
│   ├── test_tool_runtime.py     # 2 tests for Tool Runtime Engine
│   └── test_plugin_manager.py   # 1 test for Plugin Manager Platform
│
├── br_archetecture/             # Engineering Knowledge Base (Documentation)
├── main_mk37.py                 # Interactive CLI Entry Point
├── main.py                      # Voice Assistant Entry Point
└── start.py                     # Launcher Menu Entry Point
```
