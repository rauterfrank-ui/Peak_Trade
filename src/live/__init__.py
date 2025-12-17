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

# Phase 82: Alert-Pipeline
from .alert_pipeline import (
    AlertCategory,
    AlertMessage,
    AlertPipelineManager,
    AlertSeverity,
    EmailAlertChannel,
    EmailChannelConfig,
    NullAlertChannel,
    SeverityTransitionTracker,
    SlackAlertChannel,
    SlackChannelConfig,
    build_alert_pipeline_from_config,
)

# Phase 83: Alert-Storage
from .alert_storage import (
    AlertStorage,
    StoredAlert,
    get_alert_stats,
    get_default_alert_storage,
    list_recent_alerts,
    reset_default_storage,
    store_alert,
)
from .alerts import (
    AlertEvent,
    AlertLevel,
    AlertSink,
    LiveAlertsConfig,
    LoggingAlertSink,
    MultiAlertSink,
    SlackWebhookAlertSink,
    StderrAlertSink,
    WebhookAlertSink,
    build_alert_sink_from_config,
)
from .broker_base import BaseBrokerClient, DryRunBroker, PaperBroker
from .orders import (
    LiveExecutionReport,
    LiveOrderRequest,
    load_orders_csv,
    save_orders_to_csv,
    side_from_direction,
)
from .portfolio_monitor import (
    LivePortfolioMonitor,
    LivePortfolioSnapshot,
    LivePositionSnapshot,
)
from .risk_limits import LiveRiskCheckResult, LiveRiskConfig, LiveRiskLimits

# Safety- und Shadow-Session-Module werden lazy importiert, um zirkuläre
# Abhängigkeiten zu vermeiden. Direkter Import:
#   >>> from src.live.safety import SafetyGuard
#   >>> from src.live.shadow_session import ShadowPaperSession


__all__ = [
    "AlertCategory",
    "AlertEngine",
    "AlertEvent",
    "AlertEvent",
    # Alerts & Notifications (Phase 49 + 50)
    "AlertLevel",
    "AlertMessage",
    "AlertPipelineManager",
    "AlertRule",
    # Phase 82: Alert-Pipeline (Slack/Mail)
    "AlertSeverity",
    "AlertSink",
    "AlertStorage",
    # Phase 34: Alerts - lazy loaded
    "AlertsConfig",
    # Broker
    "BaseBrokerClient",
    "ConfirmTokenInvalidError",
    "DryRunBroker",
    "EmailAlertChannel",
    "EmailChannelConfig",
    "EnvironmentNotAllowedError",
    "LiveAlertsConfig",
    "LiveExecutionReport",
    # Phase 33: Monitoring - lazy loaded
    "LiveMonitoringConfig",
    "LiveNotImplementedError",
    # Orders
    "LiveOrderRequest",
    "LivePortfolioMonitor",
    "LivePortfolioSnapshot",
    # Portfolio Monitoring (Phase 48)
    "LivePositionSnapshot",
    "LiveRiskCheckResult",
    "LiveRiskConfig",
    # Risk Limits
    "LiveRiskLimits",
    "LiveRunSnapshot",
    "LiveRunTailRow",
    "LiveTradingDisabledError",
    "LoggingAlertSink",
    "MultiAlertSink",
    "NullAlertChannel",
    "PaperBroker",
    "PaperModeOrderError",
    "SafetyAuditEntry",
    "SafetyBlockedError",
    # Safety (Phase 17) - lazy loaded
    "SafetyGuard",
    "Severity",
    "SeverityTransitionTracker",
    # Phase 31: Shadow/Paper Session - lazy loaded
    "ShadowPaperSession",
    "ShadowPaperSessionMetrics",
    "SlackAlertChannel",
    "SlackChannelConfig",
    "SlackWebhookAlertSink",
    "StderrAlertSink",
    # Phase 83: Alert-Storage
    "StoredAlert",
    "TestnetDryRunOnlyError",
    "WebhookAlertSink",
    "append_alerts_to_file",
    "build_alert_pipeline_from_config",
    "build_alert_sink_from_config",
    "create_alert_engine_from_config",
    "create_safety_guard",
    "create_shadow_paper_session",
    "get_alert_stats",
    "get_default_alert_storage",
    "get_latest_run_dir",
    "list_recent_alerts",
    "load_alerts_from_file",
    "load_live_monitoring_config",
    "load_orders_csv",
    "load_run_snapshot",
    "load_run_tail",
    "render_alerts",
    "reset_default_storage",
    "save_orders_to_csv",
    "side_from_direction",
    "store_alert",
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
