# src/live/__init__.py
"""
Live-Adapter-Skeleton fuer Peak_Trade.

Dieses Paket stellt:
- Standard-Datenstrukturen fuer Orders
- Basis-Broker-Interface
- einen DryRunBroker (kein echter Handel)
- Safety-Layer (Phase 17)
bereit.

Phase 17: KEINE echten Orders werden implementiert!
          Der Safety-Layer bereitet die Architektur vor.

HINWEIS: Safety-Module werden lazy importiert, um zirkuläre
         Abhängigkeiten zu vermeiden. Direkter Import:
         >>> from src.live.safety import SafetyGuard
"""

from .orders import (
    LiveOrderRequest,
    LiveExecutionReport,
    save_orders_to_csv,
    load_orders_csv,
    side_from_direction,
)
from .broker_base import BaseBrokerClient, DryRunBroker, PaperBroker
from .risk_limits import LiveRiskLimits, LiveRiskConfig, LiveRiskCheckResult
from .portfolio_monitor import (
    LivePositionSnapshot,
    LivePortfolioSnapshot,
    LivePortfolioMonitor,
)
from .alerts import (
    AlertLevel,
    AlertEvent,
    AlertSink,
    LoggingAlertSink,
    StderrAlertSink,
    WebhookAlertSink,
    SlackWebhookAlertSink,
    MultiAlertSink,
    LiveAlertsConfig,
    build_alert_sink_from_config,
)

# Phase 82: Alert-Pipeline
from .alert_pipeline import (
    AlertSeverity,
    AlertCategory,
    AlertMessage,
    SlackChannelConfig,
    SlackAlertChannel,
    EmailChannelConfig,
    EmailAlertChannel,
    NullAlertChannel,
    AlertPipelineManager,
    SeverityTransitionTracker,
    build_alert_pipeline_from_config,
)

# Phase 83: Alert-Storage
from .alert_storage import (
    StoredAlert,
    AlertStorage,
    get_default_alert_storage,
    reset_default_storage,
    store_alert,
    list_recent_alerts,
    get_alert_stats,
)

# Safety- und Shadow-Session-Module werden lazy importiert, um zirkuläre
# Abhängigkeiten zu vermeiden. Direkter Import:
#   >>> from src.live.safety import SafetyGuard
#   >>> from src.live.shadow_session import ShadowPaperSession


__all__ = [
    # Orders
    "LiveOrderRequest",
    "LiveExecutionReport",
    "save_orders_to_csv",
    "load_orders_csv",
    "side_from_direction",
    # Broker
    "BaseBrokerClient",
    "DryRunBroker",
    "PaperBroker",
    # Risk Limits
    "LiveRiskLimits",
    "LiveRiskConfig",
    "LiveRiskCheckResult",
    # Portfolio Monitoring (Phase 48)
    "LivePositionSnapshot",
    "LivePortfolioSnapshot",
    "LivePortfolioMonitor",
    # Alerts & Notifications (Phase 49 + 50)
    "AlertLevel",
    "AlertEvent",
    "AlertSink",
    "LoggingAlertSink",
    "StderrAlertSink",
    "WebhookAlertSink",
    "SlackWebhookAlertSink",
    "MultiAlertSink",
    "LiveAlertsConfig",
    "build_alert_sink_from_config",
    # Phase 82: Alert-Pipeline (Slack/Mail)
    "AlertSeverity",
    "AlertCategory",
    "AlertMessage",
    "SlackChannelConfig",
    "SlackAlertChannel",
    "EmailChannelConfig",
    "EmailAlertChannel",
    "NullAlertChannel",
    "AlertPipelineManager",
    "SeverityTransitionTracker",
    "build_alert_pipeline_from_config",
    # Phase 83: Alert-Storage
    "StoredAlert",
    "AlertStorage",
    "get_default_alert_storage",
    "reset_default_storage",
    "store_alert",
    "list_recent_alerts",
    "get_alert_stats",
    # Safety (Phase 17) - lazy loaded
    "SafetyGuard",
    "SafetyAuditEntry",
    "SafetyBlockedError",
    "LiveTradingDisabledError",
    "ConfirmTokenInvalidError",
    "LiveNotImplementedError",
    "TestnetDryRunOnlyError",
    "PaperModeOrderError",
    "create_safety_guard",
    # Phase 31: Shadow/Paper Session - lazy loaded
    "ShadowPaperSession",
    "ShadowPaperSessionMetrics",
    "EnvironmentNotAllowedError",
    "create_shadow_paper_session",
    # Phase 33: Monitoring - lazy loaded
    "LiveMonitoringConfig",
    "LiveRunSnapshot",
    "LiveRunTailRow",
    "load_live_monitoring_config",
    "load_run_snapshot",
    "load_run_tail",
    "get_latest_run_dir",
    # Phase 34: Alerts - lazy loaded
    "AlertsConfig",
    "AlertRule",
    "AlertEvent",
    "AlertEngine",
    "Severity",
    "create_alert_engine_from_config",
    "append_alerts_to_file",
    "load_alerts_from_file",
    "render_alerts",
]


def __getattr__(name: str):
    """Lazy-Loading für Safety-, Shadow-Session-, Monitoring- und Alerts-Module."""
    _safety_exports = {
        "SafetyGuard",
        "SafetyAuditEntry",
        "SafetyBlockedError",
        "LiveTradingDisabledError",
        "ConfirmTokenInvalidError",
        "LiveNotImplementedError",
        "TestnetDryRunOnlyError",
        "PaperModeOrderError",
        "create_safety_guard",
    }
    _shadow_session_exports = {
        "ShadowPaperSession",
        "ShadowPaperSessionMetrics",
        "EnvironmentNotAllowedError",
        "create_shadow_paper_session",
    }
    _monitoring_exports = {
        "LiveMonitoringConfig",
        "LiveRunSnapshot",
        "LiveRunTailRow",
        "load_live_monitoring_config",
        "load_run_snapshot",
        "load_run_tail",
        "get_latest_run_dir",
    }
    _alerts_exports = {
        "AlertsConfig",
        "AlertRule",
        "AlertEvent",
        "AlertEngine",
        "Severity",
        "create_alert_engine_from_config",
        "append_alerts_to_file",
        "load_alerts_from_file",
        "render_alerts",
    }
    if name in _safety_exports:
        from . import safety

        return getattr(safety, name)
    if name in _shadow_session_exports:
        from . import shadow_session

        return getattr(shadow_session, name)
    if name in _monitoring_exports:
        from . import monitoring

        return getattr(monitoring, name)
    if name in _alerts_exports:
        from . import alerts

        return getattr(alerts, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
