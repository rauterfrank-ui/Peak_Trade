# P40 — Backtest Runner CLI v1

## Goal
Deterministic CLI entrypoint to run the P32 backtest report composition (P24–P31 via P32) and emit validated artifacts:
- `report.json` (schema v1, via P34/P33)
- optional bundle directory (P35)
- optional tarball bundle (P36)

## Input formats (v1)

### bars.json
A JSON array of OHLCV bars:
```json
[
  {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 10.0},
  {"open": 100.5, "high": 102.0, "low": 100.0, "close": 101.0, "volume": 12.0}
]
```
Keys: `open`, `high`, `low`, `close`, `volume` (optional, default 0).

### orders.json
A JSON array of arrays. `orders_by_bar[i]` = orders for bar `i`:
```json
[
  [],
  [{"id": "o1", "symbol": "MOCK", "side": "BUY", "order_type": "MARKET", "qty": 1.0}]
]
```
Order keys: `id`, `symbol`, `side`, `order_type`, `qty`; optional: `limit_price`, `stop_price`.
`order_type`: `MARKET`, `LIMIT`, or `STOP_MARKET`. Length must equal `len(bars)`.

## CLI
```bash
python -m src.ops.p40.backtest_runner_cli_v1 run \
  --bars-json path/to/bars.json \
  --orders-json path/to/orders.json \
  --out-dir /tmp/out \
  [--bundle-dir] [--tarball /tmp/out.tgz] [--verify]
```

## Output
- `report.json` in `--out-dir` (always)
- If `--bundle-dir`: full P35 bundle (report.json + metrics_summary.json + manifest.json)
- If `--tarball`: P36 tarball at given path
- If `--verify`: run P35/P36 verification after write
