"""
Risk Layer Alert Models
========================

Data models for risk-layer alerting system.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class AlertSeverity(str, Enum):
    """Alert severity levels for risk events."""

    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"

    @property
    def priority(self) -> int:
        """Numeric priority for sorting (higher = more severe)."""
        return {
            AlertSeverity.INFO: 1,
            AlertSeverity.WARN: 2,
            AlertSeverity.CRITICAL: 3,
        }[self]


@dataclass
class AlertEvent:
    """
    Risk alert event with metadata for routing and delivery.

    Attributes:
        id: Unique alert ID (generated if not provided)
        timestamp_utc: Alert timestamp (UTC, generated if not provided)
        source: Alert source (e.g., "risk_gate", "kill_switch", "var_gate")
        severity: Alert severity (info/warn/critical)
        title: Short alert title (< 100 chars)
        body: Detailed alert message
        labels: Key-value labels for filtering/routing
        metadata: Additional metadata for channel-specific formatting
    """

    source: str
    severity: AlertSeverity
    title: str
    body: str

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Ensure severity is AlertSeverity enum."""
        if isinstance(self.severity, str):
            self.severity = AlertSeverity(self.severity)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "id": self.id,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "source": self.source,
            "severity": self.severity.value,
            "title": self.title,
            "body": self.body,
            "labels": self.labels,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertEvent":
        """Load alert from dict."""
        timestamp_str = data.get("timestamp_utc", "")
        timestamp_utc = (
            datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if timestamp_str
            else datetime.now(timezone.utc)
        )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            timestamp_utc=timestamp_utc,
            source=data["source"],
            severity=AlertSeverity(data["severity"]),
            title=data["title"],
            body=data["body"],
            labels=data.get("labels", {}),
            metadata=data.get("metadata"),
        )

    def format_console(self) -> str:
        """Format alert for console output."""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️ ",
            AlertSeverity.WARN: "⚠️ ",
            AlertSeverity.CRITICAL: "🔴",
        }
        emoji = severity_emoji.get(self.severity, "")

        lines = [
            f"{emoji} [{self.severity.value.upper()}] {self.title}",
            f"  Source: {self.source}",
            f"  Time: {self.timestamp_utc.isoformat()}",
        ]

        if self.labels:
            labels_str = ", ".join(f"{k}={v}" for k, v in self.labels.items())
            lines.append(f"  Labels: {labels_str}")

        lines.append(f"  Message: {self.body}")

        if self.metadata:
            lines.append(f"  Metadata: {self.metadata}")

        return "\n".join(lines)
