"""
Ledger / Accounting Layer (ExecutionPipeline Slice 2)
=====================================================

This package converts deterministic execution fill events into:
- Double-entry journal entries + account balances (quote currency)
- Deterministic positions (qty, avg_cost/cost_basis)
- Deterministic PnL (realized/unrealized) and equity snapshots

Scope (Slice 2):
- Single quote currency (no FX)
- No corporate actions (splits/dividends)
- No margin/borrow accounting; shorts are supported only as signed positions
"""

from .engine import LedgerEngine, LedgerState
from .execution_to_ledger import iter_beta_exec_v1_events
from .export import export_snapshot
from .valuation import snapshot_mark_to_market
from .models import (
    JournalEntry,
    Posting,
    Position,
    QuantizationPolicy,
    ValuationSnapshot,
)

__all__ = [
    "LedgerEngine",
    "LedgerState",
    "iter_beta_exec_v1_events",
    "JournalEntry",
    "Posting",
    "Position",
    "QuantizationPolicy",
    "ValuationSnapshot",
    "snapshot_mark_to_market",
    "export_snapshot",
]
