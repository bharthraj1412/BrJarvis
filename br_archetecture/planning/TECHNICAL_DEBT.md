# 🛠️ BR JARVIS — Technical Debt & Refactoring Roadmap

## Resolved Technical Debt
1. **Ad-Hoc Settings**: Replaced dictionary-based settings in `config/models.py` with Pydantic v2 `BaseSettings` (`core/config.py`).
2. **Synchronous Tool Executions**: Wrapped synchronous tool handlers into safe asyncio threadpool tasks (`tools/tool_runtime.py`).
3. **Deprecation Warnings**: Updated `asyncio.iscoroutinefunction` calls to `inspect.iscoroutinefunction` for Python 3.14+ compatibility.
4. **Legacy Tool Registries**: Unified decorator tool registrations in `tools/registry.py` to automatically register with `ToolRuntimeEngine`.
5. **Root-level Orphans**: Removed 7 unused/redundant backend script stubs and scratch script files from root directory.

## Remaining Refactoring Opportunities
1. **Model Router Cache Integration**: Connect `AgentRouter` directly to the `MemoryCache` to cache repeated deterministic queries.
2. **C Native Compilation**: Ensure precompiled binaries (`jarvis_native.dll`) build automatically during `setup.py` across Linux/macOS.
