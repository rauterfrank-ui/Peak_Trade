# P29 — Accounting v2 (avg cost + realized PnL)

## Objective
Add average-cost accounting and realized PnL on position reductions, extending P28.

## Invariants
- No shorting: position qty must never go below 0.
- Deterministic: same inputs → same outputs.
- Cash updates:
  - BUY: cash -= (qty * price + fee)
  - SELL: cash += (qty * price - fee)
- Avg cost:
  - BUY increases avg cost: new_avg = (old_qty*old_avg + buy_qty*buy_price) / (old_qty + buy_qty)
  - SELL does not change avg cost for remaining qty; if qty goes to 0, avg cost resets to 0.
- Realized PnL on SELL:
  - realized = (sell_price - avg_cost) * sell_qty - fee
  - (fee reduces realized PnL deterministically)

## Non-goals
- No leverage/margin, borrowing, funding, or per-lot tax accounting.
