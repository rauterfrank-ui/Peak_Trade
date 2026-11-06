# P33 — Backtest Report Artifacts v1 (JSON schema)

## Goal
Persist `BacktestReportV1` (P32) as a deterministic, versioned JSON structure (schema v1).

## Schema v1
Top-level keys:
- `schema_version` (int) — must be `1`
- `fills` (list of objects)
- `state` (object)
- `equity` (list of numbers)
- `metrics` (object mapping string to number)

### fills[*]
- `order_id` (str)
- `side` (str)
- `qty` (number)
- `price` (number)
- `fee` (number)
- `symbol` (str)

### state
- `cash` (number)
- `positions_qty` (object mapping symbol to number)
- `avg_cost` (object mapping symbol to number)
- `realized_pnl` (number)

## Determinism
- `report_to_dict()` produces JSON-serializable types only.
- Deterministic text output: `json.dumps(d, sort_keys=True)`.

## API
- `report_to_dict(report)` → schema v1 dict
- `report_from_dict(d)` → `BacktestReportV1DTO` (DTO only; domain rehydration is out of scope)

## Non-goals
- Plotting
- File IO embedded in conversion
