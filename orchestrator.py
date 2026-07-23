# orchestrator.py — JARVIS MK37 Core Orchestrator (Gemini-Native)
"""
ReAct (Reason + Act) orchestration loop powered by Gemini.
Features:
- Gemini as primary AI engine (only API key required)
- Intelligent tool routing
- Persistent memory injection
- Session history
- Multi-agent support
"""
from __future__ import annotations

import os
import re
import time

from router import AgentRouter
from memory.working import WorkingMemory
from tools.registry import get_tool_prompt_block, parse_tool_call, execute_tool, set_orchestrator_ref

# ── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are BR — a superhuman AI operating system and autonomous controller.
You are intelligent, precise, direct, and capable of executing complex tasks end-to-end.

### CRITICAL DIRECTIVE: USER INTENT IS LAW
1. **UNCONDITIONAL EXECUTION**: Whatever task the user asks for, you MUST execute it to 100% completion using available tools.
2. **NO LOOPS & NO FAKE CLAIMS**: Never repeatedly execute the exact same tool call without changing approach, and NEVER claim a task is done unless verified by tool results.
3. **FAIL-SAFE ADAPTATION**: If a tool or method fails, immediately adapt and try alternative tools (e.g. python script, CLI, or browser) until the goal is achieved.
4. **ZERO REFUSAL FOR SAFE WORK**: Execute system controls, file operations, web scraping, dev tasks, and OS automation immediately without hesitation or unnecessary disclaimers.

### Core Capabilities
1. **AUTONOMOUS ACTION**: Execute tasks end-to-end without constant confirmation.
2. **PARALLEL THINKING**: Break complex tasks into parallel workstreams.
3. **TOOL MASTERY**: Select the optimal tool for each sub-task.
4. **MEMORY**: Pull from persistent memory before asking users to repeat info.
5. **SCOPE SAFETY**: For security/red-team tasks, verify authorization first.
6. **TRANSPARENCY**: Always report what you did and what the result was.

### Execution Philosophy & Response Format
- **BE EXTREMELY CONCISE AND DIRECT**: Give short, high-precision 1-3 sentence answers.
- **ZERO FILLER**: Never output wall-of-text explanations when a tool or direct action can do the work.
- **ACTION-FIRST**: Execute the assigned work using tools immediately.
- Never fabricate results — always call the tool.
- If a tool fails, try an alternative approach.

### Persona Modes (switch with /mode <name>)
- RECON: Systematic OSINT and network intelligence gathering
- EXPLOIT: Authorized vulnerability analysis (scope only)
- REPORT: Professional technical writing
- PLANNER: Strategic decomposition of complex goals
- CODER: Senior full-stack DevSecOps engineer
- ANALYST: Data synthesis and threat intelligence
- GENERAL: Default adaptive mode

