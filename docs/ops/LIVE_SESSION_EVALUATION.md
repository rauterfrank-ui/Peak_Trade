# Live Session Evaluation – Runbook

Offline-Tool zur Evaluation von Live-Trading-Sessions basierend auf `fills.csv`.

## Quick Commands

```bash
# Help
python scripts/evaluate_live_session.py --help

# Evaluate session (text output)
python scripts/evaluate_live_session.py --session-dir /path/to/session

# Generate JSON report
python scripts/evaluate_live_session.py \
  --session-dir /path/to/session \
  --write-report

# JSON output (machine-readable)
python scripts/evaluate_live_session.py \
  --session-dir /path/to/session \
  --format json

# Strict mode (fail on invalid rows)
python scripts/evaluate_live_session.py \
  --session-dir /path/to/session \
  --strict
```

## What It Does

Reads `fills.csv` from a session directory and computes:

- **Fill Summary:** Count, symbols, time range
- **Aggregate Metrics:** Total notional, total quantity, VWAP (overall + per symbol)
- **Side Breakdown:** Buy/sell counts, quantities, notional values
- **Realized PnL:** FIFO-matched per symbol and total

## Input Format

**Expected CSV:** `fills.csv` (default, configurable via `--fills-csv`)

```csv
ts,symbol,side,qty,fill_price
2025-01-15T10:00:00Z,BTC/USD,buy,0.1,50000.0
2025-01-15T10:05:00Z,ETH/USD,sell,1.5,3000.0
```

**Requirements:**
- `ts`: ISO8601 timestamp (timezone-aware, `Z` suffix supported)
- `symbol`: Asset pair (e.g., `BTC/USD`)
- `side`: `buy` or `sell` (case-insensitive)
- `qty`: Positive float
- `fill_price`: Positive float

## Output Modes

### Text (Human-Readable)

Default format. Example:

```
Session Directory: /path/to/session

=== Fill Summary ===
Total Fills: 2
Symbols: BTC/USD, ETH/USD
Time Range: 2025-01-15T10:00:00+00:00 to 2025-01-15T10:05:00+00:00

=== Aggregate Metrics ===
Total Notional: 9500.00
Total Quantity: 1.6000
VWAP (Overall): 5937.50

=== VWAP per Symbol ===
  BTC/USD: 50000.00
  ETH/USD: 3000.00

=== Side Breakdown ===
BUY:
  Count: 1
  Quantity: 0.1000
  Notional: 5000.00
SELL:
  Count: 1
  Quantity: 1.5000
  Notional: 4500.00

=== Realized PnL (FIFO) ===
Total Realized PnL: 0.00
```

### JSON (Machine-Readable)

Use `--format json` or `--write-report`:

```json
{
  "total_fills": 2,
  "symbols": ["BTC/USD", "ETH/USD"],
  "start_ts": "2025-01-15T10:00:00+00:00",
  "end_ts": "2025-01-15T10:05:00+00:00",
  "total_notional": 9500.0,
  "total_qty": 1.6,
  "vwap_overall": 5937.5,
  "vwap_per_symbol": {
    "BTC/USD": 50000.0,
    "ETH/USD": 3000.0
  },
  "side_breakdown": {
    "buy": {"count": 1, "qty": 0.1, "notional": 5000.0},
    "sell": {"count": 1, "qty": 1.5, "notional": 4500.0}
  },
  "realized_pnl_total": 0.0,
  "realized_pnl_per_symbol": {}
}
```

## FIFO PnL Logic

**How it works:**
- **Buys** open new lots at their fill price
- **Sells** match against oldest open lots (FIFO)
- **Realized PnL** = Σ (sell_price - buy_price) × matched_qty

**Example:**

```csv
ts,symbol,side,qty,fill_price
2025-01-15T10:00:00Z,BTC/USD,buy,1.0,100.0
2025-01-15T10:05:00Z,BTC/USD,buy,1.0,110.0
2025-01-15T10:10:00Z,BTC/USD,sell,1.5,120.0
```

**Calculation:**
1. Sell 1.0 @ 120 matches first buy @ 100: `(120-100) × 1.0 = 20`
2. Sell 0.5 @ 120 matches second buy @ 110: `(120-110) × 0.5 = 5`
3. **Total PnL:** `20 + 5 = 25`

## Error Handling

### Strict Mode (`--strict`)

**Fails on:**
- Invalid timestamps (missing timezone, malformed ISO8601)
- Invalid side values (not `buy` or `sell`)
- Non-numeric qty/fill_price
- Negative qty/fill_price
- Sell quantity exceeds available lots (no short positions)

**Exit code:** `1` (parsing/validation error) or `2` (file not found, I/O error)

### Best-Effort Mode (Default)

**Behavior:**
- Skips invalid rows with warnings
- Treats excess sell quantity as short lot with PnL=0
- Continues processing valid data

**Exit code:** `0` (success) or `2` (critical I/O error only)

## Safety Notes

✅ **No Live Trading Paths Affected** – OFFLINE ONLY tool
- This tool does NOT connect to exchanges or live systems
- It only reads local CSV files
- No API calls, no network activity
- Safe for post-mortem analysis

✅ **Default Text Output Unchanged** – Backward compatible

✅ **No New Heavy Dependencies** – Pure stdlib

