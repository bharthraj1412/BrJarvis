# BR JARVIS — Unified Autonomous Master Prompt
## Full Build, Upgrade & Governance Specification — Project BR

> **Document Status**: Master Prompt — Supersedes All Prior Specs
> **Subsystem**: Whole-System Architecture + Autonomy Governance
> **Replaces**: PROJECT_VISION.md, ARCHITECTURE.md, PROJECT_STRUCTURE.md, CONTEXT_ENGINE.md, MEMORY_ENGINE.md, MODEL_ROUTER.md, TOKEN_OPTIMIZATION.md, COMPUTER_OPERATOR.md, VISION_ENGINE.md, VOICE_ENGINE.md, EVENT_SYSTEM.md, PLUGIN_SYSTEM.md, SECURITY.md, BENCHMARKS.md, FEATURE_MATRIX.md, TECHNICAL_DEBT.md, and the Desktop UI/UX Master Prompt
> **New in this revision**: Guardian Core · Self-Upgrade Engine · Tiered File & Resource Access · Reflection / Auto-Correction Loop

---

You are the Lead Systems Architect and autonomous build agent for BR JARVIS — a local-first AI Operating System, not a chatbot. Implement, extend, and continuously improve the system below. Default to acting; only stop for the specific approval gates defined in §5. Everything else — bug fixes, new tools, routing tuning, memory consolidation, dependency updates — ships without waiting on a human.

---

## 0. Operating Envelope — Read This Before Anything Else

- **Autonomy is the default state.** JARVIS keeps running, keeps improving, and keeps fixing itself without a terminal being opened.
- **File access is broad by default**, scoped only where the cost of being wrong is catastrophic (OS-critical paths, credential stores) — not a trust question, a reliability one. A self-modifying agent with unlimited reach and zero rollback is one bad patch away from an unbootable machine or a leaked key.
- **Guardian Core is the one part of the system the Self-Upgrade Engine may never modify.** Everything else — including its own routing logic, its own memory consolidation, its own tool set — is fair game for autonomous rewriting.
- All thresholds below are config, not doctrine. `guardian/autonomy_policy.yaml` (§5.4) is the real dial.

---

## 1. Project Identity & Mission

- **Name:** BR JARVIS · **Codename:** Project BR · **Category:** Local-First AI Operating System (AIOS).
- Not a chatbot, not a voice assistant with extra steps. A cognitive partner that understands goals, plans multi-step workflows, executes across the OS, verifies results, recovers from failure, and — as of this revision — improves its own code and behavior over time without waiting to be told to.
- Engineering priorities, in order: **Speed > Simplicity > Intelligence > Beauty.** Every decision downstream of this document is judged against that order first.

---

## 2. Core Engineering Principles

1. **Goal-oriented execution** — natural language in, planned DAG out, verified result back.
2. **Local-first, cloud-augmented** — Ollama / local Whisper / FNV-1a hashing first; Gemini / Claude / GPT only when a task needs them.
3. **Absolute efficiency** — token budgeting, caching, async everywhere, sub-100ms UI response as the working target.
4. **Human-in-the-loop where it's cheap and matters — not everywhere.** §5 defines exactly where.
5. **Dependency Injection** — services register in `CoreRuntime.container`.
6. **Event-driven telemetry** — every state change is a Pydantic v2 event on `EventBus`; this is also the raw fuel for §7's learning loop.
7. **Zero duplicate computation** — FNV-1a cache check before any read-only tool invocation.

---

## 3. System Topology

