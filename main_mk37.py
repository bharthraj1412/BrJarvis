# main_mk37.py — JARVIS MK37 CLI Orchestrator (Gemini-Native)
"""
Production CLI for JARVIS MK37.
Only requires a Gemini API key — all other backends are optional.
"""
from __future__ import annotations

import os
import sys
import signal
import traceback
import threading
from datetime import datetime, timezone
from pathlib import Path

# ── UTF-8 on Windows ───────────────────────────────────────────────────────
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Load .env ─────────────────────────────────────────────────────────────
from pathlib import Path as _P
_env = _P(__file__).parent / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        # Parse .env manually
        for line in _env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.bootstrap import build_assistant_runtime
from router import AgentProfile

console = Console(force_terminal=True)

BANNER = """
    ██████╗  ██████╗ 
    ██╔══██╗ ██╔══██╗
    ██████╔╝ ██████╔╝
    ██╔══██╗ ██╔══██╗
    ██████╔╝ ██║  ██║
    ╚══════╝  ╚═╝  ╚═╝
      Powered by BR Core · Multi-Backend · 47 Tools · 45 Skills
"""

HELP_TEXT = """
[bold cyan]COMMANDS:[/]
  /mode <name>         Switch AI persona (recon/exploit/coder/analyst/planner/general)
  /tasks               Show active/queued tasks
  /run <goal1> | <goal2>  Run multiple goals in PARALLEL
  /skills              List all 45 built-in skills
  /skill <name>        Execute a skill directly
  /agents              List available sub-agent types
  /memory search <q>   Search persistent memories
  /memory list         List all stored memories
  /tools               Show all 43 available tools
  /history             Recent sessions
  /models              Current model configuration
  /clear               Clear conversation history
  /status              System health check
  /help                Show this help
  /quit                Exit (saves memories)

[bold cyan]PARALLEL EXECUTION:[/]
  Use [yellow]/run[/] to execute multiple goals simultaneously:
  > /run search Python news | download latest PyPI packages | update Steam games

  Or just ask naturally:
  > "Do three things: search AI news, open Chrome, and check my disk space"

[bold cyan]SKILLS (45 built-in):[/]
  /commit  /review  /edit  /research  /pc_control
  /tdd  /refactor  /security-scan  /osint  /docker-deploy
  /scaffold  /monitor  and 33 more...

[bold cyan]MODES:[/]
  general  coder  recon  exploit  analyst  planner  report

[bold cyan]TIPS:[/]
  - JARVIS can do multiple things at once — just ask!
  - Say "do X while also doing Y" for parallel execution
  - All tools run automatically (AUTO-ALLOW mode)
"""


