# Downstream economic reevaluation plan (after qualification PASS)

## Hard preconditions

1. Dataset qualification `PASS` (or operator-GO `PARTIAL` with reduced claims).
2. Measurement contract from #5349 still bound (`COST_APPLICATION=APPLIED`, shared portfolio equity).
3. `ECONOMIC_GATE_OPENED=false`, `PROMOTION_ELIGIBLE=false` remain forced.
4. Master V2 &#47; Double Play authority unchanged; `entry_side=NONE`.
5. No parameter search; fixed sealed strategy binding unless a **separate** operator-GO research slice says otherwise.

## Allowed read-only analyses

| Analysis | Notes |
|---|---|
| Anchored Walk-Forward | Train&#47;test folds on chrono panel; report sign stability |
| Regime slices | Calendar &#47; volatility &#47; drawdown regimes **only if** labels come from existing canonical fields or pre-declared external series — no new ad-hoc classifier without GO |
| Instrument slices | Sleeve contribution; LOO on shared book |
| Time slices | Non-overlapping chrono blocks (diagnostic + true OOS folds) |
| Bootstrap &#47; block bootstrap | On portfolio returns or trade blocks; seed versioned; no independent sleeve-sum fallacy |
| Fee &#47; slippage stress | Modelled bps stress + optional path re-sim if harness exists |
| Parameter stability | Only if already in non-tuning sensitivity contracts; else OUT OF SCOPE |
| Turnover | Trade counts, notional turnover, cost share of gross |
| Gross &#47; Net PnL, PF, Sharpe, MaxDD, trade count | Shared-book definitions only |
| Long &#47; Short attribution | Direction splits without changing exclusivity |
| Exit &#47; Entry attribution | Using ledger exit reasons; MAE&#47;MFE only if exported |
| Concentration risk | Herfindahl &#47; top-k PnL share |

## Explicitly forbidden in the follow-on evaluation

- Opening economic gate or marking promotion eligible
- Grid &#47; Bayesian &#47; genetic tuning to lift Sharpe &#47; PF
- Changing stops, thresholds, composition, switch, risk, sizing
- Live &#47; paper &#47; testnet &#47; scheduler activation
- Declaring true OOS when folds still share acquisition bugs

## Suggested follow-on workstream name

`CANONICAL_ECONOMIC_REEVALUATION_ON_CHRONO_3Y_DATASET_V1`  
Trigger only after dataset qualification PASS evidence is merged.
