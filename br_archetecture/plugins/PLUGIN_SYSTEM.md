# 🔌 BR JARVIS — Plugin Platform & Tool Ecosystem (`plugins/` & `tools/`)

> **Document Status**: Production Architecture Specification  
> **Subsystem**: Extensible Plugin Manager & Universal Tool Registry  
> **Module Paths**: `plugins/` and `tools/`  

---

## 1. Executive Summary

BR JARVIS features a modular plugin architecture (`plugins/`) and a centralized tool runtime (`tools/`) managing **90+ specialized tools**. The system supports dynamic tool discovery, sandbox isolation, Model Context Protocol (MCP) server integration, read-only caching via FNV-1a hashing, and strict permission policies.

---

## 2. Plugin & Tool Architecture Topology

```mermaid
graph TD
    Planner[Agent Execution Planner] --> ToolRuntime[ToolRuntimeEngine: tools/tool_runtime.py]
    
    ToolRuntime --> PermissionCheck{PermissionsPolicy Check}
    PermissionCheck -->|Denied| Refuse[PermissionDenied Error]
    
    PermissionCheck -->|Allowed| CacheCheck{Read-Only & Cache Hit?}
    CacheCheck -->|Hit| ReturnCache[Return FNV-1a Hash Cached Result]
    
    CacheCheck -->|Miss| ExecuteTool[Tool Registry Dispatch: tools/registry.py]
    
    ExecuteTool --> StandardTools[Native Tool Modules: pc_tools, excel_tools, file_tools, live_os_tools...]
    ExecuteTool --> MCPConnector[MCP Connector: tools/mcp_connector.py]
    ExecuteTool --> CustomPlugins[External Plugin Modules: plugins/plugin_manager.py]
```

---

## 3. Component Taxonomy

| Module | Component / Class | Responsibility |
|---|---|---|
| [plugins/plugin_manager.py](file:///d:/BRJARVIS/Br-Jarvis/plugins/plugin_manager.py) | `PluginManager` | Dynamic discovery, manifest parsing, isolated module loading, and plugin lifecycle hooks (`on_load`, `on_unload`). |
| [tools/registry.py](file:///d:/BRJARVIS/Br-Jarvis/tools/registry.py) | `@register_tool`, `ToolRegistry` | Decorator-based tool registration engine that automatically generates JSON schemas for LLM tool invocation. |
| [tools/tool_runtime.py](file:///d:/BRJARVIS/Br-Jarvis/tools/tool_runtime.py) | `ToolRuntimeEngine` | High-level execution runtime enforcing permissions, input validation, execution timeouts, error sanitization, and caching. |
| [tools/mcp_connector.py](file:///d:/BRJARVIS/Br-Jarvis/tools/mcp_connector.py) | `MCPConnector` | Adapter layer for connecting external Model Context Protocol (MCP) tool servers. |
| [tools/sandbox.py](file:///d:/BRJARVIS/Br-Jarvis/tools/sandbox.py) | `ToolSandbox` | Execution sandbox for running untrusted shell or code snippets in isolated subprocess containers. |

---

## 4. Native Tool Plugin Modules (90+ Tools)

- **`excel_tools.py`**: Excel report creation, sheet analysis (`analyze_project_to_excel`).
- **`pc_tools.py`**: Windows GUI control, window focus, process killing, system sound control.
- **`file_tools.py` & `workspace_tools.py`**: Workspace directory manipulation, file searches, safe edits.
- **`doc_tools.py`**: PDF, DOCX, and text document extraction and formatting.
- **`live_os_tools.py`**: Hardware metrics, network interfaces, memory usage.
- **`rag_tools.py`**: Vector store indexing, semantic search, document ingestion.
- **`redteam_tools.py`**: Security auditing, prompt injection testing, policy verification.
- **`skills_tools.py`**: Skill manifest loader and variable substitution engine.