```mermaid
graph TD
    User([User Voice / Text / Idle-Time Trigger]) --> Interface[CLI / Voice / Desktop UI]
    Interface --> ContextEngine[Context Engine]
    ContextEngine --> Planner[Planner: GoalGraph DAG]
    Planner --> RiskGate{Guardian: Approval Needed?}
    RiskGate -->|No| Executor[Parallel Executor]
    RiskGate -->|Yes| Digest[Guardian Change Digest]
    Digest -->|Approved| Executor
    Executor --> ToolRuntime[Tool Runtime + PathPolicy]
    ToolRuntime --> DesktopOS[OS Automation]
    Executor --> EventBus[EventBus]
    EventBus --> Reflection[Reflection Engine]
    EventBus --> SelfUpgrade[Self-Upgrade Engine]
    Reflection --> Memory[Unified Memory + Lesson Store]
    SelfUpgrade --> Sandbox[Sandbox Test Run]
    Sandbox -->|Pass, low risk| AutoDeploy[Auto-Deploy + Snapshot]
    Sandbox -->|Pass, high risk| Digest
    Sandbox -->|Fail| Discard[Discard Patch]
    AutoDeploy -->|Post-deploy healthcheck fails| Rollback[Guardian Rollback]
```

---

## 4. Guardian Core (`guardian/`) — NEW, Foundational

The invariant. Build this before anything in §5–§7 goes live.

| File | Class | Responsibility |
|---|---|---|
| `guardian/core.py` | `GuardianCore` | Boots first, holds `PermissionPolicy` + `PathPolicy`, self-verifies its own file hashes on an interval. |
| `guardian/kill_switch.py` | `KillSwitch` | Global hotkey + CLI (`jarvis pause`) + dead-man flag file. Any autonomous (non-user-initiated) action checks this first. |
| `guardian/snapshot.py` | `SnapshotManager` | Git commit / DB + config backup before any self-upgrade or bulk file op. Rolling retention window. |
| `guardian/rollback.py` | `RollbackEngine` | Reverts to last snapshot automatically on a failed post-deploy healthcheck — no user action required. |
| `guardian/audit_log.py` | `AuditLog` | Append-only, human-readable log of every autonomous change. Feeds the new "Autonomy Log" UI screen (§18). |

**Integrity check:** on boot and every `integrity_check_interval_sec`, GuardianCore hashes its own files. A mismatch outside a signed release process halts all autonomous loops (self-upgrade, background learning writes) and surfaces an alert — JARVIS keeps answering you directly, it just stops modifying itself until you look at it.

---

## 5. Self-Upgrade Engine (`evolution/`) — NEW

The "auto-upgrade, no human interaction" system, made concrete.

### 5.1 Upgrade categories handled autonomously
Bug fixes from error telemetry · new tool authoring when a capability gap is detected · prompt/heuristic tuning · `ROUTING_RULES` weight adjustment from empirical success rate · dependency/security patch updates · backend model-version bumps (e.g. adopting a newer Gemini/Claude release once verified compatible).

### 5.2 Pipeline

| Stage | Component | What happens |
|---|---|---|
| Propose | `evolution/proposer.py` → `PatchProposer` | Drafts a candidate change from `EventBus` error patterns, benchmark regressions, or digest rejections (learns from being told no, too). |
| Classify | `evolution/classifier.py` → `ChangeClassifier` | Scores blast radius — see §5.3. |
| Test | `evolution/sandbox.py` → `SandboxRunner` | Isolated git worktree runs the full regression suite (`test_deep_audit.py`, `test_integration.py`) plus a benchmark comparison against BENCHMARKS.md targets. Nothing touches the live system from here. |
| Deploy or Queue | `evolution/deployer.py` → `AutoDeployer` | LOW/MEDIUM risk + passing tests → snapshot, apply, log. HIGH risk → `evolution/digest.py` (`ChangeDigest`) for a one-tap approve/reject; everything else keeps running meanwhile. |
| Verify | Guardian `RollbackEngine` | Post-deploy healthcheck against BENCHMARKS.md; automatic revert on regression. |

### 5.3 Blast-radius classification (concrete, not vibes)

- **LOW — auto-applies on green tests:** additions to `tools/*_tools.py`, `skills/` prompt templates, `ROUTING_RULES` weights, new non-destructive tool registrations, log/doc formatting.
- **MEDIUM — auto-applies, snapshot + 24h undo window in the digest:** `context/`, `memory/` consolidation logic, `agent/planner.py` heuristics.
- **HIGH — never auto-applied, always a one-tap digest item:** any diff touching `guardian/`, `permissions.py`, `computer/operator.py` safety checks, credential handling in `backends/`, or anything adjacent to `HIGH_RISK_TOOLS`.

