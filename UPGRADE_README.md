# JARVIS MK37 — Gemini-Native Upgrade Guide

## What's New in This Upgrade

| Feature | Before | After |
|---------|--------|-------|
| Required API keys | Multiple | **Gemini only** |
| Parallel task execution | Sequential | **True parallel (3 workers)** |
| Web search | DDG only | **Gemini Google Search grounding** |
| Planning | Basic | **Dependency-aware parallel planning** |
| Error recovery | Retry | **Smart retry + alternative tool + replan** |
| CLI startup | Complex | **Clean Gemini-only init** |

---

## Quick Setup (5 minutes)

### 1. Get Your Gemini API Key
Go to [Google AI Studio](https://aistudio.google.com/app/apikey) → Create API key (FREE tier available)

### 2. Configure Environment
```bash
# Copy the template
cp .env.template .env

# Edit and add your key
# On Windows: notepad .env
# On Linux/Mac: nano .env
```

Set in `.env`:
```
GEMINI_API_KEY=your_actual_key_here
```

### 3. Apply the Upgrade
```bash
python setup_upgrade.py
```

### 4. Run JARVIS
```bash
# CLI mode (recommended)
python main_mk37.py

# Voice mode (requires microphone)
python main.py

# Full launcher menu
python start.py
```

---

## New Features

### Parallel Task Execution
Run multiple goals simultaneously:

```
# In CLI, use /run with | separator:
OPERATOR > /run search Python news | open Chrome | update Steam games

# Or ask naturally:
OPERATOR > Do three things at once: search AI trends, check disk space, and open Spotify
```

### Gemini-Powered Web Search
Web searches now use Gemini's Google Search grounding — **real-time results** without needing a separate search API.

### Smart Error Recovery
The agent now has 3 levels of error handling:
1. **Retry** — transient errors (network, rate limit)
2. **Alternative tool** — try a different approach
3. **Replan** — completely rethink the strategy

### Better Planning
The planner now supports:
- **Parallel steps** — mark independent steps to run simultaneously
- **Dependency tracking** — steps wait for their prerequisites
- **Smarter fallbacks** — failed critical steps trigger targeted replanning

---

## Files Changed

| File | Change |
|------|--------|
| `gemini_backend.py` | Complete rewrite — robust, vision, search grounding |
| `router.py` | Gemini-first, optional other backends, no crash on missing keys |
| `orchestrator.py` | Cleaner ReAct loop, better system prompt |
| `main_mk37.py` | Parallel `/run` command, clean Gemini-only init |
| `config/models.py` | Gemini as default, auto-create models.json |
| `agent/planner.py` | Dependency-aware parallel planning |
| `agent/executor.py` | TRUE parallel execution with thread pool |
| `agent/task_queue.py` | 3 concurrent workers, multi-goal support |
| `actions/web_search.py` | Gemini Search grounding + DDG fallback |
| `actions/code_helper.py` | All-Gemini, cleaner code |
| `actions/dev_agent.py` | All-Gemini, smarter project builder |

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/run goal1 \| goal2 \| goal3` | Run multiple goals in **parallel** |
| `/tasks` | Show active/queued task status |
| `/mode coder` | Switch AI persona |
| `/skills` | List all 45 built-in skills |
| `/memory search <query>` | Search persistent memories |
| `/history` | Recent session list |
| `/status` | System health check |
| `/help` | Full command reference |
| `/quit` | Exit and save memories |

---

## Troubleshooting

**"No backends available"**
→ Check your `.env` file has `GEMINI_API_KEY=your_key`
→ Or check `config/api_keys.json` has `"gemini_api_key": "your_key"`

**Rate limit errors**
→ Gemini free tier has limits — the system will auto-retry with exponential backoff
→ Upgrade to paid tier for higher limits: https://ai.google.dev/pricing

**Voice mode not working**
→ Voice still requires: `sounddevice`, `pyaudio`, `google-genai`
→ Run: `pip install sounddevice pyaudio google-genai`

**Parallel tasks not running**
→ Use `/run` with `|` separator in the CLI
→ Or ask: "Do X while also doing Y"

---

## Configuration

### models.json (auto-created)
```json
{
    "gemini": "gemini-2.5-flash",
    "default_backend": "gemini",
    "voice_live": "models/gemini-2.5-flash-native-audio-preview-12-2025",
    "voice_name": "Charon"
}
```

### Parallel Workers
Default: 3 concurrent tasks. Change in `agent/task_queue.py`:
```python
_queue = TaskQueue(max_concurrent=5)  # increase for more parallelism
```

---

## Architecture After Upgrade

```
User Input
    │
    ▼
main_mk37.py (CLI) ─── /run cmd ──→ ParallelGoalExecutor
    │                                      │
    ▼                               [Task] [Task] [Task]  ← parallel
JarvisOrchestrator                         │
    │                               AgentExecutor
    ▼                                      │
AgentRouter ──→ GeminiBackend      [Step] [Step]  ← parallel
    │                               [Step]         ← sequential
    ▼
Tools (43 available)
    │
Actions, Browser, Files, Code, System...
```
