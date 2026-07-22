# guardian/core.py — Master Guardian Core Safety Engine
"""
Master Guardian Core Safety Engine.
Boots first, verifies integrity hashes, holds permissions, and coordinates pause/rollback states.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from guardian.kill_switch import KillSwitch
from guardian.snapshot import SnapshotManager
from guardian.rollback import RollbackEngine
from guardian.audit_log import AuditLog

PROTECTED_CORE_PATHS = [
    "guardian/core.py",
    "guardian/kill_switch.py",
    "guardian/snapshot.py",
    "guardian/rollback.py",
    "guardian/audit_log.py",
    "permissions.py",
]


class GuardianCore:
    """Master Immutable Safety Core."""

    def __init__(self, integrity_interval: int = 300):
        self.integrity_interval = integrity_interval
        self._initial_hashes = self._calculate_hashes()
        self._last_check = time.time()

    def _calculate_hashes(self) -> dict[str, str]:
        hashes = {}
        for path_str in PROTECTED_CORE_PATHS:
            p = Path(path_str)
            if p.exists():
                try:
                    data = p.read_bytes()
                    hashes[path_str] = hashlib.sha256(data).hexdigest()
                except Exception:
                    pass
        return hashes

    def verify_integrity(self) -> dict:
        """Verify core safety files have not been modified outside release process."""
        current_hashes = self._calculate_hashes()
        mismatches = []
        for path_str, original_hash in self._initial_hashes.items():
            current_hash = current_hashes.get(path_str)
            if current_hash != original_hash:
                mismatches.append(path_str)

        self._last_check = time.time()

        if mismatches:
            # Trigger pause & audit log
            msg = f"Guardian Integrity Mismatch in files: {mismatches}"
            KillSwitch.pause(reason=msg)
            AuditLog.log(
                event_type="GUARDIAN_INTEGRITY_MISMATCH",
                title="Integrity Failure",
                details={"mismatches": mismatches},
                risk_level="HIGH",
                applied=False,
            )
            return {"valid": False, "mismatches": mismatches}

        return {"valid": True, "mismatches": []}

    def check_execution_safety(self) -> bool:
        """Return False if execution is paused or integrity failed."""
        if KillSwitch.is_paused():
            return False

        if time.time() - self._last_check > self.integrity_interval:
            res = self.verify_integrity()
            if not res["valid"]:
                return False

        return True