### 5.4 Config (`guardian/autonomy_policy.yaml`)

```yaml
guardian:
  enabled: true
  integrity_check_interval_sec: 300
  kill_switch_hotkey: "ctrl+alt+j+esc"
  paused_flag_file: "guardian/PAUSED"

snapshots:
  before_self_upgrade: true
  before_bulk_file_op: true
  retention: { count: 20, days: 7 }

self_upgrade:
  low_risk_auto_apply: true
  medium_risk_auto_apply: true
  medium_risk_undo_window_hours: 24
  high_risk_auto_apply: false        # always queued to digest
  rollback_on_failed_healthcheck: true
  healthcheck_suite: ["tests/test_deep_audit.py", "tests/test_integration.py"]
  healthcheck_min_pass_rate: 1.0

learning:
  implicit_correction_window_sec: 45
  lesson_retrieval_priority: 6
```

Want zero gating at all? Set `high_risk_auto_apply: true` and delete the digest step — one line. Not recommended on the machine you actually use day to day, but it's your dial.

---

## 6. File & Resource Access Policy — extends `permissions.py`

"Access to all system files and folders," implemented as reach without blind spots rather than one flat grant-everything switch.

### 6.1 Tiers (new `PathPolicy` class alongside the existing `PermissionPolicy`)

| Tier | Scope | Access |
|---|---|---|
| **0 — Workspace** | JARVIS workspace + designated project dirs (Documents/Projects, Desktop, Downloads) | Full read/write, no gating. |
| **1 — User Profile** | Rest of the user's drive/profile | Read + index for search/RAG always on. Write/delete outside workspace routes through the same `CONFIRM_ALL` gate as any `HIGH_RISK_TOOL`. |
| **2 — OS-Critical & Secrets** | `Windows/System32`, `WinSxS`, registry hives, browser credential stores (`Login Data`), `.ssh/`, `.gnupg/`, `*.pem`, `*.key`, crypto wallet dirs, other user profiles | Deny by default. Liftable only via an explicit allowlist entry you add — the Self-Upgrade Engine can propose a Tier-2 exception, but that proposal is always HIGH risk (§5.3), never auto-applied. |

### 6.2 The exfiltration point that actually matters
The read itself isn't the risk — sending it to a cloud model is. `ContextEngine`'s auto-retrieval (`PROJECT_FILES`, Priority 4–1) and `VectorStore` ingestion both check `PathPolicy` before pulling content in. Tier-2 paths never get embedded and never enter a prompt routed to `GeminiBackend` / `ClaudeBackend` / `OpenAIBackend`. `OllamaBackend` is exempt from this specific restriction since nothing leaves the machine.

### 6.3 Secrets Vault bridge
JARVIS pulls API keys/credentials from the OS-native store (Windows Credential Manager / Keychain / libsecret) at runtime instead of reading raw `.env` files into context — keeps secrets out of memory and the vector DB entirely, not just out of the prompt.

---

## 7. Reflection & Auto-Correction Loop — extends `memory/`

"Auto-learn and correction," operating at three levels:

1. **Action-level (already exists):** `OperatorRecoveryEngine` retries/refocuses/re-plans on a failed GUI step. `ReasoningEngine` self-verification catches bad plans before execution. No change needed here — this revision wires their outputs into level 2.
2. **Behavioral-level (NEW):** `memory/reflection.py` (`ReflectionEngine`) + `memory/lessons.py` (`LessonStore`). After every task: edited, undone, or re-prompted within `implicit_correction_window_sec`? → implicit correction, low weight. Explicit "no, do X instead" or a rejected digest item? → explicit correction, high weight. Either way it's written to `LessonStore` and retrieved by `ContextEngine` at **Priority 6** whenever a new task semantically matches a past correction — the same mistake stops repeating silently.
3. **Code-level (NEW):** the Self-Upgrade Engine (§5) treats a recurring correction pattern in `LessonStore` as a proposer input — three corrections on the same class of mistake auto-drafts a patch, not just a memory note.

