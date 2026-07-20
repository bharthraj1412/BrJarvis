# vision/engine.py — Core Vision Engine Coordinator for JARVIS MK37
from __future__ import annotations

import logging
from typing import Optional
from core.runtime import get_runtime
from events.bus import get_event_bus
from events.types import BaseEvent
from vision.ocr_engine import OCREngine
from vision.screen_analyst import ScreenAnalyst
from vision.types import ScreenAnalysisReport

logger = logging.getLogger("JARVIS.VisionEngine")


class VisionEngine:
    """Master Vision Engine managing screen capture, OCR, UI detection, and frame caching."""

    def __init__(self):
        self.analyst = ScreenAnalyst()
        self.ocr = OCREngine()
        self.runtime = get_runtime()
        self.event_bus = get_event_bus()

        self._cached_report: Optional[ScreenAnalysisReport] = None

        # Register self in DI Container
        self.runtime.container.register_instance(VisionEngine, self)
        logger.info("⚡ VisionEngine initialized")

    def analyze_screen(self, force_refresh: bool = False) -> ScreenAnalysisReport:
        """Capture and analyze primary monitor screen."""
        raw_bytes, w, h, frame_hash = self.analyst.capture_frame()

        if not force_refresh and self.analyst.is_frame_unchanged(frame_hash) and self._cached_report:
            logger.debug("⚡ VisionEngine: Unchanged frame hash, returning cached analysis")
            return self._cached_report

        ocr_text, elements = self.ocr.extract_text_and_elements(raw_bytes, w, h)

        report = ScreenAnalysisReport(
            screen_width=w,
            screen_height=h,
            ocr_text=ocr_text,
            elements=elements,
            frame_hash=frame_hash,
            active_window_title="Active Window",
        )
        self._cached_report = report

        # Publish Event
        self.event_bus.publish(BaseEvent(
            topic="vision.screen.analyzed",
            payload={"width": w, "height": h, "elements_count": len(elements)}
        ))

        return report


_global_vision_engine: Optional[VisionEngine] = None


def get_vision_engine() -> VisionEngine:
    global _global_vision_engine
    if _global_vision_engine is None:
        _global_vision_engine = VisionEngine()
    return _global_vision_engine
