# Canonical Economic Reevaluation post-#5348 v1

```text
SLICE=CANONICAL_ECONOMIC_REEVALUATION_POST_5348_V1
BASE_SHA=8eb90ecf5b8f4a7cef4b7621aa146bfd6f1ffacc
BRANCH=audit/canonical-economic-reevaluation-post-5348-v1
PRODUCTIVE_FILES_CHANGED=true
STATUS=PARTIAL
ECONOMIC_CLASS=INCONCLUSIVE_UNSTABLE
ECONOMIC_MEASUREMENT_VALID=true
COST_APPLICATION=APPLIED
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
ENTRY_SIDE=NONE
LIVE_AUTHORIZED=false
ORDERS=false
```

## Verdict

Measurement chain repaired: fee/slippage cash drag is applied on the MV2 legacy
bar path, and panel Return/Sharpe/MaxDD come from one shared research portfolio
equity (`initial_capital=10000`). Economics remain `INCONCLUSIVE_UNSTABLE`
(walk-forward/stress); gate stays closed.

## Key repaired metrics (shared book)

| Field | Value |
|---|---:|
| Total trades | 454 |
| LONG / SHORT | 69 / 385 |
| Gross PnL | 46.13329289862826 |
| Fees | 15.25295478732169 |
| Slippage | 7.626477393660845 |
| Net PnL | 23.253860717645743 |
| Cost drag | 22.87943218098253 |
| Final equity | 10023.253860717647 |
| Net return | 0.00232538607176469 |
| Profit factor (net) | 1.1135430312470467 |
| Sharpe (hourly→8760) | 0.1909766065222959 |
| Max drawdown | -0.020480218347394656 |

## Prior invalid exports (superseded)

`COST_DRAG=0`, summed instrument `NET_RETURN≈0.507`, cross-sectional `SHARPE≈0.041`.

## Safety

`ECONOMIC_GATE_OPENED=false`, `PROMOTION_ELIGIBLE=false`. Productive change limited
to enabling bound cost application on the MV2/legacy bar close path; no strategy,
direction, risk, sizing, execution, or live semantics changes.
