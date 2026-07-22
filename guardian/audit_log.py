# guardian/audit_log.py — Append-Only Human-Readable Autonomy Audit Log
"""
Append-only Audit Log for autonomous actions, self-upgrades, and routing shifts.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

AUDIT_LOG_FILE = Path("workspace/logs/autonomy_audit.jsonl")


class AuditLog:
    """Human-readable append-only ledger of autonomous events."""

    @classmethod
    def log(
        cls,
        event_type: str,
        title: str,
        details: dict | str,
        risk_level: str = "LOW",
        applied: bool = True,
    ) -> dict:
        """Log an autonomous action or patch to the audit log."""
        record = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": event_type,
            "title": title,
            "details": details if isinstance(details, dict) else {"message": str(details)},
            "risk_level": risk_level.upper(),
            "applied": applied,
        }
        try:
            AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[Guardian.AuditLog] Write error: {e}")
        return record

    @classmethod
    def get_recent(cls, count: int = 50) -> list[dict]:
        """Retrieve recent N audit log records."""
        if not AUDIT_LOG_FILE.exists():
            return []
        records = []
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-count:]:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except Exception as e:
            print(f"[Guardian.AuditLog] Read error: {e}")
        return records
