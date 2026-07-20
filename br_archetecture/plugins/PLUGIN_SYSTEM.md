# 🔌 BR JARVIS — Dynamic Plugin Platform Engine (`plugins/`)

## Overview
The Plugin Platform enables third-party developers and community contributors to extend BR JARVIS with custom skills, tools, and integrations without modifying core system files.

---

## 🏗️ Plugin Package Structure

Every plugin resides in a subfolder inside `plugins/` containing a `plugin.json` manifest:

```
plugins/
└── my_custom_plugin/
    ├── plugin.json       # Manifest metadata
    └── main.py           # Python entry point
```

### Manifest Format (`plugin.json`)
```json
{
  "name": "My Custom Plugin",
  "version": "1.0.0",
  "description": "Adds custom workspace tools",
  "author": "Community Developer",
  "entry_point": "main.py"
}
```

### Entry Point (`main.py`)
```python
def on_load(runtime):
    """Lifecycle hook invoked when plugin is loaded."""
    print(f"Plugin loaded into {runtime.config.assistant.name}")
```

---

## 🛡️ Sandbox & Crash Isolation
The `PluginManager` dynamically loads plugin modules inside isolated `try/except` wrappers. If a plugin throws an exception during initialization or execution, it is marked `FAILED` without crashing the core AI Operating System.
