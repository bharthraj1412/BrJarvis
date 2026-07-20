# voice/__init__.py — JARVIS MK37 Voice Control Package
"""
Voice package re-exporting TTS, STT, and Assistant engines.
"""
from __future__ import annotations

from voice.tts import NeuralTTS, MCIPlayer
from voice.stt import SounddeviceMicrophone
from voice.assistant import BRVoiceAssistant

__all__ = [
    "NeuralTTS",
    "MCIPlayer",
    "SounddeviceMicrophone",
    "BRVoiceAssistant",
]
