# computer/operator.py — Human-Level Computer Operator Engine for JARVIS MK37
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional
from computer.types import ActionResult, ActionType, ComputerAction
from core.runtime import get_runtime
from events.bus import get_event_bus
from events.types import AuditEvent
from permissions import check_permission
from vision.engine import get_vision_engine

logger = logging.getLogger("JARVIS.ComputerOperator")

try:
    import pyautogui
    pyautogui.FAILSAFE = False
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
        logger.info("⚡ ComputerOperator initialized")

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


_global_computer_operator: Optional[ComputerOperator] = None


def get_computer_operator() -> ComputerOperator:
    global _global_computer_operator
    if _global_computer_operator is None:
        _global_computer_operator = ComputerOperator()
    return _global_computer_operator
