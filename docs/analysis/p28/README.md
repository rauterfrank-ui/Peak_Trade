# P28 — Backtest Loop Integration v3 (positions + cash v1)

This phase introduces deterministic accounting v1: apply FillRecord streams to update
position and cash. It is deliberately minimal and extendable.

## Invariants
- Deterministic: same inputs ⇒ same outputs.
- BUY fills decrease cash by (qty * price) + fees; position increases by qty.
- SELL fills increase cash by (qty * price) - fees; position decreases by qty (no shorting in v1 unless explicitly enabled).
- Fees/slippage are already embedded in fill price/fee fields; do not re-apply.

## Non-goals
- Funding, borrow fees, leverage/margin, liquidation.
- Multi-asset portfolio aggregation (beyond simple mapping).
