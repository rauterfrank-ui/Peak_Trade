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
from .engine_legacy import LegacyLedgerEngine, LegacyLedgerState
from .execution_to_ledger import iter_beta_exec_v1_events
from .export import (
    dumps_canonical_json,
    export_events_jsonl,
    export_ledger_jsonl,
    export_snapshot,
    export_valuation_snapshot_json,
)
from .fifo_engine import FifoLedgerEngine
from .valuation import snapshot_mark_to_market
from .models import (
    # Legacy models (kept for replay-pack + Slice-1 integration tests)
    JournalEntry,
    Posting,
    Position,
    QuantizationPolicy,
    ValuationSnapshot,
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
    "LegacyLedgerEngine",
    "LegacyLedgerState",
    "FifoLedgerEngine",
    "iter_beta_exec_v1_events",
    "snapshot_mark_to_market",
    "export_snapshot",
    "export_valuation_snapshot_json",
    "export_events_jsonl",
    "export_ledger_jsonl",
    "dumps_canonical_json",
    # Legacy models
    "JournalEntry",
    "Posting",
    "Position",
    "QuantizationPolicy",
    "ValuationSnapshot",
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
