# nvidia_backend.py
from __future__ import annotations

from openai import OpenAI  # NIM uses OpenAI-compatible API
import os
import sys
from config.models import get_model

class NvidiaBackend:
    def __init__(self, model=None):
        api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
        if not api_key:
            raise ValueError("NVIDIA_API_KEY is not set or empty")
            
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
        self.model = model or get_model("nvidia")

    def complete(self, messages: list, system: str = "") -> str:
        all_messages = [{"role": "system", "content": system}] + messages
        use_color = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
        reasoning_color = "\033[90m" if use_color else ""
        reset_color = "\033[0m" if use_color else ""

        chunks: list[str] = []
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            temperature=1,
            top_p=1,
            max_tokens=16384,
            extra_body={"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}},
            stream=True,
        )

        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            if not chunk.choices or getattr(chunk.choices[0], "delta", None) is None:
                continue
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                print(f"{reasoning_color}{reasoning}{reset_color}", end="")
            content = getattr(delta, "content", None)
            if content is not None:
                print(content, end="")
                chunks.append(content)

        return "".join(chunks).strip()
