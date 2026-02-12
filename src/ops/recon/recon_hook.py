"""
Runbook-B reconciliation hook: compare expected vs observed snapshots (pure).
Default OFF via PEAK_RECON_ENABLED=1.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from src.ops.recon.models import BalanceSnapshot, PositionSnapshot, DriftReport
from src.ops.recon.providers import ReconProvider, NullReconProvider
from src.ops.recon.reconcile import ReconTolerances, reconcile


@dataclass(frozen=True)
class ReconConfig:
    enabled: bool = False
    balance_abs: float = 0.0
    position_abs: float = 0.0


def config_from_env() -> ReconConfig:
    enabled = os.getenv("PEAK_RECON_ENABLED", "0") == "1"
    bal = float(os.getenv("PEAK_RECON_BALANCE_ABS", "0") or 0.0)
    pos = float(os.getenv("PEAK_RECON_POSITION_ABS", "0") or 0.0)
    return ReconConfig(enabled=enabled, balance_abs=bal, position_abs=pos)


def run_recon_if_enabled(
    cfg: ReconConfig,
    *,
    provider: Optional[ReconProvider] = None,
    expected_balances: Optional[BalanceSnapshot] = None,
    observed_balances: Optional[BalanceSnapshot] = None,
    expected_positions: Optional[PositionSnapshot] = None,
    observed_positions: Optional[PositionSnapshot] = None,
) -> DriftReport:
    if not cfg.enabled:
        return DriftReport(ok=True, drifts=[])

    if provider is None:
        provider = NullReconProvider()

    if expected_balances is None:
        expected_balances = provider.expected_balances()
    if observed_balances is None:
        observed_balances = provider.observed_balances()
    if expected_positions is None:
        expected_positions = provider.expected_positions()
    if observed_positions is None:
        observed_positions = provider.observed_positions()

    tol = ReconTolerances(balance_abs=cfg.balance_abs, position_abs=cfg.position_abs)
    return reconcile(
        expected_balances=expected_balances,
        observed_balances=observed_balances,
        expected_positions=expected_positions,
        observed_positions=observed_positions,
        tolerances=tol,
    )
