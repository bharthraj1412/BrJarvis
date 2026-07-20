# core/retry.py — Generic Retry & Backoff Decorator for BR JARVIS
"""
Provides a configurable retry decorator with exponential backoff for
external API calls, tool executions, and network operations.

Usage:
    @retry(max_attempts=3, backoff_factor=2.0, exceptions=(ConnectionError, TimeoutError))
    async def call_api():
        ...
"""
from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import time
from typing import Any, Callable, Sequence, Type

logger = logging.getLogger("JARVIS.Retry")


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Sequence[Type[BaseException]] = (Exception,),
    on_retry: Callable[[int, BaseException], None] | None = None,
):
    """Decorator that retries a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including the first call).
        backoff_factor: Multiplier for delay between retries.
                        delay = backoff_factor * (2 ** (attempt - 1))
        max_delay: Maximum delay in seconds between retries.
        exceptions: Tuple of exception types to catch and retry on.
        on_retry: Optional callback invoked before each retry with (attempt, exception).
    """
    catchable = tuple(exceptions)

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: BaseException | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except catchable as exc:
                        last_exc = exc
                        if attempt >= max_attempts:
                            logger.error(
                                f"[Retry] {func.__name__} failed after {max_attempts} attempts: {exc}"
                            )
                            raise
                        delay = min(backoff_factor * (2 ** (attempt - 1)), max_delay)
                        logger.warning(
                            f"[Retry] {func.__name__} attempt {attempt}/{max_attempts} "
                            f"failed ({type(exc).__name__}), retrying in {delay:.1f}s"
                        )
                        if on_retry:
                            on_retry(attempt, exc)
                        await asyncio.sleep(delay)
                raise last_exc  # type: ignore[misc]
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: BaseException | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except catchable as exc:
                        last_exc = exc
                        if attempt >= max_attempts:
                            logger.error(
                                f"[Retry] {func.__name__} failed after {max_attempts} attempts: {exc}"
                            )
                            raise
                        delay = min(backoff_factor * (2 ** (attempt - 1)), max_delay)
                        logger.warning(
                            f"[Retry] {func.__name__} attempt {attempt}/{max_attempts} "
                            f"failed ({type(exc).__name__}), retrying in {delay:.1f}s"
                        )
                        if on_retry:
                            on_retry(attempt, exc)
                        time.sleep(delay)
                raise last_exc  # type: ignore[misc]
            return sync_wrapper
    return decorator
