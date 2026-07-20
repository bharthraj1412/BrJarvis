# 🔒 BR JARVIS — Security Architecture & Permission Interlock

## Overview
BR JARVIS implements strict security policies to protect user data, filesystem integrity, and system safety during autonomous computer operations.

---

## 🛡️ Security Layers

1. **Permission Policy (`permissions.py`)**:
   - `ALLOW_ALL`: Standard development mode.
   - `CONFIRM_ALL`: Requires confirmation for non-safe tools.
   - `DENY_ALL`: Blocks all actions except safe read-only tools.
2. **Human-in-the-Loop Interlock**:
   - Destructive keywords (`delete`, `remove`, `format`, `push`, `deploy`, `drop`, `purchase`, `shutdown`) trigger `requires_approval=True`.
   - The `ParallelExecutionEngine` pauses step execution when `requires_approval=True` and emits `task.step.approval_required`.
3. **Emergency Stop (`cancel_all()`)**:
   - Interruption mechanism instantly terminates all active background tasks and worker threads.
