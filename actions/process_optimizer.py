# actions/process_optimizer.py — Process Prioritization & Optimization Action for JARVIS MK37
"""
Autonomous action for process priority management, identifying memory hogs,
and terminating unresponsive background tasks.
"""
from __future__ import annotations

import psutil


class ProcessOptimizerAction:
    """Process Telemetry and Priority Optimization Manager."""

    def find_memory_hogs(self, limit_mb: float = 500.0) -> list[dict]:
        hogs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                info = p.info
                mem_mb = (info['memory_info'].rss / (1024 * 1024)) if info.get('memory_info') else 0
                if mem_mb >= limit_mb:
                    hogs.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'mem_mb': round(mem_mb, 1),
                        'cpu': info.get('cpu_percent', 0)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sorted(hogs, key=lambda x: x['mem_mb'], reverse=True)

    def optimize_processes(self, min_memory_mb: float = 600.0) -> str:
        hogs = self.find_memory_hogs(limit_mb=min_memory_mb)
        if not hogs:
            return f"✅ Process Optimizer: No background processes exceeding {min_memory_mb} MB RAM threshold."

        lines = [f"⚡ High-Resource Processes Identified (>{min_memory_mb} MB RAM):"]
        for h in hogs[:10]:
            lines.append(f"  ● PID {h['pid']:<6} | {h['name']:<25} | Memory: {h['mem_mb']} MB | CPU: {h['cpu']}%")

        return "\n".join(lines)


def run_process_optimization(threshold_mb: float = 600.0) -> str:
    action = ProcessOptimizerAction()
    return action.optimize_processes(min_memory_mb=threshold_mb)
