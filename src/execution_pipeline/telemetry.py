"""
Telemetry emitters for execution_pipeline v0.

Watch-only: emitters can write append-only JSONL, but MUST NOT trigger any
external side effects (no network calls).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .events_v0 import ExecutionEventV0

logger = logging.getLogger(__name__)


class TelemetryEmitter(Protocol):
    def emit(self, event: ExecutionEventV0) -> None: ...


class NullTelemetryEmitter:
    def emit(self, event: ExecutionEventV0) -> None:
        return None


@dataclass
class JsonlTelemetryEmitter:
    """
    Append-only JSONL emitter.

    Default path is compatible with existing repo patterns under `logs/execution`.
    """

    root: Path = Path("logs/execution")
    filename: str = "execution_pipeline_events_v0.jsonl"

    def emit(self, event: ExecutionEventV0) -> None:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            p = self.root / self.filename
            with p.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        except Exception as e:
            logger.error("Failed to emit execution_pipeline event: %s", e)
