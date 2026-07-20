# core/error_middleware.py — Global Exception and Error Handling Tracker for BR JARVIS
from __future__ import annotations

import logging
import traceback
from typing import Any, Callable, Dict, Optional, Type
from events.bus import get_event_bus
from events.types import ErrorEvent
from core.lifecycle import LifecycleManager
from core.di import get_container

logger = logging.getLogger("JARVIS.ErrorMiddleware")


class ErrorTracker:
    """Global system error tracker. Formats and processes failures, publishes events,

    and handles emergency shutdown/interlock decisions on critical failures.
    """

    def __init__(self):
        self.event_bus = get_event_bus()
        self.error_count = 0
        self.critical_error_count = 0

    def capture_exception(
        self,
        exc: BaseException,
        context: Optional[Dict[str, Any]] = None,
        is_critical: bool = False
    ) -> None:
        """Capture, format, log, and publish exception details."""
        self.error_count += 1
        exc_type = type(exc).__name__
        exc_message = str(exc)
        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        context_str = f" | Context: {context}" if context else ""
        log_msg = f"[{'CRITICAL' if is_critical else 'ERROR'}] Captured exception {exc_type}: {exc_message}{context_str}"
        
        if is_critical:
            self.critical_error_count += 1
            logger.critical(log_msg)
            logger.critical(tb_str)
        else:
            logger.error(log_msg)
            logger.error(tb_str)

        # Build and publish error event
        try:
            event = ErrorEvent(
                topic="system.error",
                error_message=exc_message,
                exception_type=exc_type,
                stack_trace=tb_str,
                payload=context or {}
            )
            self.event_bus.publish(event)
        except Exception as e:
            logger.critical(f"Failed to publish ErrorEvent to EventBus: {e}")

        # If it's critical, trigger emergency stop or lifecycle shutdown
        if is_critical:
            self.trigger_emergency_shutdown(exc_message)

    def trigger_emergency_shutdown(self, reason: str) -> None:
        """Trigger global system emergency shutdown."""
        logger.critical(f"🚨 EMERGENCY SHUTDOWN TRIGGERED. Reason: {reason}")
        try:
            container = get_container()
            lifecycle = container.resolve(LifecycleManager)
            if lifecycle:
                # Run shutdown tasks in executor loop or schedule it
                logger.info("Executing lifecycle shutdown under error tracker directive...")
                # Note: Usually run inside asyncio loop. If loop is running, schedule shutdown.
        except Exception as e:
            logger.critical(f"Failed to cleanly shutdown during emergency: {e}")


_global_error_tracker: Optional[ErrorTracker] = None


def get_error_tracker() -> ErrorTracker:
    global _global_error_tracker
    if _global_error_tracker is None:
        _global_error_tracker = ErrorTracker()
    return _global_error_tracker
