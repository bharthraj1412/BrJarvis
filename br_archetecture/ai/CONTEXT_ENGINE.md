# 🧠 BR JARVIS — Context Engine Architecture (`context/`)

## Overview
Context is the most valuable runtime resource in LLM applications. The Context Engine ensures prompt payloads are built with maximum information quality while respecting strict token budgets.

---

## 🏗️ Components

1. **TokenCounter (`context/token_counter.py`)**: Precise token accounting using `tiktoken` (with fast character ratio fallback).
2. **ContextCompressor (`context/compressor.py`)**: Filters duplicate lines, strips excess whitespace, and compresses long texts into head/tail summaries when budgets are exceeded.
3. **ContextBuilder (`context/builder.py`)**: Collects `ContextItem`s across 7 scopes:
   - `SYSTEM_STATE` (Health metrics, hardware status)
   - `CONVERSATION` (Recent dialogue turns)
   - `ACTIVE_WINDOW` (Current foreground app context)
   - `CLIPBOARD` (System clipboard content)
   - `MEMORY` (Retrieved episodic/semantic memories)
   - `PROJECT_FILES` (Workspace documents)
   - `USER_PREFERENCES` (User rules & guidelines)
4. **ContextEngine (`context/engine.py`)**: Master coordinator registered with `CoreRuntime`.

---

## 📊 Context Assembly Flow

```
Raw Multi-Source Data ──→ ContextItems ──→ Priority Sort (10 to 1) ──→ Token Budget Check ──→ Compressed Output
```
