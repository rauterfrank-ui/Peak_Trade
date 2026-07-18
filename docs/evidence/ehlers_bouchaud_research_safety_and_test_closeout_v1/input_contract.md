# Research-Only Input Contract

Reuse existing `BaseStrategy.generate_signals` + registry conventions. No parallel schema.

## Shared vocabulary

| Output | Meaning |
|---|---|
| `0` | Flat / Neutral — **no entry intent** |
| `1` | Long |
| empty series | Empty input |
| `-1` | **Forbidden** (Long/Flat only) |

## Shared gates

| Condition | Behavior |
|---|---|
| Missing `close` | `ValueError` (existing fail-closed) |
| Empty DataFrame | Empty int series |
| `len < lookback` / `lookback_ticks` | All Flat + `insufficient_history=True` |
| Non-unique or non-monotonic-increasing index | All Flat + `invalid_input=True` |
| Non-finite prices (NaN/Inf) after numeric coerce | All Flat + `invalid_input=True` |
| No forward-fill / backfill / imputation | Guaranteed |

## Ehlers-specific

- Valid path unchanged: Super Smoother on finite `close`, Long iff `close > smooth`.
- Constant series: deterministic Flat/Long from formula (typically Flat when equal).

## Bouchaud-specific

- Valid OHLC/close/bid-ask paths unchanged for clean sufficient-length inputs.
- `volume` column present + negative or non-finite → Flat (`invalid_volume`).
- `high < low` → Flat (`high_lt_low`).
- Zero-range candles: existing epsilon / fillna path (no ZeroDivision).
- `attrs.proxy_data_risk = "HIGH"` on successful proxy path.

## Determinism / look-ahead

- Causal filters/rolling only (past + current bar).
- Prefix consistency tests enforce no look-ahead.
