from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class LedgerRow:
    step: int
    cash: float
    positions: Dict[str, float]


def snapshot(step: int, cash: float, positions: Dict[str, float]) -> LedgerRow:
    return LedgerRow(
        step=step,
        cash=float(cash),
        positions={k: float(v) for k, v in sorted(positions.items())},
    )


def verify_non_negative_positions(row: LedgerRow) -> None:
    for sym, q in row.positions.items():
        if q < -1e-12:
            raise RuntimeError(f"NEGATIVE_POSITION:{sym}")


def verify_cash_is_finite(row: LedgerRow) -> None:
    if row.cash != row.cash:
        raise RuntimeError("CASH_NAN")


def verify_invariants(ledger: List[LedgerRow]) -> Tuple[float, Dict[str, float]]:
    if not ledger:
        raise RuntimeError("EMPTY_LEDGER")
    for row in ledger:
        verify_cash_is_finite(row)
        verify_non_negative_positions(row)
    last = ledger[-1]
    return last.cash, dict(last.positions)
