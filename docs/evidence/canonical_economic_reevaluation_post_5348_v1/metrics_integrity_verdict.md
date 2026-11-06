# Metrics integrity verdict — post repair

## STATUS=`PARTIAL` (measurement valid; economics inconclusive)

## ECONOMIC_MEASUREMENT_VALID=`true`

## COST_APPLICATION=`APPLIED`

## LEDGER_RECONCILIATION=`PASS`

## EQUITY_RECONCILIATION=`PASS`

## CAPITAL_DOUBLE_COUNTING=`false`

## ECONOMIC_CLASS=`INCONCLUSIVE_UNSTABLE`

## ECONOMIC_GATE_OPENED=`false`

## PROMOTION_ELIGIBLE=`false`

### Answers to critical questions (repaired)

1. **COST_DRAG** is now non-zero (`≈22.88` on shared book) because MV2 bar closes
   apply fee+slippage cash drag via canonical cost owners.
2. **NET_RETURN** is `final_shared_equity &#47; 10000 - 1` from the equal-weight
   portfolio equity curve (not a sum of instrument returns).
3. **SHARPE** is annualized from hourly portfolio equity returns (`P=8760`), not
   cross-sectional instrument returns.
4. Capital is shared once (`initial_capital=10000`); sleeve curves are combined
   equal-weight (research model), not summed as independent 10k books.
5. Profit factor (net), drawdown, Sharpe, and return share the cost-applied ledger
   and the shared portfolio equity path.
6. LONG and SHORT roundtrips include entry/exit fee+slippage cash drag; stops use
   stop price fills without a second slippage layer.

### Superseded prior exports

Prior `COST_DRAG=0`, `NET_RETURN≈0.507`, `SHARPE≈0.041` are INVALID and must not
be reused for economic claims.
