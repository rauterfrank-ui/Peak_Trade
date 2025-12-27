"""
Risk-Layer Production Alerting
================================

Foundation for production alerting infrastructure.

Phase 1 Components:
- AlertSeverity, AlertCategory: Core enums
- AlertEvent: Immutable event dataclass
- AlertConfig: TOML-based configuration with env var substitution
- AlertManager: Central coordinator for alert lifecycle
- AlertDispatcher: Routes to channels (Phase 1: in-memory sink)

Usage:
    from src.risk_layer.alerting import (
        AlertManager,
        AlertSeverity,
        AlertCategory,
        load_alert_config,
    )

    config = load_alert_config()
    manager = AlertManager(config)

    manager.register_alert(
        severity=AlertSeverity.ERROR,
        category=AlertCategory.RISK_LIMIT,
        source="var_gate",
        message="VaR limit breached",
        context={"current_var": 0.05, "limit": 0.03},
    )
"""

from src.risk_layer.alerting.alert_config import AlertConfig, load_alert_config
from src.risk_layer.alerting.alert_dispatcher import AlertDispatcher
from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_manager import AlertManager
from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity

__all__ = [
    "AlertSeverity",
    "AlertCategory",
    "AlertEvent",
    "AlertConfig",
    "load_alert_config",
    "AlertManager",
    "AlertDispatcher",
]
