# EXEC_SLICE2 — Deterministic Ledger/Accounting (FIFO Lots)

## Ziel
Slice2 fügt eine **deterministische Ledger/Accounting-Schicht** hinzu, die aus einem festen Event-Stream (Fills/Marks) reproduzierbar:
- Cash-/Fee-Bewegungen
- Positionen via **FIFO-Lots** (Long & Short)
- Realized/Unrealized PnL (Unrealized nur im Snapshot)
ableitet.

**NO-LIVE HARD**: Diese Ledger-Schicht ist *watch-only/offline*. Keine Broker-/Exchange-Write-Aktionen.

## Contracts

### Event-Typen (minimal)
Definiert in `src/execution/ledger/models.py`:
- **`FillEvent`**
  - `ts_utc`: ISO8601 UTC mit `Z` (z.B. `2026-01-01T00:00:00Z`)
  - `seq`: `int` (deterministische Total-Order)
  - `instrument`: `str` (z.B. `ABC&#47;USD`)
  - `side`: `"BUY"` / `"SELL"`
  - `qty`, `price`, `fee`: `Decimal`
  - `fee_ccy`: `str` (Default `"USD"`)
- **`MarkEvent`**
  - `ts_utc`, `seq`, `instrument`, `price` (`Decimal`)

### Deterministische Ordnung
Upstream muss Events deterministisch sortieren: **primär `(ts_utc, seq)`**.
`LedgerEngine` erzwingt **Monotonie** und wirft bei Non-Monotonicity einen Fehler.

### Decimal / Rounding Policy
- **Alle** qty/price/money Berechnungen sind `Decimal`.
- Floats sind verboten (Fail-Fast).
- Eine zentrale Policy `DecimalPolicy` quantisiert:
  - Qty/Price/Money auf `1e-8`
  - `ROUND_HALF_UP`

## Engine-Semantik
Implementierung: `src/execution/ledger/engine.py`
- BUY: eröffnet/erhöht Long (oder schließt Shorts FIFO)
- SELL: eröffnet/erhöht Short (oder schließt Longs FIFO)
- Realized PnL wird **nur beim Schließen** (Matching) gebucht.
- Unrealized PnL wird **nur im Snapshot** berechnet, basierend auf `last_mark_price`.

## Canonical JSON Export
Implementierung: `src/execution/ledger/export.py`
- `sort_keys=True`, `separators=(",", ":")`
- `Decimal` wird als **String** serialisiert
- Stable Ordering:
  - Positions nach `instrument`
  - Lots nach `(ts_utc, seq)`

Wichtige Funktionen:
- `to_canonical_dict(snapshot) -> dict`
- `dumps_canonical_json(snapshot) -> bytes`
- `export_snapshot(path, snapshot)` schreibt `snapshot.json`
- `export_events_jsonl(path, events)` schreibt Event-Stream als `events.jsonl`
- `export_ledger_jsonl(path, entries)` schreibt LedgerEntries als `ledger.jsonl`

## Tests ausführen

```bash
uv run pytest -q tests/execution/test_ledger_*.py
```

## Mini-Beispiel (Snapshot, gekürzt)

```json
{
  "ts_utc_last":"2026-01-01T00:00:05Z",
  "seq_last":6,
  "account":{
    "cash_by_ccy":{"USD":"..."},
    "fees_by_ccy":{"USD":"..."},
    "realized_pnl_by_ccy":{"USD":"..."},
    "positions":[{"instrument":"ABC/USD","qty_signed":"...","lots":[...]}]
  }
}
```

## Slice3+ TODOs (bewusst nicht Teil von Slice2)
- Multi-Currency FX Conversion / Cross-Currency Cashflows
- Corporate Actions (Splits/Dividenden)
- Margin/Borrow/Finanzierungs-Kosten
