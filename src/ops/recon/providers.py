"""
Runbook-B reconciliation snapshot providers (pluggable).
Implementations may be in-memory, local state, or exchange adapters;
tests must use offline implementations only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Protocol

from src.ops.recon.models import BalanceSnapshot, PositionSnapshot


class ReconProvider(Protocol):
    """
    Provides expected/observed snapshots for reconciliation.
    Implementations may read from in-memory ledgers, local state, or exchange adapters
    (but tests must use offline implementations).
    """

    def expected_balances(self) -> BalanceSnapshot: ...
    def observed_balances(self) -> BalanceSnapshot: ...
    def expected_positions(self) -> Optional[PositionSnapshot]: ...
    def observed_positions(self) -> Optional[PositionSnapshot]: ...


@dataclass(frozen=True)
class NullReconProvider:
    """Returns identical empty snapshots; no drift when used alone."""

    epoch: int = 0
    balances: Optional[Dict[str, float]] = None

    def expected_balances(self) -> BalanceSnapshot:
        return BalanceSnapshot(epoch=self.epoch, balances=dict(self.balances or {}))

    def observed_balances(self) -> BalanceSnapshot:
        return BalanceSnapshot(epoch=self.epoch, balances=dict(self.balances or {}))

    def expected_positions(self) -> Optional[PositionSnapshot]:
        return None

    def observed_positions(self) -> Optional[PositionSnapshot]:
        return None