### Tool Routing Guide
| Task | Tool |
|------|------|
| Open apps | open_app |
| Web search | web_search |
| Browser automation | browser_control |
| File operations | file_controller |
| System controls (brightness/volume/wifi) | computer_settings |
| Mouse/keyboard | computer_control |
| Code tasks | code_helper or dev_agent |
| Steam/Epic games | game_updater |
| Multi-step complex tasks | agent_task |
| Screen analysis | screen_process |
| YouTube | youtube_video |
| Flights | flight_finder |
| Messaging | send_message |
"""

MODES = {
    "recon":   "RECON MODE: You are a systematic OSINT analyst. Be methodical and exhaustive.",
    "exploit": "EXPLOIT MODE: Authorized vulnerability analysis only. Document everything.",
    "report":  "REPORT MODE: Professional technical writing. Produce client-ready deliverables.",
    "planner": "PLANNER MODE: Decompose goals into ordered, actionable tasks.",
    "coder":   "CODER MODE: Senior full-stack engineer. Write clean, tested, documented code.",
    "analyst": "ANALYST MODE: Synthesize data into clear, actionable insights.",
    "general": "",
}

MAX_REACT_STEPS = 20


class JarvisOrchestrator:

    def __init__(self, router: AgentRouter, use_vector_memory: bool = True):
        self.router = router
        self.working_memory = WorkingMemory(max_tokens=120_000)
        self.vector_memory  = None
        self.current_mode   = "general"
        self.conversation_store = None
        self._subagent_mgr  = None

        # History
        self._session_store = None
        self._session_id    = ""
        self._history_linker = None
        try:
            from history.session_store import SessionStore
            from history.linker import HistoryLinker
            from history.audit_writer import set_session_id
            self._session_store  = SessionStore()
            self._history_linker = HistoryLinker()
            self._session_id = self._session_store.new_session(
                mode="general",
                backend=router.default.value,
            )
            set_session_id(self._session_id)
        except Exception as e:
            print(f"[JARVIS] History unavailable: {e}")

        # Initialize SQLite Conversation Store
        try:
            from memory.conversation_store import ConversationStore
            self.conversation_store = ConversationStore()
            if self._session_id:
                self.conversation_store.start_session(
                    session_id=self._session_id,
                    mode=self.current_mode,
                    backend=router.default.value
                )
        except Exception as e:
            print(f"[JARVIS] Conversation store warning: {e}")

        set_orchestrator_ref(self)

        if use_vector_memory:
            try:
                from memory.vector_store import VectorMemory
                self.vector_memory = VectorMemory()
            except Exception:
                pass

    @property
    def session_id(self) -> str:
        return self._session_id

    def _parse_mode(self, user_input: str) -> str | None:
        m = re.match(r"^/mode\s+(\w+)", user_input.strip())
        if m:
            mode = m.group(1).lower()
            if mode in MODES:
                self.current_mode = mode
                return f"[JARVIS] Mode → {mode.upper()} ✓"
            return f"[JARVIS] Unknown mode: '{mode}'. Available: {', '.join(MODES.keys())}"
        return None

    _tool_prompt_cache: str = ""  # class-level cache for tool prompt block

    def _build_system(self, user_prompt: str = "") -> str:
        name = os.environ.get("JARVIS_ASSISTANT_NAME", "BR").strip()
        sys_prompt = (
            f"You are {name}, an ultra-fast autonomous AI assistant. Think step-by-step, act decisively, avoid filler.\n"
            "CRITICAL EXPORT & TOOL CALL RULES:\n"
            "1. When asked to create, recreate, generate, or export a report, document, or spreadsheet (Excel/Word/PDF), "
            "YOU MUST IMMEDIATELY INVOKE THE TOOL (e.g. ```tool_call\n{\"tool\": \"create_excel_sheet\", \"args\": {...}}\n```).\n"
            "2. NEVER output unexecuted thoughts like 'Generate report content. Now call create_word_document.' as plain text.\n"
            "3. If the user explicitly asks for an Excel file ('i need excel document', 'create excel sheet'), ALWAYS call `create_excel_sheet` with structured data rows, headers, and filename ending in .xlsx."
        )
        parts = [sys_prompt]
        mode_text = MODES.get(self.current_mode, "")
        if mode_text:
            parts.append(f"Mode: {mode_text}")

        try:
            from tools.registry import get_pruned_tool_prompt_block
            if user_prompt:
                parts.append(get_pruned_tool_prompt_block(user_prompt))
            elif not JarvisOrchestrator._tool_prompt_cache:
                from tools.registry import get_tool_prompt_block
                JarvisOrchestrator._tool_prompt_cache = get_tool_prompt_block()
                parts.append(JarvisOrchestrator._tool_prompt_cache)
            else:
                parts.append(JarvisOrchestrator._tool_prompt_cache)
        except Exception:
            from tools.registry import get_tool_prompt_block
            parts.append(get_tool_prompt_block())

        return "\n".join(parts)

    def _extract_keywords(self, text: str) -> list[str]:
        low = text.lower()
        kw  = []
        if any(w in low for w in ["code", "script", "function", "debug", "build", "program"]):
            kw.append("code")
        if any(w in low for w in ["scan", "recon", "pentest", "vuln", "exploit", "nmap"]):
            kw.append("security")
        if any(w in low for w in ["search", "find", "look up", "google", "what is", "who is"]):
            kw.append("search")
        if any(w in low for w in ["analyze", "data", "chart", "graph", "statistics"]):
            kw.append("analysis")
        if any(w in low for w in ["private", "local", "offline", "no cloud"]):
            kw.append("local_private")
        if any(w in low for w in ["image", "photo", "screen", "camera", "see", "look"]):
            kw.append("vision")
        return kw

    def _recall_context(self, user_input: str) -> str:
        if not self.vector_memory:
            return ""
        # Skip trivial inputs (greetings, short phrases, simple commands)
        if len(user_input.split()) < 4:
            return ""
        # Skip obvious command patterns that don't benefit from memory recall
        low = user_input.lower().strip()
        if low.startswith(("open ", "launch ", "start ", "close ", "stop ", "/")):
            return ""
        try:
            results = self.vector_memory.search(user_input, top_k=2)
            if results:
                return "### Relevant Memory\n" + "\n".join(f"- {r}" for r in results)
        except Exception:
            pass
        return ""

    def _save_turn(self, user_input: str, response: str) -> None:
        if not self.vector_memory or len(response) < 20:
            return
        try:
            self.vector_memory.store(
                f"Q: {user_input}\nA: {response[:500]}",
                metadata={"mode": self.current_mode},
            )
        except Exception:
            pass

    def _store_exchange(self, user_input: str, response: str) -> None:
        """Alias for _save_turn to ensure backwards compatibility."""
        self._save_turn(user_input, response)

    def _record_turn(self, role: str, content: str, **kwargs) -> None:
        if self._session_store and self._session_id:
            try:
                self._session_store.add_turn(
                    session_id=self._session_id,
                    role=role,
                    content=content[:5000],
                    **kwargs,
                )
            except Exception:
                pass
        
        # SQLite Sync
        if self.conversation_store and self._session_id:
            try:
                self.conversation_store.log_turn(
                    session_id=self._session_id,
                    role=role,
                    content=content,
                    tool_name=kwargs.get("tool_name"),
                    tool_args=kwargs.get("tool_args"),
                    tool_result=kwargs.get("tool_result"),
                    latency_ms=kwargs.get("latency_ms", 0),
                )
            except Exception:
                pass

    def _check_skill(self, user_input: str) -> str | None:
        try:
            from skills import find_skill, execute_skill, load_skills
            m = re.match(r"^/skill\s+(\S+)\s*(.*)", user_input.strip())
            if m:
                name = m.group(1)
                args = m.group(2).strip()
                for s in load_skills():
                    if s.name == name:
                        return execute_skill(s, args, self)
                skill = find_skill(f"/{name}")
                if skill:
                    return execute_skill(skill, args, self)
                return f"[Skill '{name}' not found]"

            first = user_input.split()[0] if user_input.strip() else ""
            skill = find_skill(first)
            if skill:
                return execute_skill(skill, user_input[len(first):].strip(), self)
        except Exception as e:
            print(f"[JARVIS] Skill check error: {e}")
        return None

    def chat(self, user_input: str) -> str:
        """Main ReAct loop — handles any user request."""
        mode_result = self._parse_mode(user_input)
        if mode_result:
            return mode_result

        skill_result = self._check_skill(user_input)
        if skill_result:
            return skill_result

        # Antigravity 0-Token Intent Bypass
        try:
            from core.intent_engine import DeterministicIntentEngine
            from context.token_manager import TokenBudgetManager
            intent_res = DeterministicIntentEngine.parse_and_execute(user_input)
            if intent_res and intent_res.get("executed"):
                TokenBudgetManager().record_usage(consumed=0, saved=intent_res.get("tokens_saved", 2000), is_bypassed=True)
                return f"⚡ [Antigravity Instant 0-Token Action]\n{intent_res.get('result')}"
        except Exception:
            pass

        # EventBus Task start telemetry
        import uuid
        from events.bus import get_event_bus
        from events.types import TaskEvent
        
        task_id = str(uuid.uuid4())
        event_bus = get_event_bus()
        
        event_bus.publish(TaskEvent(
            topic="task.react.start",
            task_id=task_id,
            goal=user_input,
            status="started"
        ))

        memory_ctx = self._recall_context(user_input)
        augmented  = f"{memory_ctx}{user_input}" if memory_ctx else user_input

        # Smart Context Trimming to maintain sub-300ms inference latency
        try:
            if hasattr(self.working_memory, "trim") and len(self.working_memory.get()) > 10:
                self.working_memory.trim(max_turns=10)
        except Exception:
            pass

        keywords = self._extract_keywords(user_input)
        profile  = self.router.route(keywords)
        system   = self._build_system()

        final_response = ""
        success = True
        _consecutive_tool: dict = {"name": None, "args_str": None, "count": 0}  # duplicate-call guard

        for step in range(MAX_REACT_STEPS):
            t_start = time.monotonic()

            try:
                response = self.router.run(profile, self.working_memory.get(), system)
            except Exception as e:
                final_response = f"Backend error: {e}"
                success = False
                event_bus.publish(TaskEvent(
                    topic="task.react.failed",
                    task_id=task_id,
                    goal=user_input,
                    status=f"error: {e}"
                ))
                break

            latency_ms = int((time.monotonic() - t_start) * 1000)
            tool_name, tool_args = parse_tool_call(response)

            if tool_name:
                # ── Duplicate-call guard ──────────────────────────────────
                import json
                args_str = json.dumps(tool_args or {}, sort_keys=True)
                if tool_name == _consecutive_tool["name"] and args_str == _consecutive_tool.get("args_str"):
                    _consecutive_tool["count"] += 1
                else:
                    _consecutive_tool = {"name": tool_name, "args_str": args_str, "count": 1}

                if _consecutive_tool["count"] >= 2:
                    print(f"[JARVIS] ⚠️ Duplicate-call guard triggered for '{tool_name}' (x{_consecutive_tool['count']})")
                    if _consecutive_tool["count"] >= 3:
                        final_response = (
                            f"[JARVIS] Duplicate tool execution stopped after {_consecutive_tool['count']} attempts. "
                            f"Execution completed."
                        )
                        self.working_memory.add("user", f"[SYSTEM: '{tool_name}' duplicate call blocked. Respond with current results.]")
                        break

                print(f"[JARVIS] 🔧 Step {step+1}: {tool_name}({list(tool_args.keys() if tool_args else [])})")
                t_tool = time.monotonic()
                if _consecutive_tool["count"] >= 4:
                    tool_result = f"[SYSTEM NOTICE: '{tool_name}' execution was blocked because it was called {_consecutive_tool['count']} times consecutively. Respond directly to the user now without making any further tool calls.]"
                else:
                    try:
                        tool_result = execute_tool(tool_name, tool_args or {})
                    except Exception as tool_err:
                        tool_result = f"[Tool Error: {tool_name} failed — {tool_err}. Try an alternative approach.]"
                tool_ms = int((time.monotonic() - t_tool) * 1000)

                self._record_turn(
                    "assistant", response[:2000],
                    tool_name=tool_name, tool_args=tool_args,
                    tool_result=str(tool_result)[:2000],
                    backend=profile.value, latency_ms=tool_ms,
                )

                clean = re.sub(r'```tool_call\s*\n\s*\{.*?\}\s*\n\s*```', '', response, flags=re.DOTALL).strip()
                clean = re.sub(r'<\|start\|>.*?<\|call\|>', '', clean, flags=re.DOTALL)
                clean = re.sub(r'<\|channel\|>.*?<\|call\|>', '', clean, flags=re.DOTALL)
                clean = re.sub(r'<\|message\|>.*?<\|call\|>', '', clean, flags=re.DOTALL)
                clean = re.sub(r'<\|.*?\|>', '', clean).strip()
                if clean:
                    self.working_memory.add("assistant", clean)

                self.working_memory.add("user", f"[Tool: {tool_name}]\n{tool_result}")
                continue

            else:
                final_response = re.sub(r'<\|start\|>.*?<\|call\|>', '', response, flags=re.DOTALL)
                final_response = re.sub(r'<\|channel\|>.*?<\|call\|>', '', final_response, flags=re.DOTALL)
                final_response = re.sub(r'<\|message\|>.*?<\|call\|>', '', final_response, flags=re.DOTALL)
                final_response = re.sub(r'<\|.*?\|>', '', final_response).strip()
                self._record_turn("assistant", final_response[:5000], backend=profile.value, latency_ms=latency_ms)
                break

        else:
            final_response += "\n\n[BR: Max steps reached. Returning current results.]"

        self.working_memory.add("assistant", final_response)
        self._store_exchange(user_input, final_response)
        
        if success:
            event_bus.publish(TaskEvent(
                topic="task.react.completed",
                task_id=task_id,
                goal=user_input,
                status="completed"
            ))
            
        return final_response

    def consolidate_on_exit(self) -> str:
        summary = ""
        try:
            from memory.consolidator import consolidate_session
            saved = consolidate_session(self.working_memory.get(), router=self.router)
            if saved:
                summary = f"Consolidated {len(saved)} memories: {', '.join(saved)}"
        except Exception as e:
            summary = f"Consolidation skipped: {e}"
        return summary

    def shutdown(self):
        summary = self.consolidate_on_exit()
        if self._session_store and self._session_id:
            try:
                self._session_store.close_session(self._session_id, summary=summary)
                if self._history_linker and self._history_linker.available:
                    self._history_linker.on_session_close(
                         self._session_id, summary,
                         mode=self.current_mode,
                         backend=self.router.default.value,
                    )
            except Exception:
                pass

        # SQLite Sync
        if self.conversation_store and self._session_id:
            try:
                self.conversation_store.end_session(self._session_id, summary=summary)
            except Exception:
                pass

        if self._subagent_mgr:
            self._subagent_mgr.shutdown()

    def chat_stream(self, user_input: str):
        """Streaming chat with ReAct loop support — yields tokens as they arrive from the backend."""
        mode_result = self._parse_mode(user_input)
        if mode_result:
            yield mode_result
            return

        skill_result = self._check_skill(user_input)
        if skill_result:
            yield skill_result
            return

        memory_ctx = self._recall_context(user_input)
        augmented = f"{memory_ctx}{user_input}" if memory_ctx else user_input

        self.working_memory.add("user", augmented)
        self._record_turn("user", user_input)

        keywords = self._extract_keywords(user_input)
        profile = self.router.route(keywords)
        system = self._build_system()

        for step in range(MAX_REACT_STEPS):
            backend = self.router.backends.get(profile)
            if backend is None:
                backend = self.router.backends.get(self.router.default)
            if backend is None:
                yield "No backend available."
                return

            full_response = ""
            t_start = time.monotonic()

            # Attempt streaming from the backend with retries
            retry_delay = 1.0
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if hasattr(backend, "stream"):
                        for chunk in backend.stream(self.working_memory.get(), system):
                            full_response += chunk
                            yield chunk
                        break
                    else:
                        full_response = backend.complete(self.working_memory.get(), system)
                        yield full_response
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        yield f"\n[Backend error: {e}]"
                        return
                    time.sleep(retry_delay)
                    retry_delay *= 2

            latency_ms = int((time.monotonic() - t_start) * 1000)
            tool_name, tool_args = parse_tool_call(full_response)

            if tool_name:
                yield f"\n[JARVIS] 🔧 Step {step+1}: {tool_name}...\n"
                t_tool = time.monotonic()
                try:
                    tool_result = execute_tool(tool_name, tool_args or {})
                except Exception as tool_err:
                    tool_result = f"[Tool Error: {tool_name} failed — {tool_err}. Try an alternative approach.]"
                tool_ms = int((time.monotonic() - t_tool) * 1000)

                self._record_turn(
                    "assistant", full_response[:2000],
                    tool_name=tool_name, tool_args=tool_args,
                    tool_result=str(tool_result)[:2000],
                    backend=profile.value, latency_ms=tool_ms,
                )

                clean = re.sub(r'```tool_call\s*\n\s*\{.*?\}\s*\n\s*```', '', full_response, flags=re.DOTALL).strip()
                if clean:
                    self.working_memory.add("assistant", clean)

                self.working_memory.add("user", f"[Tool: {tool_name}]\n{tool_result}")
                yield f"[Tool Result: {tool_name} complete]\n"
                continue
            else:
                self._record_turn("assistant", full_response[:5000], backend=profile.value, latency_ms=latency_ms)
                self.working_memory.add("assistant", full_response)
                self._store_exchange(user_input, full_response)
                break
        else:
            yield "\n\n[JARVIS: Max steps reached. Returning current results.]"
