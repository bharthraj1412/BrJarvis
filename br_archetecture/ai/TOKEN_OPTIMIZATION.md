# ⚡ BR JARVIS — Token Optimization & Cost Reduction Engine

## Overview
Token consumption directly impacts API costs and response latency. BR JARVIS implements token optimization across the entire runtime pipeline.

---

## 🛠️ Optimization Strategies

1. **Context Compression (`context/compressor.py`)**: Strips excess whitespace, removes empty lines, and truncates large outputs into head/tail summaries before LLM dispatch.
2. **Read-Only Tool Result Caching (`memory/cache.py`)**: Hashes tool arguments using fast C-native FNV-1a hashing. Identical tool calls (e.g. searching web, reading file status) return cached results instantly without invoking LLMs or network requests.
3. **Priority Context Budgeting (`context/builder.py`)**: Allocates exact token budgets (e.g. 8192 max tokens, 2048 response reserve) and sorts context items by priority so only high-value information is sent.
4. **Local-First Model Downgrading**: Simple tasks or text cleanup are routed to fast/local models (`gemini-3.1-flash-lite` or Ollama).
