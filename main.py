"""
JARVIS MK37 — Enhanced Voice + CLI Interface (main.py v2.0)

Key upgrades:
  - Full CLI/terminal control via cli_controller
  - Enhanced tool routing with screen_describe and screen_read
  - Better voice command processing and natural language understanding
  - Real-time system monitoring injected into context
  - Improved error recovery and reconnection
  - Agent task tracking in UI
  - Extended tool declarations covering all computer control actions
"""
from __future__ import annotations

import asyncio
import re
import threading
import json
import os
import sys
import time
import traceback
import platform
from pathlib import Path
from datetime import datetime

if (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import sounddevice as sd
from google import genai
from google.genai import types

from ui import JarvisUI
from memory.memory_manager import load_memory, update_memory, format_memory_for_prompt

# ── Actions ────────────────────────────────────────────────────────────────
from actions.flight_finder     import flight_finder
from actions.open_app          import open_app
from actions.weather_report    import weather_action
from actions.send_message      import send_message
from actions.reminder          import reminder
from actions.computer_settings import computer_settings
from actions.screen_processor  import screen_process
from actions.youtube_video     import youtube_video
from actions.desktop           import desktop_control
from actions.browser_control   import browser_control
from actions.file_controller   import file_controller
from actions.code_helper       import code_helper
from actions.dev_agent         import dev_agent
from actions.web_search        import web_search as web_search_action
from actions.computer_control  import computer_control
from actions.game_updater      import game_updater
from actions.system_monitor    import system_monitor

# ── Optional: CLI controller ────────────────────────────────────────────────
try:
    from actions.cli_controller import cli_controller
    _CLI_CTRL = True
except ImportError:
    _CLI_CTRL = False

# ── Config ─────────────────────────────────────────────────────────────────
def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"

try:
    from dotenv import load_dotenv as _load_dotenv
    _env = BASE_DIR / ".env"
    if _env.exists():
        _load_dotenv(_env)
except ImportError:
    pass

from config.models import get_model_config as _get_model_config

_model_cfg          = _get_model_config()
LIVE_MODEL          = _model_cfg.get("voice_live", "models/gemini-2.5-flash-native-audio-preview-12-2025")
VOICE_NAME          = _model_cfg.get("voice_name", "Charon")
CHANNELS            = 1
SEND_SAMPLE_RATE    = 16_000
RECEIVE_SAMPLE_RATE = 24_000
CHUNK_SIZE          = 1_024
_OS                 = platform.system()

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    return re.sub(r"[\x00-\x08\x0b-\x1f]", "", text).strip()


def _resolve_audio_device(kind: str, env_var: str) -> int | None:
    """Resolve audio device index from env override, system default, then first matching device."""
    try:
        devices = sd.query_devices()
    except Exception:
        return None

    want_input = kind == "input"
    chan_key = "max_input_channels" if want_input else "max_output_channels"

    def _supports(idx: int) -> bool:
        try:
            return int(devices[idx].get(chan_key, 0)) > 0
        except Exception:
            return False

    raw = (os.environ.get(env_var) or "").strip()
    if raw:
        if raw.lstrip("+-").isdigit():
            idx = int(raw)
            if 0 <= idx < len(devices) and _supports(idx):
                return idx
        else:
            needle = raw.lower()
            for i, dev in enumerate(devices):
                name = str(dev.get("name", "")).lower()
                if needle in name and _supports(i):
                    return i

    try:
        default_pair = sd.default.device
        default_idx = default_pair[0] if want_input else default_pair[1]
        if default_idx is not None and default_idx >= 0 and _supports(int(default_idx)):
            return int(default_idx)
    except Exception:
        pass

    for i in range(len(devices)):
        if _supports(i):
            return i
    return None


def _get_api_key() -> str:
    # Prefer environment variables for deployment flexibility.
    for env_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = (os.environ.get(env_name) or "").strip()
        if value:
            return value

    # Fall back to local config file for desktop-first workflows.
    if API_CONFIG_PATH.exists():
        try:
            with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            value = str(cfg.get("gemini_api_key", "")).strip()
            if value:
                return value
        except Exception:
            pass

    raise RuntimeError(
        "No Gemini API key configured. Set GEMINI_API_KEY/GOOGLE_API_KEY in .env "
        "or add gemini_api_key in config/api_keys.json"
    )


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are JARVIS MK37, an advanced AI assistant. "
            "Be concise, direct, and always use tools for tasks. "
            "You have FULL CONTROL of the user's computer via tools."
        )


