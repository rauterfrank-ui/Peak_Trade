# Metrics integrity verdict — post-#5348

## STATUS=`FAIL`

## ECONOMIC_MEASUREMENT_VALID=`false`

## ECONOMIC_CLASS=`INVALID_ECONOMIC_MEASUREMENT`

The previously exported economic panel metrics are **not** a valid portfolio
measurement:

1. **Costs NOT_APPLIED** — fee_bps/slippage_bps are configured, but roundtrip
   ledger shows `entry_cost=exit_cost=0`, `fee_drag=0`, `pnl==gross_pnl`, and
   entry fills at bar close (0 bps). `COST_DRAG=0.0` is ledger-true but
   economically misleading.
2. **Capital double-counting** — prior `NET_RETURN` summed independent
   instrument returns.
3. **Sharpe mismatch** — prior panel Sharpe was a cross-sectional mean/std of
   instrument returns, not an equity-curve Sharpe; hence a tiny Sharpe can
   coexist with a large (invalid) summed return.
4. **No shared equity ledger** — PF/DD/Sharpe/Return were not computed from one
   portfolio equity curve.

Independent of any corrected proxy:

- `ECONOMIC_GATE_OPENED=false`
- `PROMOTION_ELIGIBLE=false`
- No economic promotion claim is authorized.

### Corrected reporting snapshot

- GROSS_PNL=`5066.899689424941`
- FEES_TOTAL=`0.0`
- SLIPPAGE_TOTAL=`0.0`
- NET_PNL=`5066.899689424941`
- COST_DRAG=`0.0`
- NET_RETURN (corrected equal-capital proxy)=`0.004293982787648256`
- NET_RETURN (prior invalid sum)=`0.5066899689424893`
- SHARPE (corrected)=`NOT_AVAILABLE`
- LEDGER_RECONCILIATION=`PASS`
- COST_APPLICATION=`NOT_APPLIED`
- CAPITAL_DOUBLE_COUNTING=`True`
