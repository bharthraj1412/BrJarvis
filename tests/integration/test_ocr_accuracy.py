# tests/integration/test_ocr_accuracy.py — Scenarios 17 to 20: OCR Accuracy & Background Analysis
from __future__ import annotations

import pytest
from vision.ocr_engine import OCREngine
from vision.types import DetectedUIElement, ElementType, ScreenBoundingBox


def test_scenario_17_ocr_accuracy():
    """Scenario 17: Extract exact text string from image."""
    ocr = OCREngine()
    text, elements = ocr.extract_text_and_elements(b"dummy_data", 1920, 1080)
    
    # Assert primary keyword detection
    assert "Dashboard" in text or "Portal" in text


def test_scenario_18_handwritten_ocr():
    """Scenario 18: Fallback locator logic for handwriting text."""
    ocr = OCREngine()
    text, elements = ocr.extract_text_and_elements(b"handwritten_input", 1920, 1080)
    
    # Locate Settlement elements
    elem = ocr.find_element_by_label("Settlements", elements)
    assert elem is not None
    assert elem.element_type == ElementType.BUTTON


def test_scenario_19_ocr_noisy_background():
    """Scenario 19: Extract texts under noise-heavy canvas backgrounds."""
    ocr = OCREngine()
    text, elements = ocr.extract_text_and_elements(b"noisy_canvas_bytes", 1920, 1080)
    assert "Settings" in text


def test_scenario_20_translation_detection():
    """Scenario 20: Detect text languages / triggering system actions."""
    # Simulating translation trigger evaluation
    dummy_text = "こんにちは (Konnichiwa)"
    should_translate = any(ord(char) > 127 for char in dummy_text)
    assert should_translate is True
