# src/execution/__init__.py
"""
Execution-Pipeline fuer Peak_Trade.

Dieses Modul stellt eine einheitliche Schnittstelle bereit, um
Strategie-Signale in OrderRequests zu uebersetzen und diese ueber
einen OrderExecutor (z. B. PaperOrderExecutor) auszufuehren.

Hauptkomponenten:
- ExecutionPipeline: Zentrale Pipeline-Klasse fuer Order-Ausfuehrung
- ExecutionPipelineConfig: Konfiguration fuer die Pipeline
- OrderIntent: Order-Absicht fuer submit_order() (Phase 16A V2)
- ExecutionStatus: Detaillierter Execution-Status (Phase 16A V2)
- LiveSessionRunner: Strategy-to-Execution Bridge (Phase 80)
- LiveSessionConfig: Konfiguration fuer LiveSessionRunner

Die Pipeline kann verwendet werden in:
- Backtests (Paper-Simulation)
- Paper-Trading
- Shadow/Testnet-Sessions (Phase 80)
- Forward-/Live-Simulationen (zukuenftig)

Phase 16A V2 (Governance-aware):
- Governance-Integration via get_governance_status("live_order_execution")
- live_order_execution ist gesperrt (status="locked")
- Bei env="live" wird GovernanceViolationError/LiveExecutionLockedError geworfen

WICHTIG: Es werden KEINE echten Live-Orders an Boersen gesendet!
         live_order_execution ist governance-seitig gesperrt.
"""

from __future__ import annotations

from .pipeline import (
    ExecutionPipeline,
    ExecutionPipelineConfig,
    SignalEvent,
    ExecutionResult,
    # Phase 16A V2: Neue Komponenten
    OrderIntent,
    ExecutionStatus,
    ExecutionEnvironment,
    # Phase 16A V2: Exceptions
    ExecutionPipelineError,
    GovernanceViolationError,
    LiveExecutionLockedError,
    RiskCheckFailedError,
)

from .live_session import (
    LiveSessionRunner,
    LiveSessionConfig,
    LiveSessionMetrics,
    SessionMode,
    LiveModeNotAllowedError,
    SessionSetupError,
    SessionRuntimeError,
)

__all__ = [
    # Pipeline
    "ExecutionPipeline",
    "ExecutionPipelineConfig",
    "SignalEvent",
    "ExecutionResult",
    # Phase 16A V2: Neue Komponenten
    "OrderIntent",
    "ExecutionStatus",
    "ExecutionEnvironment",
    # Phase 16A V2: Exceptions
    "ExecutionPipelineError",
    "GovernanceViolationError",
    "LiveExecutionLockedError",
    "RiskCheckFailedError",
    # Phase 80: Live Session
    "LiveSessionRunner",
    "LiveSessionConfig",
    "LiveSessionMetrics",
    "SessionMode",
    "LiveModeNotAllowedError",
    "SessionSetupError",
    "SessionRuntimeError",
]
