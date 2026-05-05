#!/usr/bin/env python3
# setup_upgrade.py — JARVIS MK37 Upgrade Installer
"""
Applies the Gemini-native upgrade to your JARVIS MK37 installation.
Run from your JARVIS project root:
    python setup_upgrade.py

What this does:
1. Creates .env template with your API key slot
2. Upgrades all core files to Gemini-native versions
3. Installs/verifies required packages
4. Runs a quick sanity check
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# ── The upgraded files to copy ─────────────────────────────────────────────
UPGRADE_DIR = Path(__file__).parent
if len(sys.argv) > 1 and sys.argv[1].strip():
    TARGET_DIR = Path(sys.argv[1]).resolve()
else:
    # Non-interactive safe default: current directory
    try:
        # If running interactively, allow user to specify a path
        if sys.stdin.isatty():
            TARGET_DIR = Path(input("Enter your JARVIS project root path (or press Enter for current dir): ").strip() or ".").resolve()
        else:
            TARGET_DIR = Path('.').resolve()
    except Exception:
        TARGET_DIR = Path('.').resolve()

FILES_TO_UPGRADE = [
    # (source_relative, target_relative)
    ("gemini_backend.py",           "gemini_backend.py"),
    ("router.py",                   "router.py"),
    ("orchestrator.py",             "orchestrator.py"),
    ("main_mk37.py",                "main_mk37.py"),
    ("config/models.py",            "config/models.py"),
    ("agent/planner.py",            "agent/planner.py"),
    ("agent/executor.py",           "agent/executor.py"),
    ("agent/task_queue.py",         "agent/task_queue.py"),
    ("actions/web_search.py",       "actions/web_search.py"),
    ("actions/code_helper.py",      "actions/code_helper.py"),
    ("actions/dev_agent.py",        "actions/dev_agent.py"),
]

REQUIRED_PACKAGES = [
    "google-genai",
    "google-generativeai",
    "rich",
    "python-dotenv",
    "requests",
    "duckduckgo-search",
]

ENV_TEMPLATE = """\
# JARVIS MK37 Environment Configuration
# Only GEMINI_API_KEY is required — all others are optional

# ── REQUIRED ───────────────────────────────────────────────
GEMINI_API_KEY=your_gemini_api_key_here

# ── OPTIONAL (additional AI backends) ──────────────────────
# ANTHROPIC_API_KEY=your_claude_key
# OPENAI_API_KEY=your_openai_key
# MISTRAL_API_KEY=your_mistral_key
# NVIDIA_API_KEY=your_nvidia_key
# OLLAMA_HOST=http://localhost:11434

# ── MODEL OVERRIDES (optional) ─────────────────────────────
# JARVIS_MODEL_GEMINI=gemini-2.5-flash
# JARVIS_DEFAULT_BACKEND=gemini
"""


def print_step(msg: str):
    print(f"\n  ✦ {msg}")


def print_ok(msg: str):
    print(f"    [✓] {msg}")


def print_warn(msg: str):
    print(f"    [!] {msg}")


def main():
    print("\n" + "="*60)
    print("  JARVIS MK37 — Gemini-Native Upgrade")
    print("="*60)
    print(f"  Target: {TARGET_DIR}")
    print()

    if not TARGET_DIR.exists():
        print(f"ERROR: Target directory not found: {TARGET_DIR}")
        sys.exit(1)

    # 1. Create .env template
    print_step("Setting up .env configuration...")
    env_path = TARGET_DIR / ".env"
    if not env_path.exists():
        env_path.write_text(ENV_TEMPLATE, encoding="utf-8")
        print_ok(f"Created .env template — add your GEMINI_API_KEY!")
    else:
        # Add missing keys to existing .env
        existing = env_path.read_text(encoding="utf-8")
        if "GEMINI_API_KEY" not in existing:
            with open(env_path, "a") as f:
                f.write("\n# Added by upgrade\nGEMINI_API_KEY=your_gemini_api_key_here\n")
            print_ok("Added GEMINI_API_KEY slot to existing .env")
        else:
            print_ok(".env already configured")

    # 2. Upgrade core files
    print_step("Upgrading core files...")
    upgraded = 0
    for src_rel, tgt_rel in FILES_TO_UPGRADE:
        src = UPGRADE_DIR / src_rel
        tgt = TARGET_DIR / tgt_rel
        if not src.exists():
            print_warn(f"Source not found: {src_rel} (skipping)")
            continue
        tgt.parent.mkdir(parents=True, exist_ok=True)
        # Backup original
        if tgt.exists():
            bak = tgt.with_suffix(tgt.suffix + ".bak")
            shutil.copy2(tgt, bak)
        shutil.copy2(src, tgt)
        print_ok(f"Upgraded: {tgt_rel}")
        upgraded += 1

    # 3. Update config/api_keys.json if it exists (ensure gemini key slot)
    api_keys_path = TARGET_DIR / "config" / "api_keys.json"
    if api_keys_path.exists():
        import json
        try:
            data = json.loads(api_keys_path.read_text(encoding="utf-8"))
            if "gemini_api_key" not in data:
                data["gemini_api_key"] = ""
                api_keys_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print_ok("Added gemini_api_key slot to config/api_keys.json")
        except Exception:
            pass

    # 4. Install required packages
    print_step("Installing required packages...")
    for pkg in REQUIRED_PACKAGES:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print_ok(f"Installed: {pkg}")
            else:
                print_warn(f"Failed: {pkg} — {result.stderr[:60]}")
        except Exception as e:
            print_warn(f"Could not install {pkg}: {e}")

    # 5. Quick sanity check
    print_step("Running sanity check...")
    try:
        sys.path.insert(0, str(TARGET_DIR))
        import google.genai
        print_ok("google-genai SDK available")
    except ImportError:
        print_warn("google-genai not found — run: pip install google-genai")

    try:
        from rich.console import Console
        print_ok("rich console available")
    except ImportError:
        print_warn("rich not found — run: pip install rich")

    print("\n" + "="*60)
    print(f"  ✅ Upgrade complete! {upgraded}/{len(FILES_TO_UPGRADE)} files upgraded.")
    print()
    print("  NEXT STEPS:")
    print(f"  1. Edit {env_path.name} and add your GEMINI_API_KEY")
    print("  2. Run: python main_mk37.py     (CLI mode)")
    print("  3. Run: python main.py          (Voice mode)")
    print()
    print("  PARALLEL TASKS:")
    print("  > /run search AI news | update Steam | open Chrome")
    print("="*60)


if __name__ == "__main__":
    main()