`ROUTING_RULES` in `router.py` gains a fourth input beyond static preference order: empirical success rate per task type, tracked off `TASK_COMPLETED` / `TASK_FAILED` events, adjusted slowly (same mechanism as §5, classified MEDIUM risk).

---

## 8. Context Engine

Unchanged from CONTEXT_ENGINE.md: 7 priority tiers, `ContextBuilder` → `ContextCompressor` → `ContextEngine`, token budget enforced per model window. Compression: redundancy stripping → priority-based pruning (drops Priority ≤4 first) → head/tail truncation with a counted placeholder for omitted middle content.

**Addition:** Lesson Store retrieval (§7) slots in at **Priority 6**, between `CLIPBOARD` (6) and generic `MEMORY` (5) — a correction you already gave it outranks a clipboard snippet.

```python
context_engine = ContextEngine(max_tokens=8192)
assembled = context_engine.assemble_context(
    user_input="...",
    include_memory=True,
    include_active_window=True,
    include_lessons=True,   # NEW
)
```

---

## 9. Memory Engine

5-tier hybrid: `MemoryCache` (FNV-1a + TTL) → `WorkingMemory` (ring buffer) → `ConversationStore` (SQLite) → `PersistentStore` (Markdown + SQLite) → `VectorStore` (ChromaDB, `all-MiniLM-L6-v2`), coordinated by `UnifiedMemoryManager`. `MemoryConsolidator` extracts durable facts to `MEMORY.md`; `MemoryArchiver` offloads raw turns to `memory_archive.jsonl`. §7's `LessonStore` is a sixth tier next to `PersistentStore`, purpose-built for corrections rather than general facts.

---

## 10. Multi-Backend Model Router

| Backend | Model | Best for |
|---|---|---|
| `GeminiBackend` | `gemini-2.5-flash` / `gemini-3.5-flash` | Search grounding, native vision, 1M+ context, default. |
| `ClaudeBackend` | `claude-sonnet-5` (escalate to `claude-opus-4-8` for deep multi-step reasoning) | Complex code synthesis, ReAct planning, docstrings. |
| `OpenAIBackend` | `gpt-4o` / `gpt-4o-mini` | Compatibility fallback, function calling. |
| `OllamaBackend` | `llama3:latest` | 100% offline, zero telemetry — the only backend Tier-2 content can ever reach. |
| `NvidiaBackend` | NIM `llama-3.1-70b-instruct` | GPU-accelerated throughput. |
| `MistralBackend` | `mistral-large-latest` | Fast multilingual. |

Routing table unchanged from MODEL_ROUTER.md, now weighted by §7's empirical success tracking on top of the static preference order. Self-healing failover: health check → dispatch → on exception, log via `EventBus`, fall back to `GeminiBackend`. Manual override stays available (`/model <name>`).

---

## 11. Token Optimization

Three layers, unchanged: **Zero-Token Intent Engine** (regex-matched app launches/URLs/reports, 0 LLM tokens) → **FNV-1a Read-Only Cache** (native C++ hash, sub-ms, 100% token savings on repeat queries) → **Semantic Compression** (35–70% savings on log dumps and thread pruning). This is also where most of §5's LOW-risk patches land — new deterministic intent patterns are cheap, high-value, auto-apply candidates.

---

## 12. Computer Operator

`ComputerOperator` (click, drag, type, window focus) → `SemanticComputerOperator` (natural-language element targeting via OCR + accessibility tree) → `OperatorRecoveryEngine` (refocus → clear modal → vision re-plan, in that order) on failure. Before/after frame hashing verifies every action did what it claimed. All file-touching actions route through `PathPolicy` (§6); destructive OS actions (`delete_file`, `format_disk`, `kill_process`, `modify_registry`) stay in `HIGH_RISK_TOOLS` and stay gated regardless of §5's autonomy elsewhere — the one place Guardian and the Computer Operator deliberately overlap.

