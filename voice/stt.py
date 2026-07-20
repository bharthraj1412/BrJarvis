# voice/stt.py — JARVIS MK37 Speech-To-Text Audio Source
"""
Speech recognition source adapters.
Bypasses PyAudio dependency by implementing a custom sounddevice-based
AudioSource compatibility class for SpeechRecognition.
"""
from __future__ import annotations

import os
import queue
import speech_recognition as sr

_HAS_SD = False
try:
    import sounddevice as sd
    _HAS_SD = True
except ImportError:
    pass


class SounddeviceMicrophone(sr.AudioSource):
    """Zero-dependency SpeechRecognition-compatible Microphone class using sounddevice.
    Bypasses PyAudio entirely, making voice input work seamlessly on modern Python versions (e.g. 3.14).
    """
    def __init__(self, device=None, sample_rate=16000, chunk_size=1024):
        self.device_index = device
        
        # Support environment override for audio input device
        env_device = os.environ.get("JARVIS_AUDIO_INPUT_DEVICE")
        if self.device_index is None and env_device:
            env_device_str = env_device.strip()
            if env_device_str:
                try:
                    if env_device_str.isdigit():
                        self.device_index = int(env_device_str)
                    elif _HAS_SD:
                        # Find a device containing the name string case-insensitively
                        devices = sd.query_devices()
                        for idx, dev in enumerate(devices):
                            if env_device_str.lower() in dev.get('name', '').lower():
                                self.device_index = idx
                                break
                except Exception:
                    pass

        # Resolve default device index if None
        if self.device_index is None and _HAS_SD:
            try:
                self.device_index = sd.default.device[0]
                if self.device_index < 0 or self.device_index is None:
                    # Fallback: search for first device with input channels
                    devices = sd.query_devices()
                    for idx, dev in enumerate(devices):
                        if dev.get('max_input_channels', 0) > 0:
                            self.device_index = idx
                            break
            except Exception:
                self.device_index = None

        self.SAMPLE_RATE = sample_rate
        self.CHUNK = chunk_size
        self.SAMPLE_WIDTH = 2  # 16-bit PCM is 2 bytes
        self.q = queue.Queue()
        self.stream = None
        self.sd_stream = None

    def __enter__(self):
        if not _HAS_SD:
            raise ImportError(
                "sounddevice is not installed. Run 'pip install sounddevice' to use voice features."
            )
            
        self.sd_stream = sd.RawInputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.CHUNK,
            device=self.device_index,
            channels=1,
            dtype='int16',
            callback=self._callback
        )
        self.sd_stream.start()
        self.stream = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sd_stream:
            try:
                self.sd_stream.stop()
                self.sd_stream.close()
            except Exception:
                pass
            self.sd_stream = None
        self.stream = None

    def _callback(self, indata, frames, time_info, status):
        self.q.put(bytes(indata))

    def read(self, size):
        bytes_to_read = size * self.SAMPLE_WIDTH
        data = b''
        while len(data) < bytes_to_read:
            try:
                chunk = self.q.get(timeout=0.35)
                data += chunk
            except queue.Empty:
                break
        return data[:bytes_to_read]
