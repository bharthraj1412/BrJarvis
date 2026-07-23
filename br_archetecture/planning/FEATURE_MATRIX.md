# 📊 BR JARVIS — Feature Capability Matrix

> **Document Status**: Production Architecture Specification  
> **Scope**: Implementation Status across Core Subsystems  

---

## Subsystem Capability Matrix

| Subsystem | Feature | Status | Module Path |
|---|---|---|---|
| **Core Runtime** | Zero-Token Intent Engine | ✅ Production | `core/intent_engine.py` |
| **Core Runtime** | Thread-safe DI Container | ✅ Production | `core/di.py` |
| **Core Runtime** | Native C++ FNV-1a Bridge | ✅ Production | `core/native_bridge.py` |
| **Guardian Core** | KillSwitch & Pause Controller | ✅ Production | `guardian/kill_switch.py` |
| **Guardian Core** | SHA-256 Integrity Verification | ✅ Production | `guardian/core.py` |
| **Guardian Core** | Pre-Upgrade Snapshot Manager | ✅ Production | `guardian/snapshot.py` |
| **Guardian Core** | Automated Rollback Engine | ✅ Production | `guardian/rollback.py` |
| **Guardian Core** | Autonomy Audit Log | ✅ Production | `guardian/audit_log.py` |
| **Permissions** | Tiered PathPolicy & Cloud Exclusion | ✅ Production | `permissions.py` |
| **Reflection Engine** | Implicit & Explicit Correction Capture | ✅ Production | `memory/reflection.py` |
| **Lesson Store** | Priority 6 Context Integration | ✅ Production | `memory/lessons.py` |
| **Self-Upgrade Engine** | Blast-Radius ChangeClassifier | ✅ Production | `evolution/classifier.py` |
| **Self-Upgrade Engine** | PatchProposer & ChangeDigest | ✅ Production | `evolution/` |
| **Self-Upgrade Engine** | SandboxRunner Verification | ✅ Production | `evolution/sandbox.py` |
| **Self-Upgrade Engine** | AutoDeployer Pipeline | ✅ Production | `evolution/deployer.py` |
| **Reasoning & Planning** | ReAct CoT Plan Engine | ✅ Production | `reasoning/engine.py` |
| **Workflow Engine** | Durable SQLite DAG Scheduler | ✅ Production | `workflow/engine.py` |
| **Agent Executor** | Parallel Multi-Worker Execution | ✅ Production | `agent/executor.py` |
| **Multi-Agent Orchestra** | 12 Specialized SubAgents | ✅ Production | `multi_agent/subagent.py` |
| **Multi-LLM Router** | Auto-Failover to Gemini | ✅ Production | `router.py` |
| **Backends** | Gemini, Claude, GPT, Ollama, NIM, Mistral | ✅ Production | `backends/` |
| **Context Engine** | Priority Windowing & Compression | ✅ Production | `context/` |
| **Memory Engine** | 4-Tier Volatile/SQLite/Vector Memory | ✅ Production | `memory/` |
| **Computer Control** | PyAutoGUI + Semantic UI Finder | ✅ Production | `computer/` |
| **Vision Engine** | Screen Capture, PyTesseract OCR, DOM Bridge | ✅ Production | `vision/` |
| **Voice Subsystem** | Local Whisper ASR + Neural TTS | ✅ Production | `voice/` |
| **Tool Ecosystem** | 90+ Tools & `@register_tool` | ✅ Production | `tools/` |
| **Context Resolver** | Anaphoric Pronoun & History Resolver | ✅ Production | `orchestrator._resolve_context_references` |
| **Live OS Control** | Visual Action Target Trace (Red Crosshair) | ✅ Production | `actions/live_os_control.py` |
| **Orchestrator** | User Turn WorkingMemory Injection Fix | ✅ Production | `orchestrator.chat()` |

