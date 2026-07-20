# core/health.py — Hardware Metrics & Health Check Registry for JARVIS MK37
from __future__ import annotations

import logging
import os
import shutil
import time
from typing import Callable, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from core.native_bridge import is_native_active, get_status as get_native_status

logger = logging.getLogger("JARVIS.Health")


class HardwareMetrics(BaseModel):
    cpu_percent: float = 0.0
    memory_used_percent: float = 0.0
    memory_available_mb: float = 0.0
    disk_used_percent: float = 0.0
    native_c_bridge_active: bool = False
    timestamp: float = Field(default_factory=time.time)


class ComponentHealth(BaseModel):
    name: str
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    message: str = "OK"
    latency_ms: Optional[float] = None


class HealthReport(BaseModel):
    overall_status: str  # HEALTHY, DEGRADED, UNHEALTHY
    hardware: HardwareMetrics
    components: Dict[str, ComponentHealth]


class HealthMonitor:
    """Monitors system hardware usage and manages component health checks."""

    def __init__(self):
        self._checkers: Dict[str, Callable[[], ComponentHealth]] = {}

    def register_check(self, name: str, check_fn: Callable[[], ComponentHealth]) -> None:
        """Register a health check callback for a component."""
        self._checkers[name] = check_fn

    def get_hardware_metrics(self) -> HardwareMetrics:
        """Collect current OS hardware utilization statistics."""
        cpu = 0.0
        mem_pct = 0.0
        mem_avail_mb = 0.0

        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                mem_pct = mem.percent
                mem_avail_mb = mem.available / (1024 * 1024)
            except Exception:
                pass

        # Disk
        disk_pct = 0.0
        try:
            total, used, free = shutil.disk_usage(".")
            disk_pct = (used / total) * 100.0
        except Exception:
            pass

        return HardwareMetrics(
            cpu_percent=cpu,
            memory_used_percent=mem_pct,
            memory_available_mb=mem_avail_mb,
            disk_used_percent=disk_pct,
            native_c_bridge_active=is_native_active(),
        )

    def generate_report(self) -> HealthReport:
        """Run all registered checks and return an aggregated HealthReport."""
        hardware = self.get_hardware_metrics()
        components: Dict[str, ComponentHealth] = {}
        has_degraded = False
        has_unhealthy = False

        # Built-in check: Native Bridge
        native_stat = get_native_status()
        components["c_native_bridge"] = ComponentHealth(
            name="c_native_bridge",
            status="HEALTHY" if native_stat["active"] else "DEGRADED",
            message=f"Library v{native_stat['version']}" if native_stat["active"] else "Python Fallback Active",
        )

        for name, fn in self._checkers.items():
            try:
                t0 = time.perf_counter()
                res = fn()
                res.latency_ms = (time.perf_counter() - t0) * 1000.0
                components[name] = res
                if res.status == "DEGRADED":
                    has_degraded = True
                elif res.status == "UNHEALTHY":
                    has_unhealthy = True
            except Exception as e:
                components[name] = ComponentHealth(name=name, status="UNHEALTHY", message=str(e))
                has_unhealthy = True

        overall = "HEALTHY"
        if has_unhealthy:
            overall = "UNHEALTHY"
        elif has_degraded or hardware.cpu_percent > 95.0 or hardware.memory_used_percent > 90.0:
            overall = "DEGRADED"

        return HealthReport(overall_status=overall, hardware=hardware, components=components)
