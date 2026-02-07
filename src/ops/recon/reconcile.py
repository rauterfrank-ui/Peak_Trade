from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from .models import (
    BalanceSnapshot,
    PositionSnapshot,
    DriftReport,
)


@dataclass(frozen=True)
class ReconTolerances:
    balance_abs: float = 0.0
    position_abs: float = 0.0


def reconcile(
    expected_balances: BalanceSnapshot,
    observed_balances: BalanceSnapshot,
    expected_positions: Optional[PositionSnapshot] = None,
    observed_positions: Optional[PositionSnapshot] = None,
    tolerances: Optional[ReconTolerances] = None,
) -> DriftReport:
    tol = tolerances or ReconTolerances()
    drifts = []

    # balances
    assets = set(expected_balances.balances.keys()) | set(observed_balances.balances.keys())
    for a in sorted(assets):
        e = float(expected_balances.balances.get(a, 0.0))
        o = float(observed_balances.balances.get(a, 0.0))
        if abs(e - o) > tol.balance_abs:
            drifts.append(
                f"balance[{a}] expected={e} observed={o} abs_diff={abs(e - o)} tol={tol.balance_abs}"
            )

    # positions (optional)
    if expected_positions is not None and observed_positions is not None:
        syms = set(expected_positions.positions.keys()) | set(observed_positions.positions.keys())
        for s in sorted(syms):
            e = float(expected_positions.positions.get(s, 0.0))
            o = float(observed_positions.positions.get(s, 0.0))
            if abs(e - o) > tol.position_abs:
                drifts.append(
                    f"position[{s}] expected={e} observed={o} abs_diff={abs(e - o)} tol={tol.position_abs}"
                )

    return DriftReport(ok=(len(drifts) == 0), drifts=drifts)
