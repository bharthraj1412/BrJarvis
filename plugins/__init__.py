# plugins/__init__.py — JARVIS MK37 Dynamic Plugin Loader
"""
Handles scanning and dynamically importing third-party community plugins
from the plugins/ directory at startup.
"""
from __future__ import annotations

import json
import sys
import importlib.util
from pathlib import Path

# Ensure plugins/ folder is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def load_custom_plugins() -> list[dict]:
    """
    Scans the plugins/ directory for subfolders containing 'plugin.json'
    and imports their specified entry point Python scripts.
    """
    plugins_dir = Path(__file__).resolve().parent
    loaded_plugins = []

    if not plugins_dir.exists():
        return []

    for item in plugins_dir.iterdir():
        if item.is_dir() and not item.name.startswith("__"):
            json_path = item / "plugin.json"
            if json_path.exists():
                try:
                    meta = json.loads(json_path.read_text(encoding="utf-8"))
                    name = meta.get("name", item.name)
                    entry_point = meta.get("entry_point", "main.py")
                    script_path = item / entry_point

                    if script_path.exists():
                        # Dynamically load the python file
                        spec = importlib.util.spec_from_file_location(
                            f"custom_plugin_{item.name}", str(script_path)
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[spec.name] = module
                            spec.loader.exec_module(module)
                            
                            loaded_plugins.append({
                                "name": name,
                                "version": meta.get("version", "1.0.0"),
                                "description": meta.get("description", ""),
                                "author": meta.get("author", "Unknown"),
                            })
                            print(f"[Plugins] ✅ Loaded custom plugin '{name}' from {item.name}")
                except Exception as e:
                    print(f"[Plugins] ⚠️  Failed to load custom plugin in {item.name}: {e}")

    return loaded_plugins
