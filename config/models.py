# config/models.py — JARVIS MK37 Model Configuration (Gemini-Native)
"""
Central model configuration. Gemini is the primary backend.
Priority: ENV VARS > models.json > hardcoded defaults
"""
from __future__ import annotations

import os
import json
from pathlib import Path

_CONFIG_DIR  = Path(__file__).resolve().parent
_MODELS_JSON = _CONFIG_DIR / "models.json"

# ── Defaults (Gemini-first) ────────────────────────────────────────────────
_DEFAULTS = {
    "voice_live":       "models/gemini-3.1-flash-live-preview",
    "voice_name":       "Charon",
    "gemini":           "gemini-3.5-flash",
    "claude":           "claude-sonnet-4-20250514",
    "gpt":              "gpt-4o",
    "ollama":           "llama3",
    "nvidia":           "meta/llama-3.1-70b-instruct",
    "mistral":          "mistral-large-latest",
    "default_backend":  "gemini",
    "planner_model":    "gemini-3.1-pro-preview",
    "fast_model":       "gemini-3.1-flash-lite",
    "openai_base_url":  "",
    "openai_model":     "",
}

_ENV_MAP = {
    "JARVIS_MODEL_GEMINI":    "gemini",
    "JARVIS_MODEL_CLAUDE":    "claude",
    "JARVIS_MODEL_GPT":       "gpt",
    "JARVIS_MODEL_OLLAMA":    "ollama",
    "JARVIS_MODEL_NVIDIA":    "nvidia",
    "JARVIS_MODEL_MISTRAL":   "mistral",
    "JARVIS_MODEL_VOICE":     "voice_live",
    "JARVIS_VOICE_NAME":      "voice_name",
    "JARVIS_DEFAULT_BACKEND": "default_backend",
    "OPENAI_BASE_URL":        "openai_base_url",
    "OPENAI_MODEL":           "openai_model",
}

_cache: dict | None = None


def get_model_config(force_reload: bool = False) -> dict:
    global _cache
    if _cache is not None and not force_reload:
        return _cache.copy()

    config = dict(_DEFAULTS)

    # models.json overrides
    if _MODELS_JSON.exists():
        try:
            data = json.loads(_MODELS_JSON.read_text(encoding="utf-8"))
            for k, v in data.items():
                if not k.startswith("_") and isinstance(v, str) and v.strip():
                    config[k] = v.strip()
        except Exception as e:
            print(f"[Config] Warning reading models.json: {e}")

    # ENV overrides (highest priority)
    for env_key, cfg_key in _ENV_MAP.items():
        val = os.environ.get(env_key, "").strip()
        if val:
            config[cfg_key] = val

    # Always ensure Gemini stays default if configured
    if config.get("default_backend") not in ("gemini", "claude", "gpt", "ollama", "nvidia", "mistral"):
        config["default_backend"] = "gemini"

    _cache = config
    return config.copy()


def get_model(backend: str) -> str:
    return get_model_config().get(backend, _DEFAULTS.get(backend, ""))


def ensure_models_json():
    """Create models.json with defaults if it doesn't exist."""
    if not _MODELS_JSON.exists():
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = dict(_DEFAULTS)
        data["_comment"] = (
            "Edit this file to change models. JARVIS reads it on every boot. "
            "Gemini is the only required backend. Set GEMINI_API_KEY in .env"
        )
        _MODELS_JSON.write_text(json.dumps(data, indent=4), encoding="utf-8")
        print(f"[Config] Created default models.json at {_MODELS_JSON}")


ensure_models_json()
