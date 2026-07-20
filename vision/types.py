# vision/types.py — Pydantic v2 Data Models for Vision Engine
from __future__ import annotations

import enum
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ElementType(str, enum.Enum):
    BUTTON = "BUTTON"
    INPUT = "INPUT"
    TEXT = "TEXT"
    WINDOW = "WINDOW"
    ICON = "ICON"
    UNKNOWN = "UNKNOWN"


class ScreenBoundingBox(BaseModel):
    xmin: int
    ymin: int
    xmax: int
    ymax: int

    @property
    def center_x(self) -> int:
        return (self.xmin + self.xmax) // 2

    @property
    def center_y(self) -> int:
        return (self.ymin + self.ymax) // 2


class DetectedUIElement(BaseModel):
    element_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    text: Optional[str] = None
    bbox: ScreenBoundingBox
    confidence: float = 1.0
    element_type: ElementType = ElementType.UNKNOWN


class ScreenAnalysisReport(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    screen_width: int = 1920
    screen_height: int = 1080
    ocr_text: str = ""
    elements: List[DetectedUIElement] = Field(default_factory=list)
    frame_hash: int = 0
    active_window_title: Optional[str] = None
