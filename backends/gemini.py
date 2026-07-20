# backends/gemini.py — JARVIS MK37 Primary AI Backend (Gemini)
"""
Robust Gemini backend — the ONLY required backend for JARVIS MK37.
Supports: text completion, streaming, vision, grounding (web search).
Falls back gracefully on any model error.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Generator

from backends.base import BaseBackend


def _load_api_key() -> str:
    """Load Gemini API key from env or config/api_keys.json."""
    for env in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get(env, "").strip()
        if val:
            return val

    cfg_path = Path(__file__).parent.parent / "config" / "api_keys.json"
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            key = data.get("gemini_api_key", "").strip()
            if key:
                return key
        except Exception:
            pass

    raise ValueError(
        "No Gemini API key found.\n"
        "Set GEMINI_API_KEY env var OR add 'gemini_api_key' to config/api_keys.json"
    )


class GeminiBackend(BaseBackend):
    """
    Full-featured Gemini backend for JARVIS MK37.
    Model priority: gemini-3.5-flash → gemini-3.1-pro-preview → ...
    """

    FALLBACK_MODELS = [
        "gemini-3.5-flash",
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    def __init__(self, model: str = None, api_key: str = None):
        self.api_key = api_key or _load_api_key()
        self.model   = model or self._pick_model()
        self._client = None
        print(f"[Gemini] [OK] Using model: {self.model}")

    @property
    def name(self) -> str:
        return "Gemini"

    @property
    def model_name(self) -> str:
        return self.model

    def _pick_model(self) -> str:
        """Try to use the best available model."""
        try:
            from config.models import get_model
            cfg_model = get_model("gemini")
            if cfg_model:
                return cfg_model
        except Exception:
            pass
        return self.FALLBACK_MODELS[0]

    @property
    def client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def complete(self, messages: list, system: str = "", tools: list = None) -> str:
        """Standard completion — used by the ReAct orchestrator."""
        contents = []

        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content = msg.get("content", "")
            if content:
                contents.append({"role": role, "parts": [{"text": content}]})

        config = {}
        if system:
            config["system_instruction"] = system

        for attempt, model in enumerate(self.FALLBACK_MODELS):
            try:
                target_model = self.model if attempt == 0 else model
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=contents if contents else [{"role": "user", "parts": [{"text": "hello"}]}],
                    config=config if config else None,
                )
                return response.text or ""
            except Exception as e:
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    print(f"[Gemini] Rate limit on {target_model}, waiting 5s...")
                    time.sleep(5)
                if attempt == len(self.FALLBACK_MODELS) - 1:
                    raise
                print(f"[Gemini] Model {target_model} failed: {e} — trying next...")
                time.sleep(1)

        return ""

    def stream(self, messages: list, system: str = "") -> Generator[str, None, None]:
        """Streaming completion."""
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content = msg.get("content", "")
            if content:
                contents.append({"role": role, "parts": [{"text": content}]})

        config = {}
        if system:
            config["system_instruction"] = system

        try:
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config if config else None,
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[Stream error: {e}]"

    def complete_with_search(self, query: str, system: str = "") -> str:
        """Completion with Google Search grounding (real-time web data)."""
        try:
            config = {"tools": [{"google_search": {}}]}
            if system:
                config["system_instruction"] = system

            response = self.client.models.generate_content(
                model=self.model,
                contents=query,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            print(f"[Gemini] Search grounding failed: {e} — falling back to regular completion")
            return self.complete([{"role": "user", "content": query}], system)

    def complete_with_vision(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        """Vision completion — analyze an image."""
        import base64
        try:
            b64 = base64.b64encode(image_bytes).decode("ascii")
            contents = [{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": b64}},
                    {"text": prompt},
                ]
            }]
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
            return response.text or ""
        except Exception as e:
            return f"Vision error: {e}"

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio bytes using Gemini."""
        import base64
        try:
            b64 = base64.b64encode(audio_bytes).decode("ascii")
            contents = [{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": b64}},
                    {"text": "Transcribe this audio clip exactly. If you only hear noise or silence, return an empty string. Output only the transcription, no chat, no intro, no comments."},
                ]
            }]
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
            return (response.text or "").strip()
        except Exception as e:
            print(f"[Gemini] Transcription failed: {e}")
            return ""

    def quick(self, prompt: str) -> str:
        """Quick single-prompt completion — for planning, routing, etc."""
        return self.complete([{"role": "user", "content": prompt}])

    def ping(self, timeout: float = 3.0) -> bool:
        """Health check via completion to leverage fallback model chain."""
        try:
            start = time.monotonic()
            result = self.complete([{"role": "user", "content": "ping"}])
            elapsed = time.monotonic() - start
            is_err = "error" in result.lower() or "failed" in result.lower()
            return bool(result) and not is_err and elapsed < timeout
        except Exception:
            return False
