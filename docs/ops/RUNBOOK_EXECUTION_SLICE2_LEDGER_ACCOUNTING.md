# RUNBOOK: ExecutionPipeline – Slice 2 (Ledger/Accounting + Deterministic PnL)

## Ziel
Slice 2 erweitert die Slice‑1 Execution Events (insb. FILL) um einen **buchhalterisch prüfbaren** Accounting‑Layer:

- **Double‑Entry Journal Entries** + **Account Balances** (Single Quote Currency)
- **Positions** (qty, avg_cost / WAC) deterministisch
- **PnL**: realized (nur bei Reduktion/Close), unrealized (Mark‑to‑Market), Equity (cash + position_value)
- **Determinismus**: gleiche Input‑Events + gleiche Prices → **bit‑identische** Snapshots/Exports

## Scope Lock (Slice 2)
- **Keine** Live‑Execution Freischaltung (Governance bleibt unverändert).
- **Keine** Multi‑Currency FX/Conversions (Single Quote Currency pro Engine).
- **Keine** Corporate Actions (Splits/Dividends).
- Shorts werden nur als **signierte Position** unterstützt (ohne Borrow/Margin‑Accounting).

## Implementierung (Code-Orte)
- **Ledger Package**: `src/execution/ledger/`
  - `engine.py`: `LedgerEngine.apply(event)` + `open_cash()` + `snapshot()&#47;export_snapshot_json()`
  - `models.py`: `JournalEntry`, `Posting`, `Position`, `ValuationSnapshot`, `QuantizationPolicy`
  - `quantization.py`: deterministisches `Decimal` Parsing + Quantize + Symbol Parser
  - `pnl.py`: unrealized PnL (Mark‑to‑Market)

## Input-Events (Slice 1 → Slice 2)
Slice‑2 konsumiert **BETA_EXEC_V1** Events aus dem Slice‑1 Orchestrator (`src/execution/orchestrator.py`).

Wichtig:
- `ts_utc` ist **nicht deterministisch** und wird in Slice‑2 bewusst ignoriert.
- Für korrektes Accounting muss ein `FILL`‑Event im `payload` enthalten:
  - `side` (BUY/SELL)
  - `quantity`, `price`, `fee`, `fee_currency`

## Accounting Modell (Single Quote Currency)
Konten-Konventionen (alle Beträge in Quote Currency):
- `CASH:<QUOTE>`
- `INVENTORY_COST:<SYMBOL>:<QUOTE>` (signiert; Shorts sind negative Inventory‑Balance)
- `FEES_EXPENSE:<QUOTE>`
- `REALIZED_PNL:<QUOTE>` (Income via Credit/negative Posting)
- `EQUITY_OPENING:<QUOTE>` (nur für `open_cash()` Opening Entry)

Posting‑Konvention:
- **amount > 0** = Debit
- **amount < 0** = Credit

## Invariants (müssen immer gelten)
- **Double‑Entry**: Für jedes `JournalEntry` gilt `sum(postings.amount) == 0`.
- **Cash korrekt**:
  - BUY: cash_delta = \(-(notional + fee)\)
  - SELL: cash_delta = \(+(notional - fee)\)
- **Realized PnL**: nur bei Close/Reduktion; niemals bei reinem Aufstocken.
- **Unrealized PnL**: nur Mark‑to‑Market (nicht gebucht), via `(mark - avg_cost) * qty`.
- **Determinismus**:
  - Keine Floats (nur `Decimal`/Strings)
  - Quantisierung über `QuantizationPolicy` (Default: 8 Dezimalstellen)
  - Stabile Sortierung/Serialisierung (JSON mit `sort_keys=True`)

## Verify / Tests (lokal)
Targeted:

```bash
python3 -m pytest -q tests/execution/ledger
```

Zusätzlich (Slice‑1 Determinismus‑Contract):

```bash
python3 -m pytest -q tests/execution/test_execution_determinism_contract.py
```

## Minimal Usage (Programmatic)

```python
from decimal import Decimal
from src.execution.ledger import LedgerEngine

eng = LedgerEngine(quote_currency="EUR")
eng.open_cash(amount=Decimal("100000"))

# Apply BETA_EXEC_V1 events (z.B. aus execution_events.jsonl) oder Fill-Objekte.
# Snapshot mit Mark-Prices:
snap_json = eng.export_snapshot_json(
    ts_sim=123,
    mark_prices={"BTC/EUR": Decimal("51000.00000000")},
)
print(snap_json)
```
