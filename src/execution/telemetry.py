# src/execution/telemetry.py
"""
Execution Telemetry - Event Emitters & Loggers.

Phase 16B: Pluggable telemetry backends for execution events.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from .events import ExecutionEvent

logger = logging.getLogger(__name__)


class ExecutionEventEmitter(ABC):
    """
    Abstract base for execution event emitters.

    Implementations can log to files, send to monitoring systems,
    or integrate with observability platforms.
    """

    @abstractmethod
    def emit(self, event: ExecutionEvent) -> None:
        """
        Emit an execution event.

        Args:
            event: ExecutionEvent to emit
        """
        raise NotImplementedError


class NullEmitter(ExecutionEventEmitter):
    """
    Null emitter - does nothing.

    Useful for disabling telemetry or as default.
    """

    def emit(self, event: ExecutionEvent) -> None:
        """No-op emit."""
        pass


class JsonlExecutionLogger(ExecutionEventEmitter):
    """
    JSONL file logger for execution events.

    Appends events to logs/execution/<session_id>.jsonl.
    Creates directories if needed.

    Format: One JSON object per line (JSONL).

    Example:
        logger = JsonlExecutionLogger("logs/execution")
        logger.emit(event)
        # Creates: logs/execution/<session_id>.jsonl
    """

    def __init__(self, base_path: str = "logs/execution", *, fixed_filename: Optional[str] = None):
        """
        Initialize JSONL logger.

        Args:
            base_path: Base directory for execution logs
            fixed_filename: If set, write all events to a single JSONL file
                           (e.g. "execution_events.jsonl") instead of <session_id>.jsonl.
        """
        self.base_path = Path(base_path)
        self.fixed_filename = fixed_filename
        self._handles: dict[str, Path] = {}

    def _get_log_path(self, session_id: str) -> Path:
        """Get log file path for session."""
        if self.fixed_filename:
            return self.base_path / self.fixed_filename
        return self.base_path / f"{session_id}.jsonl"

    def emit(self, event: ExecutionEvent) -> None:
        """
        Emit event to JSONL file.

        Args:
            event: ExecutionEvent to log
        """
        try:
            # Ensure directory exists
            log_path = self._get_log_path(event.session_id)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Append event as JSON line
            with log_path.open("a") as f:
                json_line = json.dumps(event.to_dict())
                f.write(json_line + "\n")

        except Exception as e:
            logger.error(f"Failed to emit execution event: {e}")


class FixedJsonlAppendOnlyWriter:
    """
    Minimal append-only JSONL writer for contract logs.

    Used by RUNBOOK B / Slice 1 for writing:
      logs/execution/execution_events.jsonl
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def append(self, obj: dict[str, Any]) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("a") as f:
                f.write(json.dumps(obj, sort_keys=True) + "\n")
        except Exception as e:
            logger.error(f"Failed to append JSONL event: {e}")


class CompositeEmitter(ExecutionEventEmitter):
    """
    Composite emitter - emits to multiple backends.

    Example:
        emitter = CompositeEmitter([
            JsonlExecutionLogger(),
            PrometheusEmitter(),
        ])
    """

    def __init__(self, emitters: list[ExecutionEventEmitter]):
        """
        Initialize composite emitter.

        Args:
            emitters: List of emitters to emit to
        """
        self.emitters = emitters

    def emit(self, event: ExecutionEvent) -> None:
        """
        Emit to all emitters.

        Args:
            event: ExecutionEvent to emit
        """
        for emitter in self.emitters:
            try:
                emitter.emit(event)
            except Exception as e:
                logger.error(f"Emitter {emitter.__class__.__name__} failed: {e}")
