# src/execution/__init__.py
"""
Execution-Pipeline fuer Peak_Trade.

Dieses Modul stellt eine einheitliche Schnittstelle bereit, um
Strategie-Signale in OrderRequests zu uebersetzen und diese ueber
einen OrderExecutor (z. B. PaperOrderExecutor) auszufuehren.

Hauptkomponenten:
- ExecutionPipeline: Zentrale Pipeline-Klasse fuer Order-Ausfuehrung
- ExecutionPipelineConfig: Konfiguration fuer die Pipeline

Die Pipeline kann verwendet werden in:
- Backtests (Paper-Simulation)
- Paper-Trading
- Forward-/Live-Simulationen (zukuenftig)

WICHTIG: Es werden KEINE echten Orders an Boersen gesendet.
         Alles bleibt auf Paper-/Sandbox-Level.
"""
from __future__ import annotations

from .pipeline import ExecutionPipeline, ExecutionPipelineConfig, SignalEvent

__all__ = ["ExecutionPipeline", "ExecutionPipelineConfig", "SignalEvent"]