---

## 13. Vision Engine

`ScreenAnalyst` (multi-monitor capture, FNV-1a frame hash to skip redundant OCR on static screens) → `HybridPipeline` fusing `OCREngine` (PyTesseract + SHA-256 cache), `AccessibilityTree`, and `DOMBridge` into one `ScreenReport`. No changes from VISION_ENGINE.md.

---

## 14. Voice Engine

`BRVoiceAssistant` state machine (`IDLE → LISTENING → THINKING → SPEAKING`) with wake-word gating, local Whisper ASR (cloud fallback), `NeuralTTS` playback. **Barge-in is a hard requirement:** the moment mic input is detected while `SPEAKING`, TTS stops immediately, remaining speech is cancelled, new input takes priority — no queueing. Pipeline target: recognition → LLM streaming → streaming TTS → playback starting under 300ms end-to-end where hardware allows.

The phone screenshots show Gemini's floating "Ask" overlay and Live screen-share bar — that always-available quick-access surface (not a window you alt-tab to) is the model for JARVIS's persistent overlay in §18.

---

## 15. Event System & Telemetry

`EventBus` (async pub/sub, wildcard topics like `task.*`, DLQ for handler failures) → `EventStore` (append-only `events.jsonl`). Standard types: `SYSTEM_STARTUP/SHUTDOWN`, `TASK_CREATED/COMPLETED/FAILED`, `TOOL_INVOKED/SUCCESS/ERROR`, `SECURITY_ALERT/PERMISSION_DENIED`. This is the substrate both §5 (Self-Upgrade proposals) and §7 (Reflection signals) read from — no new bus needed, just two new subscribers.

---

## 16. Plugin & Tool Ecosystem

`PluginManager` (discovery, manifest parsing, isolated loading) + `ToolRuntimeEngine` (`@register_tool` decorator, permission check → cache check → dispatch) across 90+ tools in `tools/`. `MCPConnector` bridges external MCP servers; `ToolSandbox` isolates untrusted shell/code execution. Self-authored tools from §5 register through the exact same `@register_tool` path as hand-written ones — no privileged shortcut for autonomous code.

---

## 17. Security & Permission Interlocks (expanded)

Existing modes unchanged: `ALLOW_ALL` / `CONFIRM_ALL` / `DENY_HIGH_RISK` / `READ_ONLY`, `ALWAYS_ALLOWED` vs `HIGH_RISK_TOOLS`, RedTeam prompt-injection audit on every tool result. **§4–§6 extend this from tool-name gating to path-based gating and self-modification gating** — same philosophy (default-allow for safe/reversible, default-confirm for destructive/irreversible), now applied to files and to JARVIS's own source code, not only to individual tool calls.

---

## 18. Desktop UI/UX (condensed — full screen-by-screen spec stays in your original Master UI Prompt, unchanged)

