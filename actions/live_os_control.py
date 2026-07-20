# actions/live_os_control.py — BR JARVIS MK37 Live Autonomous OS Controller
"""
Live Autonomous OS Visual Control Engine ("Antigravity Live Control").
Real-time screen perception, visual grounding, fast reaction loop, and continuous desktop automation.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import re
import sys
import time
from pathlib import Path

from actions.computer_control import (
    _screen_size,
    _take_screenshot_bytes,
    _click,
    _double_click,
    _right_click,
    _type_text,
    _smart_type,
    _hotkey,
    _press,
    _scroll,
    _drag,
    _move,
    _focus_window,
    _clear_field,
)

from core.native_bridge import fast_hash, grid_transform

_OS = platform.system()


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_api_key() -> str:
    try:
        cfg_path = _base_dir() / "config" / "api_keys.json"
        if cfg_path.exists():
            return json.loads(cfg_path.read_text(encoding="utf-8")).get("gemini_api_key", "")
    except Exception:
        pass
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")


class LiveOSController:
    """Autonomous Live OS Control Loop Engine."""

    def __init__(self, goal: str, max_steps: int = 20, step_delay: float = 0.5):
        self.goal = goal.strip()
        self.max_steps = max_steps
        self.step_delay = step_delay
        self.history: list[dict] = []
        self._last_img_hash: int | None = None

    def run(self, player=None, speak=None) -> str:
        """Execute the live visual control loop until goal is achieved or steps exhausted."""
        api_key = _get_api_key()
        if not api_key:
            return "Error: No API key available for Live OS Vision Controller."

        try:
            from google import genai
            from google.genai import types as gtypes
            from config.models import get_model

            client = genai.Client(api_key=api_key)
            model_name = get_model("gemini") or "gemini-3.5-flash"
        except Exception as e:
            return f"Failed to initialize Gemini Vision client: {e}"

        screen_w, screen_h = _screen_size()

        if player:
            player.write_log(f"[LiveOS] Starting task: '{self.goal}' on {screen_w}x{screen_h}")
        if speak:
            speak(f"Starting live OS control for: {self.goal}")

        print(f"\n============================================================")
        print(f" 🤖 JARVIS LIVE OS CONTROL ENGINE (Antigravity Mode)")
        print(f" Goal: {self.goal}")
        print(f" Screen Resolution: {screen_w}×{screen_h}")
        print(f"============================================================\n")

        for step in range(1, self.max_steps + 1):
            time.sleep(self.step_delay)

            # 1. Capture screen frame
            img_bytes = _take_screenshot_bytes()
            if not img_bytes:
                print(f"[LiveOS Step {step}] ⚠️ Failed to capture screenshot.")
                continue

            # Native C fast FNV-1a hash check for static screen detection
            img_hash = fast_hash(img_bytes)
            is_static = (img_hash == self._last_img_hash)
            self._last_img_hash = img_hash

            # 2. Prepare visual prompt
            history_summary = ""
            if self.history:
                last_few = self.history[-4:]
                history_summary = "PAST ACTIONS TAKEN:\n" + "\n".join(
                    f" - Step {h['step']}: Action='{h['action']}', Target='{h.get('target','')}', Result='{h['result']}'"
                    for h in last_few
                )

            system_instruction = (
                f"You are JARVIS, an autonomous AI operating system controller. "
                f"Your goal is: '{self.goal}'.\n"
                f"Current screen resolution: {screen_w} width x {screen_h} height.\n"
                f"Coordinates scale: 0 to 1000 for x_norm and y_norm (where 0,0 is top-left, 1000,1000 is bottom-right).\n"
                f"{history_summary}\n\n"
                f"Analyze the screenshot carefully. Identify open windows, input fields, buttons, icons, or text required to reach the goal.\n"
                f"Respond ONLY with a valid JSON object matching this schema:\n"
                f"{{\n"
                f'  "thought": "short explanation of visual analysis and next step",\n'
                f'  "action": "click" | "double_click" | "right_click" | "type" | "hotkey" | "press" | "drag" | "scroll" | "focus" | "wait" | "done" | "fail",\n'
                f'  "x_norm": 0..1000,\n'
                f'  "y_norm": 0..1000,\n'
                f'  "text": "text to type if action is type",\n'
                f'  "keys": "hotkey combo like ctrl+t or enter if action is hotkey/press",\n'
                f'  "reason": "why this action is taken",\n'
                f'  "done": true/false\n'
                f"}}\n"
            )

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        gtypes.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        system_instruction,
                    ],
                )
                raw_text = (response.text or "").strip()
                # Clean JSON fences if present
                clean_json = re.sub(r"```(?:json)?", "", raw_text).strip().rstrip("`").strip()
                data = json.loads(clean_json)
            except Exception as e:
                print(f"[LiveOS Step {step}] ⚠️ Vision inference parsing failed: {e}")
                continue

            thought = data.get("thought", "")
            action = data.get("action", "wait").lower().strip()
            x_norm = data.get("x_norm")
            y_norm = data.get("y_norm")
            text_val = data.get("text", "")
            keys_val = data.get("keys", "")
            is_done = data.get("done", False)

            # Native hardware grid transform: (0..1000) -> actual pixels
            px_x, px_y = None, None
            if x_norm is not None and y_norm is not None:
                try:
                    px_x, px_y = grid_transform(int(x_norm), int(y_norm), screen_w, screen_h)
                except Exception:
                    px_x, px_y = None, None

            print(f"➔ [Step {step}/{self.max_steps}] Thought: {thought}")
            print(f"   Action: '{action}' | Target Coords: ({px_x}, {px_y}) | Input: '{text_val or keys_val}'")

            if player:
                player.write_log(f"[LiveOS #{step}] {action} -> ({px_x},{px_y})")

            # 3. Execute OS action
            result_str = ""
            try:
                if action == "done" or is_done:
                    summary = f"Goal achieved in {step} steps: {thought}"
                    print(f"\n✅ {summary}\n")
                    if speak:
                        speak("Task completed successfully, sir.")
                    return summary

                if action == "fail":
                    summary = f"Task marked unachievable at step {step}: {thought}"
                    print(f"\n❌ {summary}\n")
                    return summary

                if action == "click" and px_x is not None and px_y is not None:
                    result_str = _click(px_x, px_y, "left")

                elif action == "double_click" and px_x is not None and px_y is not None:
                    result_str = _double_click(px_x, px_y)

                elif action == "right_click" and px_x is not None and px_y is not None:
                    result_str = _right_click(px_x, px_y)

                elif action == "type":
                    if px_x is not None and px_y is not None:
                        _click(px_x, px_y, "left")
                        time.sleep(0.1)
                    result_str = _smart_type(text_val, clear_first=False)

                elif action == "hotkey":
                    result_str = _hotkey(*[k.strip() for k in keys_val.split("+")])

                elif action == "press":
                    result_str = _press(keys_val or "enter")

                elif action == "scroll":
                    result_str = _scroll("down" if (y_norm or 500) > 500 else "up", 4)

                elif action == "focus":
                    result_str = _focus_window(text_val)

                elif action == "wait":
                    time.sleep(1.0)
                    result_str = "Waited 1s"
                else:
                    result_str = f"Executed generic action: {action}"

            except Exception as ex:
                result_str = f"Action execution error: {ex}"
                print(f"   ⚠️ Action error: {ex}")

            self.history.append({
                "step": step,
                "action": action,
                "target": f"({px_x},{px_y})" if px_x is not None else "",
                "result": result_str
            })

        summary = f"Live OS Control reached maximum step limit ({self.max_steps}). Goal: {self.goal}"
        print(f"\n⚠️ {summary}\n")
        return summary


def live_os_control_action(parameters: dict, player=None, speak=None) -> str:
    goal = parameters.get("goal", "").strip()
    if not goal:
        return "Please provide a goal for Live OS Control, sir."

    max_steps = int(parameters.get("max_steps", 20))
    controller = LiveOSController(goal=goal, max_steps=max_steps)
    return controller.run(player=player, speak=speak)
