# 🖥️ BR JARVIS — Computer Operator Subsystem (`computer/`)

## Overview
The Computer Operator enables BR JARVIS to interact with operating systems (Windows, Linux, macOS) through direct screen vision, keyboard/mouse emulation, application window management, and terminal execution.

---

## 🛠️ Operating Model

```
Observe (Screen Capture / OCR)
       ↓
Understand (UI Element Model)
       ↓
Plan (Action Steps / DAG Node)
       ↓
Execute (Mouse / Keyboard Control)
       ↓
Verify (State Check / Verification Loop)
       ↓
Recover (Re-plan on Failure)
```

---

## 🛡️ Safety & Approval Interlock
Destructive operations (e.g. file deletion, system configuration changes, formatting drives) automatically set `requires_approval=True` and pause execution until explicit user confirmation is received via the `ParallelExecutionEngine` safety interlock.