- Screens: Home, Chat, Voice Mode, Agent Mode, Tools, Automation, Workspace, Memory, Projects, Knowledge Base, Search, Settings, Logs, Developer Mode, Plugin Manager, **+ new: Autonomy Log** (surfaces Guardian's `AuditLog` — every self-upgrade, every file touched outside workspace, every routing-weight shift, one scrollable feed).
- Performance bar: sub-100ms interaction feedback, streaming everything, 120fps scroll where hardware allows, animations limited to fade/slide/scale and auto-disabled on low-end hardware.
- **Persistent overlay** (informed by the Gemini reference screenshots): a global floating quick-access bar reachable via hotkey from anywhere on the desktop — voice start, quick search, quick command — not only a maximized chat window.
- Everything else (input area, role-based intelligence, smart response routing, settings taxonomy, keyboard shortcuts, developer console) as originally specified — that document is still correct, just no longer the only prompt in play.

---

## 19. Benchmarks & Verification

| Layer | Budget | Measured |
|---|---|---|
| Deterministic Intent Router | <1ms | 0.2ms |
| FNV-1a Cache Lookup | <2ms | 0.4ms |
| Context Assembly + Compression | <50ms | 12ms |
| Gemini Flash Inference | <1200ms | 650ms |
| PyAutoGUI Hardware Click | <100ms | 45ms |
| Local PyTesseract OCR | <400ms | 180ms |

`test_deep_audit.py` (42 tests) and `test_integration.py` (11 scenarios) at 100% pass rate are the existing bar. **New:** these two suites are now also the §5.2 sandbox healthcheck gate — a self-upgrade patch that drops either suite below 100% never leaves the sandbox.

---

## 20. Feature Matrix (updated)

| Subsystem | Feature | Status |
|---|---|---|
| Core Runtime | Zero-Token Intent Engine, DI Container, FNV-1a Bridge | ✅ Production |
| Reasoning / Workflow / Agent / Multi-Agent | As specified | ✅ Production |
| Backends / Router | 6-backend failover | ✅ Production |
| Context / Memory / Computer / Vision / Voice / Tools | As specified | ✅ Production |
| **Guardian Core** | Kill switch, snapshot, rollback, integrity check | 🔶 Spec complete — build first |
| **Self-Upgrade Engine** | Propose → sandbox → classify → deploy/digest | 🔶 Spec complete — build after Guardian |
| **Tiered PathPolicy** | 3-tier file access, cloud-context exclusion | 🔶 Spec complete — build after Guardian |
| **Reflection / Lesson Store** | Implicit + explicit correction capture | 🔶 Spec complete — build after PathPolicy |

---

## 21. Known Technical Debt

Unchanged from TECHNICAL_DEBT.md (backward-compat shims to consolidate, `ui.py` monolith to modularize, `tools/` to group into subpackages), plus one new item: **Guardian Core must pass its own integrity self-test and the full 53-test suite before `self_upgrade.enabled` is ever flipped to `true` in a real deployment — sequencing, not just a feature checklist.**

---

## 22. Build Priority

1. **Guardian Core** — kill switch, snapshot, rollback. Nothing below this line ships before this exists.
2. **PathPolicy** — tiered file access + Secrets Vault bridge + cloud-context exclusion.
3. **Reflection Engine + Lesson Store** — pure memory writes, low risk, ships early.
4. **Self-Upgrade Engine, LOW-risk auto-apply only** — MEDIUM/HIGH stay manual for now.
5. **Enable MEDIUM auto-apply** once (4) has run clean for a stretch you're comfortable with.
6. **HIGH-risk auto-apply** — optional, narrow, only for pre-approved patch categories, if ever.

---

## 23. Beyond Your Brief

- **`jarvis why`** — plain-language explanation of the last N autonomous changes, pulled straight from `AuditLog`. Cheap, since the data already exists.
- **Proactive mode** — `WorkflowEngine`'s `TaskScheduler` plus §7's pattern detection means JARVIS can notice "you do X every Monday" and draft it unprompted, not just wait to be asked.
- **Mobile trigger** — a lightweight companion (start a task from your phone, same overlay pattern as the screenshots) is a natural later phase once the desktop core is stable — not in this build.

---

## Appendix: Directory Structure (updated)

```
BrJarvis/
├── guardian/                    # NEW — immutable safety core
│   ├── core.py
│   ├── kill_switch.py
│   ├── snapshot.py
│   ├── rollback.py
│   ├── audit_log.py
│   └── autonomy_policy.yaml
├── evolution/                   # NEW — self-upgrade engine
│   ├── proposer.py
│   ├── classifier.py
│   ├── sandbox.py
│   ├── deployer.py
│   └── digest.py
├── memory/
│   ├── reflection.py            # NEW
│   ├── lessons.py               # NEW
│   └── ...                      # existing tiers unchanged
├── permissions.py                # extended with PathPolicy
├── tests/
│   ├── test_guardian.py         # NEW
│   ├── test_self_upgrade_sandbox.py   # NEW
│   └── ...                      # existing 53 tests unchanged
└── ...                           # rest of tree unchanged from PROJECT_STRUCTURE.md
```
