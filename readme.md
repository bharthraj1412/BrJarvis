# BRJARVIS

[![CI](https://github.com/bharathrajp14/BrJarvis/actions/workflows/ci.yml/badge.svg)](https://github.com/bharathrajp14/BrJarvis/actions)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11--3.14-blue.svg)](https://www.python.org/)
[![Repository](https://img.shields.io/badge/repository-bharathrajp14%2FBrJarvis-181717.svg)](https://github.com/bharathrajp14/BrJarvis)

**BRJARVIS** is a local-first, multimodal AI operating environment for dependable task execution, software work, system automation, voice interaction, personal memory, connectors, and Career OS workflows. It combines a canonical Python runtime with a FastAPI/PWA workspace, a CLI, desktop voice surfaces, and a compact floating assistant for quick commands without taking over the user’s screen.

> **Repository:** [github.com/bharathrajp14/BrJarvis](https://github.com/bharathrajp14/BrJarvis)

## What BRJARVIS provides

BRJARVIS is designed around a single runtime rather than several disconnected assistants. Presentation surfaces submit work to the same orchestrator, task queue, repositories, connector layer, and verification pipeline. This keeps task state, approvals, errors, and final results consistent whether a request starts in the CLI, the browser workspace, Career OS, the voice assistant, or the floating widget.

| Surface | Purpose | Launch command |
|---|---|---|
| Web workspace | Authenticated FastAPI/PWA control plane for tasks, workspace activity, connectors, and results | `jarvis-server` or `python start.py web` |
| CLI | Interactive terminal REPL and one-shot natural-language commands | `jarvis-cli` or `python start.py cli` |
| Floating widget | Compact Orb/Rail assistant for commands, voice capture, task history, and workspace handoff | `python start.py floating` |
| Voice assistant | Dedicated voice/HUD entry point | `python start.py voice` |
| Career OS | Career studio, CRM data, application tracking, and synchronization | `python start.py career` |
| Diagnostics | Status, doctor, smoke, and audio environment checks | `jarvis status`, `python start.py doctor`, `python start.py smoke` |

## Architecture

The installable package under `src/brjarvis` is the source of truth. The runtime is composed from typed configuration, policy-controlled tools, approval gates, durable repositories, task execution ledgers, event persistence, and verification-aware outcomes. The web and desktop surfaces are adapters over this shared runtime.

```text
User
 ├─ Web workspace / PWA
 ├─ CLI / one-shot command
 ├─ Career OS
 ├─ Voice assistant
 └─ Floating Orb/Rail
          │
          ▼
   Canonical assistant runtime
          │
   ┌──────┼───────────────┬──────────────┐
   │      │               │              │
Task   Tools &        Connectors     Memory and
queue  policy gates   and APIs        repositories
          │
          ▼
   Verification, evidence, recovery, and final result
```

The floating widget is intentionally split into focused modules:

- `floating_surface.py` contains the Qt presentation layer: Orb, Command Rail, Context Card, controls, and task-history rendering.
- `floating_runtime.py` contains state, command execution, backend coordination, task-history updates, generation guards, and workspace handoff logic.
- `floating_voice.py` contains microphone capture, manual-stop lifecycle, transcription, and speech playback coordination.
- `float_widget.py` preserves the historical launcher contract and provides a headless fallback when Qt is unavailable.

The current architecture and ownership map are documented in the [production architecture diagram](docs/architecture/production-architecture.png) and [production-readiness audit](docs/audit/PRODUCTION_READINESS_2026-08-19.md).

## Requirements

Use a project-local virtual environment. The setup scripts support Python **3.11–3.13**; the package metadata declares Python `>=3.11, <=3.14`.

Do not install BRJARVIS into system Python, use `--no-deps`, or bypass dependency resolution. Hardware-bound features such as microphone input, speech recognition, text-to-speech, PySide6, and desktop automation require their optional dependencies and a compatible operating-system environment.

## Installation

### Windows

```powershell
git clone https://github.com/bharathrajp14/BrJarvis.git
cd BrJarvis
.\setup_env.bat --dev
```

### Linux or macOS

```bash
git clone https://github.com/bharathrajp14/BrJarvis.git
cd BrJarvis
./setup_linux.sh --dev
```

The setup scripts create `.venv`, install the development dependencies, run `pip check`, and initialize `.env` from `.env.template` when needed. To install optional capabilities manually:

```bash
python -m pip install -e ".[voice,automation]"
python -m pip install -e ".[web,documents,llm-backends]"
```

For a complete development installation, use the project extras declared in `pyproject.toml`:

```bash
python -m pip install -e ".[all,dev]"
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1`. On Linux or macOS, use `source .venv/bin/activate`.

## Security configuration

Copy `.env.template` to `.env` and replace every placeholder before starting the web control plane:

```bash
cp .env.template .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set the generated value as `JARVIS_SERVER_API_KEY`. It must be unique, random, and at least 24 characters long. A minimal secure baseline is:

```dotenv
JARVIS_SERVER_API_KEY=<unique random value>
JARVIS_PERMISSION_MODE=confirm_destructive
JARVIS_HEADLESS=false
JARVIS_ENABLE_UNSAFE_HOST_EXECUTION=false
JARVIS_ENABLE_UNTRUSTED_PLUGINS=false
JARVIS_COOKIE_SECURE=true
JARVIS_CORS_ORIGINS=https://your-approved-origin.example
```

`JARVIS_COOKIE_SECURE=true` requires HTTPS, normally terminated by a trusted reverse proxy. Do not expose the control plane directly to an untrusted network. Localhost is not treated as an authentication boundary.

Connector credentials should be stored through the operating-system credential store. Do not place real provider secrets in JSON metadata, prompts, logs, generated artifacts, or committed files. If a secret has ever been committed, rotate it at the provider; deleting the file does not invalidate the credential.

## Running BRJARVIS

After activating the virtual environment, the installed entry points are:

```bash
jarvis status
jarvis-cli
jarvis-server
```

The source-checkout dispatcher provides the complete set of modes:

```bash
python start.py status
python start.py doctor
python start.py web --port 8000
python start.py cli
python start.py floating
python start.py voice
python start.py career
python start.py career sync
python start.py smoke
python start.py audio
python start.py test
```

A natural-language one-shot command can be passed directly to the dispatcher:

```bash
python start.py "summarize the current project status"
```

Use `python start.py help` for the launcher’s current command summary. Use `python start.py doctor --fix` only when you understand the repair actions it may perform.

## Floating widget workflow

The floating widget is designed for study-friendly, low-distraction use. It uses a compact, translucent Orb/Rail layout rather than occupying the full screen. The minimized state becomes a circular orb, while the expanded state exposes the command rail and context card.

### Manual-stop voice capture

The microphone flow is deliberately controlled by the user:

1. Click **MIC** to begin recording.
2. Speak naturally; silence does not normally end the recording.
3. Click **STOP** when the complete instruction has been captured.
4. BRJARVIS converts the buffered audio to WAV and transcribes it.
5. The transcript passes through a refinement model that produces a concise project instruction without executing it.
6. The refined instruction is submitted to the canonical project orchestrator.
7. The final response appears in task history and may be replayed through the speaker control.

A safety recording cap remains as a fail-safe. Starting a new command or shutting down cancels active recording/playback and prevents stale callbacks from overwriting newer UI state.

### Task history and continuation

The Context Card shows completed and previous tasks with their goal, status, and available answer or result. Selecting a previous task loads its original goal into the editable command field. It does not silently rerun the task; the user reviews the command and explicitly presses **Send** to continue.

### Workspace handoff

When **Open workspace** is selected, the widget first checks whether the backend is ready. If necessary, it starts the local web server, waits for readiness, requests a one-time authenticated handoff, and opens the workspace URL. This avoids opening a browser page whose backend is not running.

The detailed workflow contract is in [FLOATING_WIDGET_VOICE_PROJECT_PLAN.md](docs/FLOATING_WIDGET_VOICE_PROJECT_PLAN.md).

## Testing and verification

Run the maintained non-benchmark regression suite from the repository root:

```bash
python -m pytest tests -m "not benchmark" -q --tb=short --timeout=60
```

For the floating-widget and workspace work, the focused regression set includes Qt offscreen rendering, manual-stop audio capture, runtime state transitions, workspace handoff, FastAPI routes, WebSocket behavior, CLI, and Career OS integration:

```bash
python -m pytest -q \
  tests/unit/test_floating_voice.py \
  tests/unit/test_floating_runtime.py \
  tests/unit/test_float_widget_qt.py \
  tests/test_web_workspace.py \
  tests/integration/test_fastapi_web_routes.py \
  tests/integration/test_websocket_hub.py \
  tests/unit/test_cli_repl.py \
  tests/integration/test_career_os_integration.py
```

Additional quality checks include:

```bash
python -m pip check
python -m py_compile src/brjarvis/desktop/floating_voice.py \
  src/brjarvis/desktop/floating_runtime.py \
  src/brjarvis/desktop/floating_surface.py \
  src/brjarvis/web/api/routes/voice.py
node --check src/brjarvis/web/static/app.js
git diff --check
```

For release verification, build and test the wheel outside the source checkout as described in the [production operations runbook](docs/runbooks/PRODUCTION_OPERATIONS.md).

## Repository layout

```text
BrJarvis/
├─ src/brjarvis/                 Installable application package
│  ├─ agent/                     Task orchestration and execution
│  ├─ career/                    Career OS and CRM workflows
│  ├─ core/                      Configuration, runtime, CLI, and shared services
│  ├─ desktop/                   Qt surfaces, voice, and floating widget
│  ├─ tools/                     Tool schemas, policy, sandbox, and registry
│  └─ web/                       FastAPI server, routes, static PWA, and WebSocket layer
├─ tests/                        Unit, integration, smoke, security, and end-to-end tests
├─ docs/                         Architecture, audit, operations, and feature plans
├─ scripts/                      Diagnostics, setup, smoke, and maintenance helpers
├─ start.py                      Source-checkout compatibility dispatcher
├─ pyproject.toml                Package metadata, dependencies, extras, and entry points
├─ setup_env.bat                 Windows development setup
└─ setup_linux.sh                Linux/macOS development setup
```

## Safety defaults

| Capability | Default behavior |
|---|---|
| Mutating tools | High-risk actions require approval when metadata is incomplete. |
| Destructive actions | Confirmation is required. |
| Host code execution | Disabled unless explicitly enabled. |
| Untrusted plugins | Disabled unless explicitly trusted. |
| Workspace files | Canonicalized and contained before use. |
| Task outcomes | Verified success, partial, failed, cancelled, and timed-out states remain distinct. |
| Event persistence | Bounded in memory, queued for persistence, and written to rotating JSONL files. |

## Documentation

| Document | Purpose |
|---|---|
| [Floating widget voice plan](docs/FLOATING_WIDGET_VOICE_PROJECT_PLAN.md) | Manual-stop recording, transcript refinement, task history, and workspace handoff contract |
| [Production operations runbook](docs/runbooks/PRODUCTION_OPERATIONS.md) | Setup, security, validation, startup, shutdown, monitoring, and rollback |
| [Production-readiness audit](docs/audit/PRODUCTION_READINESS_2026-08-19.md) | Architecture assessment, implemented hardening, residual risks, and release checklist |
| [Production architecture diagram](docs/architecture/production-architecture.png) | Current subsystem and ownership map |
| [Manual operations guide](docs/operations/MANUAL_WORKS_AND_OPERATIONS_GUIDE.md) | Broader operator workflows |
| [Changelog](CHANGELOG.md) | Version history and compatibility notes |

## License

BRJARVIS is released under the [MIT License](LICENSE).