def _show_task_status(router: AgentRouter):
    """Show current parallel task queue status."""
    try:
        from agent.task_queue import get_queue
        q = get_queue()
        statuses = q.get_all_statuses()
        if not statuses:
            console.print("[dim]No tasks in queue.[/]")
            return
        table = Table(title="Task Queue", border_style="cyan")
        table.add_column("ID", style="cyan")
        table.add_column("Goal", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Result", style="dim")
        for s in statuses[-10:]:
            status_color = {"running": "green", "completed": "blue", "failed": "red"}.get(s["status"], "white")
            table.add_row(
                s["task_id"],
                s["goal"][:40],
                f"[{status_color}]{s['status']}[/]",
                s.get("result", "")[:50] or "-"
            )
        console.print(table)
        console.print(f"[dim]Active: {q.active_count()} | Pending: {q.pending_count()}[/]")
    except Exception as e:
        console.print(f"[red]Task queue error: {e}[/]")


def _run_parallel_goals(goals_str: str, jarvis, speak=None):
    """Run multiple goals in parallel from /run command."""
    goals = [g.strip() for g in goals_str.split("|") if g.strip()]
    if not goals:
        console.print("[yellow]No goals specified.[/]")
        return

    if len(goals) == 1:
        # Single goal — run normally
        _chat_with_progress(goals[0], jarvis)
        return

    console.print(f"\n[bold green]⚡ Running {len(goals)} tasks in PARALLEL[/]")
    for i, g in enumerate(goals, 1):
        console.print(f"  [cyan]{i}.[/] {g}")
    console.print()

    from agent.task_queue import get_queue, TaskPriority
    q = get_queue()
    task_ids = q.submit_many(goals, priority=TaskPriority.NORMAL, speak=speak)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        tasks_progress = {
            tid: progress.add_task(f"[cyan]{goals[i][:40]}[/]", total=None)
            for i, tid in enumerate(task_ids)
        }

        while True:
            all_done = True
            for tid, ptask in tasks_progress.items():
                status = q.get_status(tid)
                if status and status["status"] not in ("completed", "failed", "cancelled"):
                    all_done = False
                elif status and status["status"] == "completed":
                    progress.update(ptask, description=f"[green]✓ {goals[task_ids.index(tid)][:35]}[/]")
                elif status and status["status"] == "failed":
                    progress.update(ptask, description=f"[red]✗ {goals[task_ids.index(tid)][:35]}[/]")
            if all_done:
                break
            import time
            time.sleep(0.5)

    console.print("\n[bold]Results:[/]")
    for i, tid in enumerate(task_ids):
        status = q.get_status(tid)
        if status:
            result = status.get("result", status.get("error", "No result"))
            console.print(Panel(
                Markdown(str(result)[:500]),
                title=f"[cyan]{goals[i][:40]}[/]",
                border_style="green" if status["status"] == "completed" else "red",
            ))


def _chat_with_progress(user_input: str, jarvis) -> str:
    """Send a message to JARVIS with a spinner indicator."""
    response = ""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold bright_blue]JARVIS is thinking...[/]"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("", total=None)
        try:
            response = jarvis.chat(user_input)
        except Exception as e:
            response = f"Error: {e}"
            traceback.print_exc()

    console.print(Panel(
        Markdown(response),
        title="[bold bright_blue]JARVIS[/]",
        border_style="bright_blue",
        padding=(1, 2),
    ))
    return response


def _handle_memory_command(args: str, jarvis):
    parts = args.strip().split(maxsplit=1)
    subcmd = parts[0].lower() if parts else "list"
    sub_args = parts[1] if len(parts) > 1 else ""

    if subcmd == "search" and sub_args:
        try:
            from memory.memory_context import find_relevant_memories
            results = find_relevant_memories(sub_args, max_results=5)
            if not results:
                console.print(f"[yellow]No memories found for '{sub_args}'[/]")
                return
            table = Table(title=f"Memories: '{sub_args}'", border_style="green")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Content", style="white")
            for r in results:
                table.add_row(r["name"], f"{r['type']}/{r['scope']}", r["content"][:80])
            console.print(table)
        except Exception as e:
            console.print(f"[red]Memory search error: {e}[/]")
    elif subcmd == "list":
        try:
            from memory.persistent_store import load_index
            entries = load_index("all")
            if not entries:
                console.print("[yellow]No memories stored.[/]")
                return
            table = Table(title="Persistent Memories", border_style="green")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Description", style="white")
            for e in entries:
                table.add_row(e.name, e.type, e.description[:60])
            console.print(table)
        except Exception as e:
            console.print(f"[red]Memory list error: {e}[/]")
    else:
        console.print("[yellow]Usage: /memory search <query>  |  /memory list[/]")


def _handle_history_command(args: str, jarvis):
    try:
        from history.session_store import SessionStore
        store = SessionStore()
    except Exception as e:
        console.print(f"[red]History unavailable: {e}[/]")
        return

    sessions = store.recent(10)
    if not sessions:
        console.print("[yellow]No sessions recorded yet.[/]")
        return
    table = Table(title="Recent Sessions", border_style="bright_blue")
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="white")
    table.add_column("Turns", style="dim")
    table.add_column("Summary", style="white")
    for s in sessions:
        ts = s.get("start_ts", 0)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M") if ts else "?"
        summary = (s.get("summary") or "")[:60]
        table.add_row(s["id"][:12], dt, str(s.get("turn_count", 0)), summary)
    console.print(table)


