# P30 — Equity Curve v1

This phase introduces a deterministic equity curve primitive for backtests.

## Inputs
- FillRecord (P26)
- AccountingV2 (P29)

## Output (Row Schema)
- ts (int or bar index)
- cash
- position_qty / position_value
- realized_pnl
- unrealized_pnl
- fees
- equity = cash + position_value

## Invariants
- Deterministic given same inputs
- equity == cash + position_value (within float tolerance)
- fees reduce cash/equity exactly once
