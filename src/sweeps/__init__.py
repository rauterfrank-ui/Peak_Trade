# src/sweeps/__init__.py
"""
Peak_Trade – Hyperparameter Sweep Engine (Phase 20)
====================================================

Dieses Modul stellt eine generische Infrastruktur für Hyperparameter-Sweeps bereit.

Kernkomponenten:
- SweepConfig: Konfiguration für einen Sweep-Lauf
- SweepResult: Ergebnis eines einzelnen Sweep-Runs
- SweepEngine: Orchestriert Sweep-Läufe und Registry-Integration

Scope:
- Nur Backtest- und Portfolio-Backtest-Sweeps
- Keine Live- oder Testnet-Orders
- Volle Integration mit Experiments-Registry
"""

from __future__ import annotations

from .engine import (
    SweepConfig,
    SweepResult,
    SweepSummary,
    SweepEngine,
    expand_parameter_grid,
    generate_sweep_id,
)

__all__ = [
    "SweepConfig",
    "SweepResult",
    "SweepSummary",
    "SweepEngine",
    "expand_parameter_grid",
    "generate_sweep_id",
]