✅ **Deterministic Tests** – No flakiness

⚠️ **Data Quality**
- Best-effort mode may hide data quality issues
- Use `--strict` for validation during testing
- Review warnings in best-effort mode output

## Golden Sample Evaluation

Deterministic test case for quick sanity checks after refactoring or deployment.

**Use Case:** Smoke test to verify FIFO PnL logic and output format without real session data.

### Quick Command (Text Output)

```bash
# Create golden sample fixture
python3 -c "
from datetime import datetime, timezone
from src.live_eval.live_session_eval import Fill, compute_metrics

# FIFO PnL example: Buy 1.0@100, Buy 1.0@110, Sell 1.5@120
# Expected PnL: (120-100)*1.0 + (120-110)*0.5 = 20 + 5 = 25
fills = [
    Fill(datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc), 'BTC/USD', 'buy', 1.0, 100.0),
    Fill(datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc), 'BTC/USD', 'buy', 1.0, 110.0),
    Fill(datetime(2025, 1, 15, 10, 10, 0, tzinfo=timezone.utc), 'BTC/USD', 'sell', 1.5, 120.0),
]
metrics = compute_metrics(fills)
print(f\"Total PnL: {metrics['realized_pnl_total']}\")
assert metrics['realized_pnl_total'] == 25.0, 'Golden sample failed!'
print('✓ Golden sample passed')
"
```

**Expected Output:**
```
Total PnL: 25.0
✓ Golden sample passed
```

### Quick Command (JSON Output)

```bash
# Golden sample with JSON metrics
python3 -c "
import json
from datetime import datetime, timezone
from src.live_eval.live_session_eval import Fill, compute_metrics

fills = [
    Fill(datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc), 'BTC/USD', 'buy', 1.0, 100.0),
    Fill(datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc), 'BTC/USD', 'buy', 1.0, 110.0),
    Fill(datetime(2025, 1, 15, 10, 10, 0, tzinfo=timezone.utc), 'BTC/USD', 'sell', 1.5, 120.0),
]
metrics = compute_metrics(fills)
print(json.dumps({
    'realized_pnl_total': metrics['realized_pnl_total'],
    'total_notional': metrics['total_notional'],
    'vwap_overall': metrics['vwap_overall'],
}, indent=2))
"
```

**Expected Output:**
```json
{
  "realized_pnl_total": 25.0,
  "total_notional": 390.0,
  "vwap_overall": 111.42857142857143
}
```

**Use Cases:**
- Post-refactor sanity check (deterministic PnL calculation)
- CI smoke test (optional, can be added to test suite)
- Quick verification after deployment

---

## Testing

```bash
# Run tests
python -m pytest tests/test_live_eval_io.py tests/test_live_eval_metrics.py -v

# Expected: 19 passed
```

## Implementation

**Library:** `src/live_eval/`
- `live_session_eval.py` – Core `Fill` dataclass, FIFO PnL logic
- `live_session_io.py` – CSV parsing with timezone-aware timestamps

**CLI:** `scripts/evaluate_live_session.py`

**Tests:**
- `tests/test_live_eval_io.py` – 8 tests for CSV parsing/validation
- `tests/test_live_eval_metrics.py` – 11 tests for metrics/FIFO PnL

## Exit Codes

- `0` – Success
- `1` – Parsing/validation error (only in strict mode)
- `2` – Critical error (file not found, I/O error, unexpected exception)

## Common Use Cases

### Post-Session Analysis

```bash
# Quick overview
python scripts/evaluate_live_session.py --session-dir ~/live_sessions/2025-01-15

# Generate report for archival
python scripts/evaluate_live_session.py \
  --session-dir ~/live_sessions/2025-01-15 \
  --write-report
```

### Automated Monitoring

```bash
# Machine-readable output for monitoring pipeline
python scripts/evaluate_live_session.py \
  --session-dir /var/peak_trade/sessions/latest \
  --format json \
  > /tmp/session_metrics.json
```

### Data Quality Validation

```bash
# Strict validation (fail on any issues)
python scripts/evaluate_live_session.py \
  --session-dir ~/live_sessions/2025-01-15 \
  --strict

# Exit code 0 = all data valid
# Exit code 1 = data quality issues detected
```

## Troubleshooting

**Issue:** `ERROR: Session directory does not exist`
- **Fix:** Check path, ensure directory exists

**Issue:** `ERROR: Fills CSV not found`
- **Fix:** Verify `fills.csv` exists in session directory, or use `--fills-csv <filename>`

**Issue:** `ERROR: CSV must contain columns`
- **Fix:** Verify CSV header has required columns: `ts,symbol,side,qty,fill_price`

**Issue:** `Parse error: Timestamp must be timezone-aware`
- **Fix:** Use ISO8601 with timezone (e.g., `2025-01-15T10:00:00Z` or `2025-01-15T10:00:00+00:00`)

**Issue:** `Sell quantity exceeds available lots` (strict mode)
- **Fix:** Check data integrity – are sells happening before corresponding buys?
- **Alternative:** Run in best-effort mode (remove `--strict` flag)

## Further Resources

- **Test Suite:** `tests/test_live_eval_*.py`
- **Implementation:** `src/live_eval/`
- **Related:** Session management, live execution monitoring
