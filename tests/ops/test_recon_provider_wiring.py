"""
Unit tests for reconciliation provider wiring (offline, deterministic).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.ops.recon.models import BalanceSnapshot, PositionSnapshot
from src.ops.recon.recon_hook import ReconConfig, run_recon_if_enabled


@dataclass(frozen=True)
class FakeProvider:
    """Minimal provider for tests; implements ReconProvider protocol."""

    eb: BalanceSnapshot
    ob: BalanceSnapshot

    def expected_balances(self) -> BalanceSnapshot:
        return self.eb

    def observed_balances(self) -> BalanceSnapshot:
        return self.ob

    def expected_positions(self) -> Optional[PositionSnapshot]:
        return None

    def observed_positions(self) -> Optional[PositionSnapshot]:
        return None


def test_provider_used_when_snapshots_none():
    cfg = ReconConfig(enabled=True, balance_abs=0.0, position_abs=0.0)
    p = FakeProvider(
        eb=BalanceSnapshot(epoch=1, balances={"USD": 100.0}),
        ob=BalanceSnapshot(epoch=2, balances={"USD": 90.0}),
    )
    rep = run_recon_if_enabled(
        cfg,
        provider=p,
        expected_balances=None,
        observed_balances=None,
    )
    assert rep.ok is False
    assert len(rep.drifts) == 1
