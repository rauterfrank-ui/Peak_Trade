# Limitations and blockers

## Limitations

1. Production lifecycle SSOT is the existing validated registry snapshot (live-instrument
   derived). Historical delistings absent from that snapshot remain uncovered.
2. `LRC-USDT-SWAP` is present in the production registry but no longer served by the
   public instruments/candles API (`OKX_ERROR_CODE:51001`); it is excluded from enrichment
   and is not in the long panel.
3. Public candle earliest timestamps can precede registry `listing_time` by <1h (bar skew)
   or, for some names, trigger `PUBLIC_HISTORY_BEFORE_LISTING` exclusion (>1h).
4. Common panel start is governed by the youngest included instrument (HBAR listing
   ~2023-08-16), not the full chrono_3y target start 2021-09-01.
5. Production `LUNA-USDT-SWAP` shows continuous public history from its registry listing
   (2022-05-28); the earlier scaffold-sample LUNA finding does not apply to this SSOT.

## Blockers for promotion / economics

- Economic Gate remains closed; this slice only authorizes later offline reevaluation
  readiness when criteria are met.
- No Sharpe/PnL/edge claims.

## Explicit non-claims

- MASS_UNBOUNDED_DOWNLOAD=false (bounded long-panel window only)
- CREDENTIALS_USED=false
- ORDERS=false
- ECONOMIC_GATE_OPENED=false
- PROMOTION_ELIGIBLE=false
