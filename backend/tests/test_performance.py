import logging

import pytest

from app.core.performance import log_async_stage

TIMING_LOGGER_NAME = "uvicorn.error.workflow_timing"


class RecordCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record):
        self.records.append(record)


@pytest.mark.asyncio
async def test_stage_timing_logs_safe_fields_on_success():
    logger = logging.getLogger(TIMING_LOGGER_NAME)
    correlation_id = "f92cc118-f005-4882-b2d4-9fbc404e6412"
    capture = RecordCapture()
    original_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(capture)

    try:
        async with log_async_stage("groq_generation", correlation_id):
            pass
    finally:
        logger.removeHandler(capture)
        logger.setLevel(original_level)

    record = capture.records[0]
    assert record.event == "workflow_stage_timing"
    assert record.stage == "groq_generation"
    assert record.elapsed_ms >= 0
    assert record.outcome == "success"
    assert record.correlation_id == correlation_id
    assert "workflow_stage_timing" in record.getMessage()
    assert "stage=groq_generation" in record.getMessage()
    assert "elapsed_ms=" in record.getMessage()
    assert "outcome=success" in record.getMessage()
    assert f"correlation_id={correlation_id}" in record.getMessage()


@pytest.mark.asyncio
async def test_stage_timing_logs_failure_without_exception_details():
    logger = logging.getLogger(TIMING_LOGGER_NAME)
    capture = RecordCapture()
    original_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(capture)

    try:
        with pytest.raises(RuntimeError):
            async with log_async_stage("hindsight_memory_recall", "safe-correlation-id"):
                raise RuntimeError("private customer message must not be logged")
    finally:
        logger.removeHandler(capture)
        logger.setLevel(original_level)

    record = capture.records[0]
    assert record.outcome == "failure"
    assert "private customer message" not in record.getMessage()
