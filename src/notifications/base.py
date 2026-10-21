"""Minimal alert types for the test-health Slack adapter.

Live-workflow helpers stay absent from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal, Protocol, runtime_checkable


@dataclass
class Alert:
    """One local alert record. Construction does not deliver it."""

    level: Literal["info", "warning", "critical"]
    source: str
    message: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        valid_levels = ("info", "warning", "critical")
        if self.level not in valid_levels:
            raise ValueError(f"Invalid alert level: {self.level}. Must be one of {valid_levels}")
        if not self.source:
            raise ValueError("Alert source cannot be empty")
        if not self.message:
            raise ValueError("Alert message cannot be empty")


@runtime_checkable
class Notifier(Protocol):
    """Local send interface. Implementations decide whether delivery exists."""

    def send(self, alert: Alert) -> None:
        """Accept one alert."""
