# 🔀 BR JARVIS — Intelligent Multi-Backend Model Router (`router.py`)

## Overview
BR JARVIS features an intelligent, multi-backend LLM router that dynamically selects inference backends based on task requirements, vision needs, offline status, and token budgets.

---

## 🔀 Model Routing Hierarchy

```
                                  Input Prompt
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
       [Vision / Real-time]                        [Offline / Private]
                │                                             │
      Gemini 2.5/3.5 Flash                               Ollama Llama3
                │                                             │
      (Google Search Grounding)                      (100% Offline Mode)
```

| Task Category | Primary Backend | Model ID | Fallback Backend |
|---|---|---|---|
| **Primary ReAct & Search** | Gemini | `gemini-3.5-flash` | GPT-4o / Claude |
| **Complex Software Engineering** | Claude | `claude-sonnet-4-20250514` | Gemini 3.1 Pro |
| **100% Offline Execution** | Ollama | `llama3` | Mistral |
| **Accelerated Inference** | NVIDIA NIM | `meta/llama-3.1-70b-instruct` | Gemini |

---

## 🔄 Self-Healing Fallback Engine
If a backend request fails (e.g. 504 Gateway Timeout or Rate Limit), `AgentRouter` catches the exception and automatically redirects the request to **Gemini**, ensuring zero operational downtime.
