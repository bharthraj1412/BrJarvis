# voice/audio_processor.py — Audio Signal Processing & Noise Floor Filter for JARVIS MK37
"""
Provides Voice Activity Detection (VAD), RMS audio noise floor estimation,
auto-gain adjustment, and silence filtering for robust speech input.
"""
from __future__ import annotations

import math
import struct
from typing import Tuple


class AudioProcessor:
    """Real-time PCM audio buffer analysis and noise suppression filter."""

    def __init__(self, sample_rate: int = 16000, frame_duration_ms: int = 30):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * (frame_duration_ms / 1000.0) * 2)  # 16-bit mono = 2 bytes per sample
        self.noise_floor = 300.0

    def calculate_rms(self, pcm_data: bytes) -> float:
        """Calculate Root Mean Square (RMS) energy level of 16-bit PCM audio samples."""
        if not pcm_data or len(pcm_data) < 2:
            return 0.0
        
        count = len(pcm_data) // 2
        try:
            shorts = struct.unpack(f"<{count}h", pcm_data[:count*2])
            sum_squares = sum(s * s for s in shorts)
            return math.sqrt(sum_squares / count)
        except Exception:
            return 0.0

    def update_noise_floor(self, pcm_data: bytes, alpha: float = 0.05) -> float:
        """Dynamically update ambient noise floor estimation during quiet periods."""
        rms = self.calculate_rms(pcm_data)
        if rms > 0:
            self.noise_floor = (1 - alpha) * self.noise_floor + alpha * rms
        return self.noise_floor

    def is_speech_present(self, pcm_data: bytes, threshold_multiplier: float = 2.2) -> bool:
        """Check if audio frame exceeds dynamic noise floor speech threshold (VAD)."""
        rms = self.calculate_rms(pcm_data)
        threshold = max(self.noise_floor * threshold_multiplier, 400.0)
        return rms >= threshold

    def normalize_pcm(self, pcm_data: bytes, target_peak: int = 24000) -> bytes:
        """Apply dynamic auto-gain control to PCM audio bytes."""
        if not pcm_data or len(pcm_data) < 2:
            return pcm_data
        
        count = len(pcm_data) // 2
        try:
            shorts = list(struct.unpack(f"<{count}h", pcm_data[:count*2]))
            max_val = max(abs(s) for s in shorts) or 1
            if max_val >= target_peak:
                return pcm_data
            
            scale = min(target_peak / max_val, 4.0)
            scaled = [min(32767, max(-32768, int(s * scale))) for s in shorts]
            return struct.pack(f"<{count}h", *scaled)
        except Exception:
            return pcm_data
