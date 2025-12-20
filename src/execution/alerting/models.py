"""
Alert Models - Phase 16I

Data models for telemetry alerting system.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    
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
    Alert event with metadata for routing and deduplication.
    
    Attributes:
        id: Unique alert ID (generated if not provided)
        timestamp_utc: Alert timestamp (UTC, generated if not provided)
        source: Alert source (e.g., "health_check", "trend_degradation")
        severity: Alert severity (info/warn/critical)
        title: Short alert title (< 100 chars)
        body: Detailed alert message
        labels: Key-value labels for filtering/routing
        dedupe_key: Key for deduplication (same key = same alert)
        sample_payload: Optional raw data that triggered alert
    """
    
    source: str
    severity: AlertSeverity
    title: str
    body: str
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    labels: Dict[str, str] = field(default_factory=dict)
    dedupe_key: Optional[str] = None
    sample_payload: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Ensure severity is AlertSeverity enum."""
        if isinstance(self.severity, str):
            self.severity = AlertSeverity(self.severity)
        
        # Generate dedupe_key if not provided
        if self.dedupe_key is None:
            self.dedupe_key = f"{self.source}:{self.title}"
    
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
            "dedupe_key": self.dedupe_key,
            "sample_payload": self.sample_payload,
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
            dedupe_key=data.get("dedupe_key"),
            sample_payload=data.get("sample_payload"),
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
        
        if self.sample_payload:
            lines.append(f"  Sample: {self.sample_payload}")
        
        return "\n".join(lines)
