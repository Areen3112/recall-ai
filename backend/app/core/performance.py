"""PII-free timing instrumentation for awaited workflow stages."""

import logging
from contextvars import ContextVar
from contextlib import asynccontextmanager
from time import perf_counter
from typing import AsyncIterator, Callable

_TIMING_LOGGER = logging.getLogger("uvicorn.error.workflow_timing")
_CURRENT_CORRELATION_ID: ContextVar[str | None] = ContextVar(
    "workflow_correlation_id", default=None
)


def current_correlation_id() -> str | None:
    """Return the safe request correlation ID for diagnostics inside a timed stage."""
    return _CURRENT_CORRELATION_ID.get()


@asynccontextmanager
async def log_async_stage(
    stage: str, correlation_id: str
) -> AsyncIterator[Callable[[], None]]:
    started = perf_counter()
    correlation_token = _CURRENT_CORRELATION_ID.set(correlation_id)
    success = False
    explicitly_failed = False

    def mark_failed() -> None:
        nonlocal explicitly_failed
        explicitly_failed = True

    try:
        yield mark_failed
        success = True
    finally:
        success = success and not explicitly_failed
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        outcome = "success" if success else "failure"
        # Uvicorn's default logging config sends uvicorn.error descendants to
        # its console handler at INFO. The app.* namespace inherits root WARNING
        # and has no console handler under that config, so its INFO records vanish.
        try:
            _TIMING_LOGGER.info(
                "workflow_stage_timing stage=%s elapsed_ms=%s outcome=%s correlation_id=%s",
                stage,
                elapsed_ms,
                outcome,
                correlation_id,
                extra={
                    "event": "workflow_stage_timing",
                    "stage": stage,
                    "elapsed_ms": elapsed_ms,
                    "outcome": outcome,
                    "correlation_id": correlation_id,
                },
            )
        finally:
            _CURRENT_CORRELATION_ID.reset(correlation_token)
