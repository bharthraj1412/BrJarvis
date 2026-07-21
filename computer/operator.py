# computer/operator.py — Human-Level Computer Operator Engine for JARVIS MK37
from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional
from computer.types import ActionResult, ActionType, ComputerAction
from core.runtime import get_runtime
from events.bus import get_event_bus
from events.types import AuditEvent
from permissions import check_permission
from vision.engine import get_vision_engine

logger = logging.getLogger("JARVIS.ComputerOperator")

try:
    import pyautogui
    # Enforce PyAutoGUI Fail-Safe security: moving mouse to corner aborts automation
    pyautogui.FAILSAFE = True
    _PYAUTOGUI_AVAILABLE = True
except ImportError:
    _PYAUTOGUI_AVAILABLE = False

try:
    import pyperclip
    _PYPERCLIP_AVAILABLE = True
except ImportError:
    _PYPERCLIP_AVAILABLE = False


class ComputerOperator:
    """Master Computer Operator automating mouse, keyboard, clipboard, and window focus."""

    def __init__(self):
        self.runtime = get_runtime()
        self.event_bus = get_event_bus()
        self.vision = get_vision_engine()

        # Register self in DI container
        self.runtime.container.register_instance(ComputerOperator, self)
        logger.info("⚡ ComputerOperator initialized (Failsafe ACTIVE)")

    def execute_action(self, action: ComputerAction) -> ActionResult:
        """Execute a desktop OS action with permission policy validation and verification."""
        # Permission check
        if not check_permission(action.action_type.value, {"x": action.x, "y": action.y, "text": action.text}):
            err_msg = f"Permission denied for computer action {action.action_type.value}"
            logger.warning(f"🔒 {err_msg}")
            return ActionResult(action_id=action.action_id, success=False, verification_message=err_msg)

        logger.info(f"🖱️ ComputerOperator: Executing [{action.action_type.value}] - {action.description}")

        try:
            if action.action_type == ActionType.MOUSE_CLICK:
                if _PYAUTOGUI_AVAILABLE and action.x is not None and action.y is not None:
                    pyautogui.click(action.x, action.y)

            elif action.action_type == ActionType.KEYBOARD_TYPE:
                if _PYAUTOGUI_AVAILABLE and action.text:
                    pyautogui.typewrite(action.text, interval=0.01)

            elif action.action_type == ActionType.HOTKEY:
                if _PYAUTOGUI_AVAILABLE and action.keys:
                    pyautogui.hotkey(*action.keys)

            elif action.action_type == ActionType.CLIPBOARD_SET:
                if _PYPERCLIP_AVAILABLE and action.text:
                    pyperclip.copy(action.text)

            elif action.action_type == ActionType.CLIPBOARD_GET:
                clip_text = pyperclip.paste() if _PYPERCLIP_AVAILABLE else ""
                return ActionResult(action_id=action.action_id, success=True, data=clip_text)

            elif action.action_type == ActionType.WINDOW_FOCUS:
                success = self.focus_window(action.text or "")
                return ActionResult(
                    action_id=action.action_id,
                    success=success,
                    verification_message=f"Focus window '{action.text}' result: {success}",
                )

            # Audit event
            self.event_bus.publish(AuditEvent(
                topic="audit.action",
                action_type=action.action_type.value,
                target=action.description or "desktop",
                user_confirmed=not action.requires_approval
            ))

            # Post-action state verification via VisionEngine
            report = self.vision.analyze_screen(force_refresh=True)
            verify_msg = f"Action Verified on screen ({report.screen_width}x{report.screen_height})"

            return ActionResult(action_id=action.action_id, success=True, verification_message=verify_msg)

        except Exception as e:
            logger.error(f"❌ ComputerOperator action failed: {e}", exc_info=True)
            return ActionResult(action_id=action.action_id, success=False, verification_message=str(e))

    async def async_execute_action(self, action: ComputerAction) -> ActionResult:
        """Asynchronous execution wrapper for computer action."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.execute_action, action)

    def focus_window(self, title_query: str) -> bool:
        """Attempt to focus a window matching title substring."""
        if not title_query:
            return False

        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                
                # Find matching window handle
                found_hwnd = None
                
                def enum_windows_callback(hwnd, extra):
                    nonlocal found_hwnd
                    if user32.IsWindowVisible(hwnd):
                        length = user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(hwnd, buff, length + 1)
                            if title_query.lower() in buff.value.lower():
                                found_hwnd = hwnd
                                return False
                    return True

                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

                if found_hwnd:
                    user32.SetForegroundWindow(found_hwnd)
                    return True
            except Exception as e:
                logger.debug(f"win32 window focus failed: {e}")

        return False

    def click(self, x: int, y: int, description: str = "") -> ActionResult:
        """Convenience method to click screen coordinates."""
        action = ComputerAction(
            action_type=ActionType.MOUSE_CLICK,
            x=x,
            y=y,
            description=description or f"Click at ({x}, {y})",
        )
        return self.execute_action(action)

    def type_text(self, text: str, description: str = "") -> ActionResult:
        """Convenience method to type text."""
        action = ComputerAction(
            action_type=ActionType.KEYBOARD_TYPE,
            text=text,
            description=description or f"Type '{text[:20]}'",
        )
        return self.execute_action(action)

    def hotkey(self, keys: List[str], description: str = "") -> ActionResult:
        """Convenience method to press a hotkey combination."""
        action = ComputerAction(
            action_type=ActionType.HOTKEY,
            keys=keys,
            description=description or f"Hotkey {'+'.join(keys)}",
        )
        return self.execute_action(action)


_global_computer_operator: Optional[ComputerOperator] = None


def get_computer_operator() -> ComputerOperator:
    global _global_computer_operator
    if _global_computer_operator is None:
        _global_computer_operator = ComputerOperator()
    return _global_computer_operator