def _get_sys_context() -> str:
    """Quick system context snapshot for the prompt."""
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=None)
        ram  = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        return (
            f"[SYSTEM] CPU:{cpu:.0f}%  RAM:{ram:.0f}%  DISK:{disk:.0f}%  "
            f"OS:{_OS}  {datetime.now().strftime('%A %Y-%m-%d %H:%M')}"
        )
    except Exception:
        return f"[SYSTEM] OS:{_OS}  {datetime.now().strftime('%A %Y-%m-%d %H:%M')}"


# ══════════════════════════════════════════════════════════════════════════════
# Tool declarations — complete set for voice/CLI interface
# ══════════════════════════════════════════════════════════════════════════════

TOOL_DECLARATIONS = [
    # ── App / Browser ─────────────────────────────────────────────────────────
    {
        "name": "open_app",
        "description": "Open any application on the computer. Use whenever the user asks to open, launch, or start any app or website.",
        "parameters": {"type": "OBJECT", "properties": {
            "app_name": {"type": "STRING"}
        }, "required": ["app_name"]}
    },
    {
        "name": "browser_control",
        "description": "Full web browser control: open URLs, search, click, type, scroll, fill forms, get text, navigate, screenshot.",
        "parameters": {"type": "OBJECT", "properties": {
            "action":      {"type": "STRING"},
            "browser":     {"type": "STRING"},
            "url":         {"type": "STRING"},
            "query":       {"type": "STRING"},
            "engine":      {"type": "STRING"},
            "selector":    {"type": "STRING"},
            "text":        {"type": "STRING"},
            "description": {"type": "STRING"},
            "direction":   {"type": "STRING"},
            "amount":      {"type": "INTEGER"},
            "key":         {"type": "STRING"},
            "path":        {"type": "STRING"},
            "clear_first": {"type": "BOOLEAN"},
        }, "required": ["action"]}
    },
    # ── Web Search ────────────────────────────────────────────────────────────
    {
        "name": "web_search",
        "description": "Search the web for any information, current events, facts, or comparisons.",
        "parameters": {"type": "OBJECT", "properties": {
            "query":  {"type": "STRING"},
            "mode":   {"type": "STRING"},
            "items":  {"type": "ARRAY", "items": {"type": "STRING"}},
            "aspect": {"type": "STRING"},
        }, "required": ["query"]}
    },
    # ── Weather / Flights ─────────────────────────────────────────────────────
    {
        "name": "weather_report",
        "description": "Show weather for a city.",
        "parameters": {"type": "OBJECT", "properties": {
            "city": {"type": "STRING"}
        }, "required": ["city"]}
    },
    {
        "name": "flight_finder",
        "description": "Search Google Flights and report best options.",
        "parameters": {"type": "OBJECT", "properties": {
            "origin":      {"type": "STRING"},
            "destination": {"type": "STRING"},
            "date":        {"type": "STRING"},
            "return_date": {"type": "STRING"},
            "passengers":  {"type": "INTEGER"},
            "cabin":       {"type": "STRING"},
            "save":        {"type": "BOOLEAN"},
        }, "required": ["origin", "destination", "date"]}
    },
    # ── Messaging / Reminders ─────────────────────────────────────────────────
    {
        "name": "send_message",
        "description": "Send a message via WhatsApp, Telegram, Instagram, Signal, Discord, or Messenger.",
        "parameters": {"type": "OBJECT", "properties": {
            "receiver":     {"type": "STRING"},
            "message_text": {"type": "STRING"},
            "platform":     {"type": "STRING"},
        }, "required": ["receiver", "message_text", "platform"]}
    },
    {
        "name": "reminder",
        "description": "Set a timed desktop notification reminder.",
        "parameters": {"type": "OBJECT", "properties": {
            "date":    {"type": "STRING"},
            "time":    {"type": "STRING"},
            "message": {"type": "STRING"},
        }, "required": ["date", "time", "message"]}
    },
    # ── YouTube ────────────────────────────────────────────────────────────────
    {
        "name": "youtube_video",
        "description": "Play, summarize, get info on, or browse trending YouTube videos.",
        "parameters": {"type": "OBJECT", "properties": {
            "action": {"type": "STRING"},
            "query":  {"type": "STRING"},
            "save":   {"type": "BOOLEAN"},
            "region": {"type": "STRING"},
            "url":    {"type": "STRING"},
        }, "required": []}
    },
    # ── Computer Vision ────────────────────────────────────────────────────────
    {
        "name": "screen_process",
        "description": (
            "Capture and analyze screen or webcam. Use ONLY for visual questions: "
            "'what's on screen', 'look at camera', 'describe what you see'. "
            "After calling, stay SILENT — vision module speaks directly."
        ),
        "parameters": {"type": "OBJECT", "properties": {
            "angle": {"type": "STRING"},
            "text":  {"type": "STRING"},
        }, "required": ["text"]}
    },
    # ── Computer Control: OS-level ─────────────────────────────────────────────
    {
        "name": "computer_settings",
        "description": (
            "ALL OS-level hardware/UI controls: brightness, volume, WiFi, dark mode, "
            "window snap/min/max/close, keyboard shortcuts, scrolling, zoom, tabs, "
            "screenshot, lock screen, restart, shutdown, type text on screen. "
            "NEVER use screen_find for these."
        ),
        "parameters": {"type": "OBJECT", "properties": {
            "action":      {"type": "STRING"},
            "description": {"type": "STRING"},
            "value":       {"type": "STRING"},
        }, "required": []}
    },
    # ── Computer Control: Mouse/Keyboard ──────────────────────────────────────
    {
        "name": "computer_control",
        "description": (
            "Direct mouse and keyboard automation plus AI screen element detection. "
            "Actions: click, double_click, triple_click, right_click, move, drag, "
            "drag_rel, scroll, type, smart_type, hotkey, press, key_down, key_up, "
            "clear_field, select_all, copy, paste, clipboard_get, clipboard_set, "
            "screenshot, screen_find, screen_click, smart_click, smart_type_elem, "
            "screen_read, screen_describe, wait_for_element, focus_window, "
            "get_active_window, list_windows, minimize, maximize, close_window, "
            "snap_left, snap_right, random_data, user_data, wait, screen_size, "
            "get_pos."
        ),
        "parameters": {"type": "OBJECT", "properties": {
            "action":      {"type": "STRING"},
            "text":        {"type": "STRING"},
            "x":           {"type": "INTEGER"},
            "y":           {"type": "INTEGER"},
            "x1":          {"type": "INTEGER"},
            "y1":          {"type": "INTEGER"},
            "x2":          {"type": "INTEGER"},
            "y2":          {"type": "INTEGER"},
            "dx":          {"type": "INTEGER"},
            "dy":          {"type": "INTEGER"},
            "keys":        {"type": "STRING"},
            "key":         {"type": "STRING"},
            "direction":   {"type": "STRING"},
            "amount":      {"type": "INTEGER"},
            "seconds":     {"type": "NUMBER"},
            "title":       {"type": "STRING"},
            "description": {"type": "STRING"},
            "type":        {"type": "STRING"},
            "field":       {"type": "STRING"},
            "clear_first": {"type": "BOOLEAN"},
            "use_cache":   {"type": "BOOLEAN"},
            "path":        {"type": "STRING"},
            "timeout":     {"type": "NUMBER"},
            "interval":    {"type": "NUMBER"},
        }, "required": ["action"]}
    },
    # ── CLI Controller ─────────────────────────────────────────────────────────
    {
        "name": "cli_controller",
        "description": (
            "Full terminal/shell access. Run ANY shell command, manage persistent "
            "shell sessions with state (env vars, cwd), execute Python code, "
            "send input to interactive programs, manage background processes. "
            "Actions: run, run_session, send_input, cd, pwd, python, pipe, bg, "
            "which, env, session_new, session_end, history, auto."
        ),
        "parameters": {"type": "OBJECT", "properties": {
            "action":  {"type": "STRING"},
            "cmd":     {"type": "STRING"},
            "name":    {"type": "STRING"},
            "cwd":     {"type": "STRING"},
            "timeout": {"type": "INTEGER"},
            "key":     {"type": "STRING"},
            "value":   {"type": "STRING"},
            "code":    {"type": "STRING"},
        }, "required": ["action"]}
    },
    # ── File Management ────────────────────────────────────────────────────────
    {
        "name": "file_controller",
        "description": "Manage files and folders: list, create, delete, move, copy, rename, read, write, find, disk usage, organize.",
        "parameters": {"type": "OBJECT", "properties": {
            "action":      {"type": "STRING"},
            "path":        {"type": "STRING"},
            "destination": {"type": "STRING"},
            "new_name":    {"type": "STRING"},
            "content":     {"type": "STRING"},
            "name":        {"type": "STRING"},
            "extension":   {"type": "STRING"},
            "count":       {"type": "INTEGER"},
        }, "required": ["action"]}
    },
    # ── Desktop ────────────────────────────────────────────────────────────────
    {
        "name": "desktop_control",
        "description": "Desktop control: wallpaper, organize, clean, list, stats, AI-powered tasks.",
        "parameters": {"type": "OBJECT", "properties": {
            "action": {"type": "STRING"},
            "path":   {"type": "STRING"},
            "url":    {"type": "STRING"},
            "mode":   {"type": "STRING"},
            "task":   {"type": "STRING"},
        }, "required": ["action"]}
    },
    # ── Code / Dev ─────────────────────────────────────────────────────────────
    {
        "name": "code_helper",
        "description": "Write, edit, explain, run, build, optimize, or screen-debug code files.",
        "parameters": {"type": "OBJECT", "properties": {
            "action":      {"type": "STRING"},
            "description": {"type": "STRING"},
            "language":    {"type": "STRING"},
            "output_path": {"type": "STRING"},
            "file_path":   {"type": "STRING"},
            "code":        {"type": "STRING"},
            "args":        {"type": "STRING"},
            "timeout":     {"type": "INTEGER"},
        }, "required": ["action"]}
    },
    {
        "name": "dev_agent",
        "description": "Build complete multi-file projects: plan, write, install deps, open VSCode, run+fix.",
        "parameters": {"type": "OBJECT", "properties": {
            "description":  {"type": "STRING"},
            "language":     {"type": "STRING"},
            "project_name": {"type": "STRING"},
            "timeout":      {"type": "INTEGER"},
        }, "required": ["description"]}
    },
    # ── System ────────────────────────────────────────────────────────────────
    {
        "name": "system_monitor",
        "description": "Real-time system health: CPU, RAM, disk, network, top processes.",
        "parameters": {"type": "OBJECT", "properties": {
            "action": {"type": "STRING"}
        }, "required": []}
    },
    # ── Agent Task ────────────────────────────────────────────────────────────
    {
        "name": "agent_task",
        "description": (
            "Execute complex multi-step tasks requiring multiple tools. "
            "Examples: 'research X and save to file', 'find and organize files'. "
            "Do NOT use for single commands. NEVER use for Steam/Epic."
        ),
        "parameters": {"type": "OBJECT", "properties": {
            "goal":     {"type": "STRING"},
            "priority": {"type": "STRING"},
        }, "required": ["goal"]}
    },
    # ── Games ─────────────────────────────────────────────────────────────────
    {
        "name": "game_updater",
        "description": "ONLY tool for Steam/Epic Games: install, update, list, download status, schedule.",
        "parameters": {"type": "OBJECT", "properties": {
            "action":              {"type": "STRING"},
            "platform":            {"type": "STRING"},
            "game_name":           {"type": "STRING"},
            "app_id":              {"type": "STRING"},
            "hour":                {"type": "INTEGER"},
            "minute":              {"type": "INTEGER"},
            "shutdown_when_done":  {"type": "BOOLEAN"},
        }, "required": []}
    },
    # ── Memory ────────────────────────────────────────────────────────────────
    {
        "name": "save_memory",
        "description": (
            "Save an important personal fact silently. Call when the user reveals "
            "name, location, preferences, projects, or relationships."
        ),
        "parameters": {"type": "OBJECT", "properties": {
            "category": {"type": "STRING"},
            "key":      {"type": "STRING"},
            "value":    {"type": "STRING"},
        }, "required": ["category", "key", "value"]}
    },
    # ── Mode / Skills ─────────────────────────────────────────────────────────
    {
        "name": "mode_switch",
        "description": "Switch JARVIS persona mode: recon, exploit, report, planner, coder, analyst, general.",
        "parameters": {"type": "OBJECT", "properties": {
            "mode": {"type": "STRING"}
        }, "required": ["mode"]}
    },
    {
        "name": "run_skill",
        "description": "Execute a JARVIS skill by name. Use list_skills to see available skills.",
        "parameters": {"type": "OBJECT", "properties": {
            "skill_name": {"type": "STRING"},
            "arguments":  {"type": "STRING"},
        }, "required": ["skill_name"]}
    },
    {
        "name": "list_skills",
        "description": "List all available JARVIS skills.",
        "parameters": {"type": "OBJECT", "properties": {}, "required": []}
    },
    # ── Shutdown ─────────────────────────────────────────────────────────────
    {
        "name": "shutdown_jarvis",
        "description": "Shut down JARVIS completely. Call when user says goodbye, exit, close, stop JARVIS.",
        "parameters": {"type": "OBJECT", "properties": {}, "required": []}
    },
]