def main():
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

    try:
        console.print(Panel(Text(BANNER, style="bold cyan"), border_style="bright_blue"))
    except Exception:
        print(BANNER)

    console.print("\n[bold cyan]Initializing AI backends...[/]")
    runtime = build_assistant_runtime()
    backends = runtime.backends
    router = runtime.router

    if not backends:
        console.print("[bold red]ERROR: No backends available![/]")
        console.print("[yellow]Set your Gemini API key:[/]")
        console.print("  1. Create [cyan].env[/] file with: GEMINI_API_KEY=your_key")
        console.print("  2. OR add to [cyan]config/api_keys.json[/]: {\"gemini_api_key\": \"your_key\"}")
        sys.exit(1)

    from config.models import get_model_config
    default_name = get_model_config().get("default_backend", "gemini").upper()
    console.print(f"\n[bold green]✓ BR online[/] — {len(backends)} backend(s) | Model: {default_name}")
    console.print(f"[dim]Type /help for commands | /run goal1 | goal2 for parallel tasks | /quit to exit[/]\n")

    jarvis = runtime.orchestrator

    # Load skills silently
    try:
        from skills import load_skills
        from tools.registry import TOOL_SCHEMAS, _import_plugins
        _import_plugins()
        skill_count = len([s for s in load_skills() if s.user_invocable])
        tool_count = len(TOOL_SCHEMAS)
        console.print(f"  [dim]✓ {skill_count} skills loaded | {tool_count} tools ready | 3 parallel workers[/]\n")
    except Exception:
        pass

    # Pre-warm task queue
    from agent.task_queue import get_queue
    get_queue()

    # ── Main loop ──────────────────────────────────────────────────────────
    while True:
        try:
            user_input = console.input("[bold cyan]OPERATOR >[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Shutting down...[/]")
            jarvis.shutdown()
            break

        if not user_input:
            continue

        cmd = user_input.lower().strip()

        if cmd in ("/quit", "/exit", "exit", "quit", "bye"):
            console.print("[yellow]Consolidating memories...[/]")
            jarvis.shutdown()
            console.print("[bold yellow]Goodbye, sir.[/]")
            break

        elif cmd == "/help":
            console.print(HELP_TEXT)

        elif cmd == "/clear":
            jarvis.working_memory.history.clear()
            console.print("[green]Conversation cleared.[/]")

        elif cmd == "/tasks":
            _show_task_status(router)

        elif cmd.startswith("/run "):
            goals_str = user_input[5:].strip()
            _run_parallel_goals(goals_str, jarvis)

        elif cmd == "/skills":
            try:
                from skills import load_skills
                skills = [s for s in load_skills() if s.user_invocable]
                table = Table(title=f"Skills ({len(skills)})", border_style="magenta")
                table.add_column("Name", style="cyan bold")
                table.add_column("Trigger", style="yellow")
                table.add_column("Description", style="white")
                for s in skills:
                    table.add_row(s.name, ", ".join(s.triggers[:2]), s.description[:60])
                console.print(table)
            except Exception as e:
                console.print(f"[red]Skills error: {e}[/]")

        elif cmd == "/agents":
            try:
                from multi_agent.subagent import load_agent_definitions
                defs = load_agent_definitions()
                table = Table(title="Sub-Agent Types", border_style="blue")
                table.add_column("Type", style="cyan bold")
                table.add_column("Source", style="dim")
                table.add_column("Description", style="white")
                for name, d in sorted(defs.items()):
                    table.add_row(name, d.source, d.description[:70])
                console.print(table)
            except Exception as e:
                console.print(f"[red]Agents error: {e}[/]")

        elif cmd == "/tools":
            try:
                from tools.registry import TOOL_SCHEMAS, _import_plugins
                _import_plugins()
                table = Table(title=f"Tools ({len(TOOL_SCHEMAS)})", border_style="green")
                table.add_column("Tool", style="cyan bold")
                table.add_column("Description", style="white")
                for t in sorted(TOOL_SCHEMAS, key=lambda x: x["name"]):
                    table.add_row(t["name"], t["description"][:80])
                console.print(table)
            except Exception as e:
                console.print(f"[red]Tools error: {e}[/]")

        elif cmd == "/models":
            try:
                from config.models import get_model_config
                cfg = get_model_config()
                table = Table(title="Model Config", border_style="bright_blue")
                table.add_column("Setting", style="cyan")
                table.add_column("Value", style="white")
                for k in ("gemini", "claude", "gpt", "default_backend", "openai_base_url", "openai_model"):
                    table.add_row(k, cfg.get(k, "—"))
                console.print(table)
            except Exception as e:
                console.print(f"[red]Config error: {e}[/]")

        elif cmd.startswith("/backend"):
            args = user_input[8:].strip()
            if args:
                msg = router.switch_backend(args)
                console.print(f"[green]{msg}[/]")
            else:
                table = Table(title="Active Backends", border_style="bright_blue")
                table.add_column("Backend", style="cyan")
                table.add_column("Model Name", style="white")
                table.add_column("Default", style="green")
                status = router.get_status()
                for bk_name, info in status.items():
                    default_star = "★ DEFAULT" if info["is_default"] else ""
                    table.add_row(info["name"], info["model"], default_star)
                console.print(table)

        elif cmd == "/test":
            console.print("\n[bold cyan]Running connection tests to all active backends...[/]")
            for profile, backend in router.backends.items():
                start = time.monotonic()
                try:
                    ok = backend.ping(timeout=3.0)
                    elapsed = (time.monotonic() - start) * 1000
                    status_str = f"[green]ONLINE ({elapsed:.1f}ms)[/]" if ok else "[red]OFFLINE (ping failed)[/]"
                except Exception as e:
                    status_str = f"[red]FAILED ({e})[/]"
                console.print(f"  ● {backend.name:10s} ({backend.model_name}) -> {status_str}")
            console.print()

        elif cmd == "/status":
            table = Table(title="JARVIS Status", border_style="bright_blue")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Mode", jarvis.current_mode.upper())
            table.add_row("Backend", router.default.value)
            table.add_row("History", str(len(jarvis.working_memory.history)))
            table.add_row("Vector Memory", "Active" if jarvis.vector_memory else "Disabled")
            try:
                from agent.task_queue import get_queue
                q = get_queue()
                table.add_row("Active Tasks", str(q.active_count()))
                table.add_row("Queued Tasks", str(q.pending_count()))
            except Exception:
                pass
            console.print(table)

        elif cmd.startswith("/memory"):
            _handle_memory_command(cmd[7:].strip(), jarvis)

        elif cmd.startswith("/history"):
            _handle_history_command(cmd[8:].strip(), jarvis)

        elif cmd.startswith("/mode ") or cmd.startswith("/mode\t"):
            # Let orchestrator handle it
            result = jarvis.chat(user_input)
            console.print(f"[green]{result}[/]")

        elif cmd.startswith("/install-skills"):
            pack = user_input[15:].strip()
            if pack:
                try:
                    from skills.installer import install_skill_pack
                    console.print(f"[cyan]Installing {pack}...[/]")
                    console.print(install_skill_pack(pack))
                except Exception as e:
                    console.print(f"[red]Install failed: {e}[/]")
            else:
                console.print("[yellow]Usage: /install-skills <pack_name>[/]")

        else:
            # Normal chat — detect if multiple goals requested
            # Check for parallel indicators
            parallel_keywords = ["while also", "at the same time", "simultaneously", "in parallel", "also do", "and also"]
            if any(kw in cmd for kw in parallel_keywords) or (" and " in cmd and len(cmd) > 60):
                # Let JARVIS plan with agent_task for complex requests
                _chat_with_progress(user_input, jarvis)
            else:
                _chat_with_progress(user_input, jarvis)


if __name__ == "__main__":
    main()
