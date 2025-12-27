"""
Telemetry Alerting - Phase 16I + 16J

Real-time alerting and incident hooks with lifecycle management.

Core Components:
- models: AlertSeverity, AlertEvent
- rules: AlertRule, rule evaluation
- engine: AlertEngine (evaluate, dedupe, cooldown, rate limiting, operator state)
- adapters: AlertSink protocol (console, webhook)
- history: AlertHistory (persistent JSONL storage)
- operator_state: OperatorState (ACK/SNOOZE/RESOLVE)

Features:
- Config-driven (default: disabled)
- Dry-run mode (no external calls)
- Dedupe + cooldown logic
- Rate limiting
- Deterministic alert ordering
- Operator actions (ACK, SNOOZE) - Phase 16J
- Alert history with retention - Phase 16J

Phase 16I: Real-time Alerting (Phases 16F+16H → actionable alerts)
Phase 16J: Alert Lifecycle & Noise Control
"""

from .models import AlertSeverity, AlertEvent
from .rules import AlertRule, RuleType
from .engine import AlertEngine
from .history import AlertHistory
from .operator_state import OperatorState, OperatorAction

__all__ = [
    "AlertSeverity",
    "AlertEvent",
    "AlertRule",
    "RuleType",
    "AlertEngine",
    "AlertHistory",
    "OperatorState",
    "OperatorAction",
]
