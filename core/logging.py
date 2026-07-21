# core/logging.py — Structured JSON & Console Logging Framework for JARVIS MK37
from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Context Var for Correlation IDs across async tasks
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="sys-init")


class JSONFormatter(logging.Formatter):
    """Machine-readable JSON log formatter with context vars."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry["data"] = record.extra_data
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class ColoredConsoleFormatter(logging.Formatter):
    """Human-readable colorized console log formatter."""
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[41m", # Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        cid = correlation_id_ctx.get()
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"{color}[{record.levelname[:1]} {timestamp}][{cid[:8]}]{self.RESET}"
        msg = f"{prefix} \033[1m{record.name}\033[0m: {record.getMessage()}"
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        return msg


def setup_logger(name: str = "JARVIS", level: str = "INFO", log_to_file: bool = True) -> logging.Logger:
    """Configures and returns a structured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    if logger.handlers:
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredConsoleFormatter())
    logger.addHandler(console_handler)

    # File Handler (JSONL)
    if log_to_file:
        file_path = LOGS_DIR / "jarvis.jsonl"
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


class LogTimer:
    """Context manager for timing operational code blocks."""
    def __init__(self, logger: logging.Logger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.logger.debug(f"▶ Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        if exc_type:
            self.logger.error(f"❌ Failed: {self.operation_name} after {duration_ms:.2f}ms ({exc_val})")
        else:
            self.logger.info(f"✓ Completed: {self.operation_name} in {duration_ms:.2f}ms")
