"""
Telemetry Alerting - Phase 16I

Real-time alerting and incident hooks on top of health + trend analysis.

Core Components:
- models: AlertSeverity, AlertEvent
- rules: AlertRule, rule evaluation
- engine: AlertEngine (evaluate, dedupe, cooldown, rate limiting)
- adapters: AlertSink protocol (console, webhook)

Features:
- Config-driven (default: disabled)
- Dry-run mode (no external calls)
- Dedupe + cooldown logic
- Rate limiting
- Deterministic alert ordering

Phase 16I: Real-time Alerting (Phases 16F+16H → actionable alerts)
"""

from .models import AlertSeverity, AlertEvent
from .rules import AlertRule, RuleType
from .engine import AlertEngine

__all__ = [
    "AlertSeverity",
    "AlertEvent",
    "AlertRule",
    "RuleType",
    "AlertEngine",
]
