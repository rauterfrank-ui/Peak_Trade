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

from .engine import LedgerEngine
from .execution_to_ledger import iter_beta_exec_v1_events
from .export import (
    dumps_canonical_json,
    export_events_jsonl,
    export_ledger_jsonl,
    export_snapshot,
)
from .models import (
    # EXEC_SLICE2 FIFO models
    DecimalPolicy,
    FillEvent,
    MarkEvent,
    LedgerEvent,
    PositionLot,
    PositionState,
    AccountState,
    LedgerEntry,
    LedgerSnapshot,
)

__all__ = [
    "LedgerEngine",
    "iter_beta_exec_v1_events",
    "export_snapshot",
    "export_events_jsonl",
    "export_ledger_jsonl",
    "dumps_canonical_json",
    # FIFO Slice2 models
    "DecimalPolicy",
    "FillEvent",
    "MarkEvent",
    "LedgerEvent",
    "PositionLot",
    "PositionState",
    "AccountState",
    "LedgerEntry",
    "LedgerSnapshot",
]
