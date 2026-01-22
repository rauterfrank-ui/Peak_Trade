# RUNBOOK: ExecutionPipeline – Slice 2 „Ledger/Accounting + Deterministic PnL“

## Purpose
Slice 2 macht Slice‑1 Execution Events buchhalterisch prüfbar:

- Double‑Entry **Journal Entries** + **Account Balances**
- Deterministische **Positions** (qty, avg_cost / WAC)
- Deterministische **PnL** (realized/unrealized) + **Equity**
- **Replays**: gleiche Input‑Events + gleiche Preise → bit‑identische Exports

## Scope (Scope Lock)
- NO‑LIVE: Keine Live‑Orders, keine Governance‑Unlocks.
- Single Quote Currency (keine FX / Multi‑Currency).
- Keine Corporate Actions (Splits/Dividends).
- Shorts nur als signierte Position (ohne Borrow/Margin‑Accounting).

## Preconditions
- Slice 1: deterministische `BETA_EXEC_V1` Event‑Streams (mindestens `FILL`, `fee`).
- Money math: ausschließlich `Decimal`/Strings (keine Floats).

## Implementation (Repo Paths)
- Code:
  - `src/execution/ledger/engine.py` – `LedgerEngine.apply(event)` + `snapshot()/export_snapshot_json()`
  - `src/execution/ledger/models.py` – `JournalEntry`, `Posting`, `Position`, `ValuationSnapshot`, `QuantizationPolicy`
  - `src/execution/ledger/quantization.py` – deterministisches Decimal Parsing + Quantize
  - `src/execution/ledger/pnl.py` – unrealized PnL (MTM)
  - `src/execution/ledger/valuation.py` – Mark‑to‑Market Wrapper
  - `src/execution/ledger/export.py` – stabile JSON Exports
  - `src/execution/ledger/execution_to_ledger.py` – dünner Slice‑1→Slice‑2 Adapter (`ts_utc` drop)
- Tests:
  - `tests/execution/test_ledger_double_entry.py`
  - `tests/execution/test_ledger_pnl_golden.py`
  - `tests/execution/test_execution_slice1_to_ledger_integration.py`

## Determinism Contract (Hard Requirements)
- Keine `datetime.now()` in der Ledger‑Core Logik.
- `ts_sim` ist Ordering Key (Input), `ts_utc` wird ignoriert.
- Stabile Sortierung:
  - Events upstream sortieren: `(run_id, session_id, ts_sim, event_type, event_id)`
  - Postings stable order by `(account, amount)`
  - Positions stable order by `symbol`
- Quantisierung:
  - Default: 8 Dezimalstellen (konfigurierbar via `QuantizationPolicy`)
  - Quantize nach kritischen Arithmetik‑Schritten
- Export:
  - JSON `sort_keys=True`, stabile Separators, deterministische List Ordering

## Accounting Invariants
- Double‑Entry: `sum(postings.amount) == 0` pro `JournalEntry` (Quote Currency).
- Cash:
  - BUY: cash_delta = \(-(notional + fee)\)
  - SELL: cash_delta = \(+(notional - fee)\)
- Realized PnL:
  - Nur beim Close/Reduktion
  - Fees werden separat als Expense geführt (nicht in avg_cost eingerechnet)
- Unrealized PnL:
  - Nur Mark‑to‑Market: `(mark_price - avg_cost) * qty`

## Verify Commands (Snapshot-only)

```bash
python3 -m pytest -q tests/execution/test_ledger_double_entry.py
python3 -m pytest -q tests/execution/test_ledger_pnl_golden.py
python3 -m pytest -q tests/execution/test_execution_slice1_to_ledger_integration.py
python3 -m pytest -q tests/execution/test_execution_determinism_contract.py
```

## Minimal Demo (Programmatic)

```python
from decimal import Decimal
from src.execution.ledger import LedgerEngine

eng = LedgerEngine(quote_currency="EUR")
eng.open_cash(amount=Decimal("10000"))

# Apply events / fills, then:
print(eng.export_snapshot_json(ts_sim=123, mark_prices={"BTC/EUR": Decimal("51000")}))
```

## Exit Criteria (DoD)
- Unit + Golden + Integration Tests grün.
- Exports sind stabil (bit‑identisch) für identische Inputs.
- Keine Änderungen, die NO‑LIVE/Governance Locks lockern.