# ══════════════════════════════════════════════════════════════════════════════
class JarvisLive:

    def __init__(self, ui: JarvisUI):
        self.ui              = ui
        self.session         = None
        self.audio_in_queue  = None
        self.out_queue       = None
        self._loop           = None
        self._is_speaking    = False
        self._speaking_lock  = threading.Lock()
        self._turn_done      = None
        self._current_mode   = "general"
        self._reconnect_count = 0
        self._audio_input_device = _resolve_audio_device("input", "JARVIS_AUDIO_INPUT_DEVICE")
        self._audio_output_device = _resolve_audio_device("output", "JARVIS_AUDIO_OUTPUT_DEVICE")
        self._audio_output_enabled = True

        # Allow text commands from UI
        self.ui.on_text_command = self._on_text_command

    # ── Text command from UI input bar ─────────────────────────────────────
    def _on_text_command(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True,
            ),
            self._loop,
        )

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")

    def speak(self, text: str):
        if not self._loop or not self.session:
            print(f"[JARVIS/speak] {text}")
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True,
            ),
            self._loop,
        )

    def speak_error(self, tool_name: str, error):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")

    # ── System prompt builder ──────────────────────────────────────────────
    def _build_config(self) -> types.LiveConnectConfig:
        memory   = load_memory()
        mem_str  = format_memory_for_prompt(memory)
        sys_p    = _load_system_prompt()
        sys_ctx  = _get_sys_context()
        now_str  = datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")

        parts = [
            f"[CURRENT TIME]\n{now_str}\n",
            f"{sys_ctx}\n",
        ]
        if mem_str:
            parts.append(mem_str)
        parts.append(sys_p)

        full_system = "\n".join(parts)

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction=full_system,
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=VOICE_NAME
                    )
                )
            ),
        )

    # ── Tool executor ──────────────────────────────────────────────────────
    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})

        print(f"[JARVIS] 🔧 {name}  {str(args)[:80]}")
        self.ui.set_state("THINKING")

        # Fast-path: save_memory
        if name == "save_memory":
            category = args.get("category", "notes")
            key      = args.get("key", "")
            value    = args.get("value", "")
            if key and value:
                update_memory({category: {key: {"value": value}}})
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            return types.FunctionResponse(id=fc.id, name=name,
                                           response={"result": "ok", "silent": True})

        loop   = asyncio.get_event_loop()
        result = "Done."

        try:
            # ── Dispatch table ────────────────────────────────────────────

            if name == "open_app":
                r = await loop.run_in_executor(
                    None, lambda: open_app(parameters=args, player=self.ui))
                result = r or f"Opened {args.get('app_name')}."

            elif name == "browser_control":
                r = await loop.run_in_executor(
                    None, lambda: browser_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "web_search":
                r = await loop.run_in_executor(
                    None, lambda: web_search_action(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "weather_report":
                r = await loop.run_in_executor(
                    None, lambda: weather_action(parameters=args, player=self.ui))
                result = r or "Weather opened."

            elif name == "flight_finder":
                r = await loop.run_in_executor(
                    None, lambda: flight_finder(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "send_message":
                r = await loop.run_in_executor(
                    None, lambda: send_message(parameters=args, player=self.ui))
                result = r or f"Message sent to {args.get('receiver')}."

            elif name == "reminder":
                r = await loop.run_in_executor(
                    None, lambda: reminder(parameters=args, player=self.ui))
                result = r or "Reminder set."

            elif name == "youtube_video":
                r = await loop.run_in_executor(
                    None, lambda: youtube_video(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "screen_process":
                threading.Thread(
                    target=screen_process,
                    kwargs={"parameters": args, "player": self.ui},
                    daemon=True,
                ).start()
                result = "Vision module activated. Silence — vision speaks directly."

            elif name == "computer_settings":
                r = await loop.run_in_executor(
                    None, lambda: computer_settings(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "computer_control":
                r = await loop.run_in_executor(
                    None, lambda: computer_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "cli_controller":
                if _CLI_CTRL:
                    r = await loop.run_in_executor(
                        None, lambda: cli_controller(parameters=args, player=self.ui))
                    result = r or "Done."
                else:
                    # Fallback: direct subprocess
                    cmd = args.get("cmd", "")
                    if cmd:
                        import subprocess
                        r = subprocess.run(
                            cmd, shell=True, capture_output=True,
                            text=True, timeout=30, encoding="utf-8", errors="replace"
                        )
                        out = (r.stdout or "") + (r.stderr or "")
                        result = out.strip() or "Command completed."
                    else:
                        result = "No command specified."

            elif name == "file_controller":
                r = await loop.run_in_executor(
                    None, lambda: file_controller(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "desktop_control":
                r = await loop.run_in_executor(
                    None, lambda: desktop_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "code_helper":
                r = await loop.run_in_executor(
                    None, lambda: code_helper(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "dev_agent":
                r = await loop.run_in_executor(
                    None, lambda: dev_agent(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "system_monitor":
                r = await loop.run_in_executor(
                    None, lambda: system_monitor(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "agent_task":
                from agent.task_queue import get_queue, TaskPriority
                pmap     = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
                priority = pmap.get(args.get("priority", "normal").lower(), TaskPriority.NORMAL)
                task_id  = get_queue().submit(
                    goal=args.get("goal", ""), priority=priority, speak=self.speak
                )
                self.ui.update_agent_task(task_id, args.get("goal", "")[:20], "running")
                result = f"Task started (ID: {task_id})."

            elif name == "game_updater":
                r = await loop.run_in_executor(
                    None, lambda: game_updater(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "mode_switch":
                mode = args.get("mode", "general").lower()
                valid = ["recon", "exploit", "report", "planner", "coder", "analyst", "general"]
                if mode in valid:
                    self._current_mode = mode
                    self.ui.write_log(f"SYS: Mode → {mode.upper()}")
                    result = f"Switching to {mode.upper()} mode. I'm now operating as a {mode} specialist."
                else:
                    result = f"Unknown mode: {mode}. Available: {', '.join(valid)}"

            elif name == "run_skill":
                def _rs():
                    from skills import load_skills, find_skill, execute_skill
                    sn = args.get("skill_name", "")
                    sa = args.get("arguments", "")
                    skill = next((s for s in load_skills() if s.name == sn), None)
                    if skill is None:
                        skill = find_skill(f"/{sn}")
                    if skill is None:
                        return f"Skill '{sn}' not found."
                    class _Bridge:
                        def chat(sb, msg): return f"[Skill: {skill.name}]\n\n{msg[:2000]}"
                        current_mode = "general"
                        _subagent_mgr = None
                    return execute_skill(skill, sa, _Bridge())
                r = await loop.run_in_executor(None, _rs)
                result = r or "Skill executed."

            elif name == "list_skills":
                def _ls():
                    from skills import load_skills
                    skills = [s for s in load_skills() if s.user_invocable]
                    return "Skills: " + ", ".join(s.name for s in skills)
                result = await loop.run_in_executor(None, _ls)

            elif name == "shutdown_jarvis":
                self.ui.write_log("SYS: JARVIS shutting down.")
                self.speak("Goodbye, sir.")
                def _bye():
                    import time as _t, os as _os
                    _t.sleep(1.2)
                    _os._exit(0)
                threading.Thread(target=_bye, daemon=True).start()
                result = "Shutting down."

            else:
                result = f"Unknown tool: {name}"

        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            traceback.print_exc()

        if not self.ui.muted:
            self.ui.set_state("LISTENING")

        print(f"[JARVIS] 📤 {name} → {str(result)[:100]}")
        return types.FunctionResponse(id=fc.id, name=name, response={"result": result})

    # ── Audio coroutines ───────────────────────────────────────────────────

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    async def _listen_audio(self):
        loop = asyncio.get_event_loop()

        def _safe_put(item):
            try:
                self.out_queue.put_nowait(item)
            except asyncio.QueueFull:
                pass

        def callback(indata, frames, time_info, status):
            with self._speaking_lock:
                speaking = self._is_speaking
            if not speaking and not self.ui.muted:
                loop.call_soon_threadsafe(
                    _safe_put,
                    {"data": indata.tobytes(), "mime_type": "audio/pcm"},
                )

        try:
            with sd.InputStream(
                samplerate=SEND_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=callback,
                device=self._audio_input_device,
            ):
                print(f"[JARVIS] 🎤 Mic stream open (device={self._audio_input_device})")
                self.ui.write_log(f"SYS: Mic ready (device={self._audio_input_device})")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            self.ui.write_log(
                f"ERR: Microphone unavailable ({e}). Set JARVIS_AUDIO_INPUT_DEVICE and restart."
            )
            while True:
                await asyncio.sleep(1.0)

    async def _receive_audio(self):
        out_buf: list[str] = []
        in_buf:  list[str] = []

        async for response in self.session.receive():
            if response.data:
                if self._turn_done and self._turn_done.is_set():
                    self._turn_done.clear()
                if self._audio_output_enabled:
                    self.audio_in_queue.put_nowait(response.data)

            sc = response.server_content
            if sc:
                if sc.output_transcription and sc.output_transcription.text:
                    txt = _clean_transcript(sc.output_transcription.text)
                    if txt:
                        out_buf.append(txt)

                if sc.input_transcription and sc.input_transcription.text:
                    txt = _clean_transcript(sc.input_transcription.text)
                    if txt:
                        in_buf.append(txt)

                if sc.turn_complete:
                    if self._turn_done:
                        self._turn_done.set()
                    if in_buf:
                        full_in = " ".join(in_buf).strip()
                        if full_in:
                            self.ui.write_log(f"You: {full_in}")
                        in_buf = []
                    if out_buf:
                        full_out = " ".join(out_buf).strip()
                        if full_out:
                            self.ui.write_log(f"Jarvis: {full_out}")
                        out_buf = []

            if response.tool_call:
                fn_responses = []
                for fc in response.tool_call.function_calls:
                    fr = await self._execute_tool(fc)
                    fn_responses.append(fr)
                await self.session.send_tool_response(function_responses=fn_responses)

    async def _play_audio(self):
        try:
            stream = sd.RawOutputStream(
                samplerate=RECEIVE_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                device=self._audio_output_device,
            )
            stream.start()
            self._audio_output_enabled = True
            self.ui.write_log(f"SYS: Speaker ready (device={self._audio_output_device})")
        except Exception as e:
            self._audio_output_enabled = False
            self.ui.write_log(
                f"ERR: Speaker unavailable ({e}). Set JARVIS_AUDIO_OUTPUT_DEVICE and restart."
            )
            while True:
                await asyncio.sleep(1.0)
            return
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        self.audio_in_queue.get(), timeout=0.1
                    )
                except asyncio.TimeoutError:
                    if (self._turn_done and self._turn_done.is_set()
                            and self.audio_in_queue.empty()):
                        self.set_speaking(False)
                        self._turn_done.clear()
                    continue
                self.set_speaking(True)
                await asyncio.to_thread(stream.write, chunk)
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()

    # ── Main run loop ──────────────────────────────────────────────────────

    async def run(self):
        client = genai.Client(
            api_key=_get_api_key(),
            http_options={"api_version": "v1beta"},
        )

        while True:
            self._reconnect_count += 1
            try:
                print(f"[JARVIS] 🔌 Connecting (attempt {self._reconnect_count})…")
                self.ui.set_state("THINKING")
                config = self._build_config()

                async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
                    self.session          = session
                    self._loop            = asyncio.get_event_loop()
                    self.audio_in_queue   = asyncio.Queue()
                    self.out_queue        = asyncio.Queue(maxsize=12)
                    self._turn_done       = asyncio.Event()

                    print("[JARVIS] ✅ Connected.")
                    self.ui.set_state("LISTENING")
                    self.ui.write_log("SYS: JARVIS MK37 Neural Core online.")
                    self.ui.write_log(
                        f"SYS: Audio devices in={self._audio_input_device} out={self._audio_output_device}"
                    )
                    if self._reconnect_count > 1:
                        self.ui.write_log(f"SYS: Reconnected (attempt {self._reconnect_count})")

                    tasks = [
                        asyncio.create_task(self._send_realtime()),
                        asyncio.create_task(self._listen_audio()),
                        asyncio.create_task(self._receive_audio()),
                        asyncio.create_task(self._play_audio()),
                    ]
                    done, pending = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_EXCEPTION
                    )
                    for t in pending:
                        t.cancel()
                    for t in done:
                        if t.exception():
                            raise t.exception()

            except Exception as e:
                print(f"[JARVIS] ⚠ {e}")
                if "API_KEY" in str(e).upper() or "NO GEMINI API KEY" in str(e).upper():
                    self.ui.write_log(
                        "ERR: API key missing/invalid. Set GEMINI_API_KEY in .env "
                        "or config/api_keys.json"
                    )
                    await asyncio.sleep(10)
                else:
                    traceback.print_exc()

            self.set_speaking(False)
            self.ui.set_state("THINKING")
            wait = min(3 + self._reconnect_count * 0.5, 15)
            self.ui.write_log(f"SYS: Reconnecting in {wait:.0f}s…")
            await asyncio.sleep(wait)


# ══════════════════════════════════════════════════════════════════════════════
def main():
    ui = JarvisUI("face.png")

    def runner():
        ui.wait_for_api_key()
        jarvis = JarvisLive(ui)
        try:
            asyncio.run(jarvis.run())
        except KeyboardInterrupt:
            print("\n🔴 Shutting down…")

    threading.Thread(target=runner, daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
