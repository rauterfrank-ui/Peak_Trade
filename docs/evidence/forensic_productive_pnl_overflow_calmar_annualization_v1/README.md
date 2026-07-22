# Forensic: productive PnL OverflowError → Calmar annualization

```text
SCOPE=INFRASTRUCTURE_ONLY
BASE_SHA=c1e20a28faee4242d93309942ee4548826c5d668
FIRST_LOSS_BOUNDARY=src/backtest/stats.py::compute_calmar_ratio
OVERFLOW_CLASS=ACCUMULATION
PRODUCTIVE_PNL_REEXECUTED=false
DEVELOPMENT_EVALUATION_REEXECUTED=false
HOLDOUT_ACCESSED=false
STRATEGY_PARAMETERS_CHANGED=false
SECOND_PNL_TRUTH_CREATED=false
```

## Finding

Terminal VCB/VDB evidence recorded `UNEXPECTED:OverflowError:(34, 'Result too large')`
during productive PnL/metrics materialization. Static + synthetic reproduction shows
the exception is raised in `compute_calmar_ratio` when:

1. equity has non-zero drawdown (annualization path is entered),
2. `total_return` is explosively large,
3. `years = (len(equity)-1) &#47; periods_per_year` is small (hourly `24*365`).

Python's `**` raises `OverflowError` before the existing `np.isfinite` guard runs.

## Not repaired in this slice

Equity construction in
`productive_exit_pnl_evaluator_v1._metrics_from_trades`
(`UNIT_RISK_NOTIONAL=1.0` + absolute multi-instrument quote PnL) amplifies
`total_return`. Changing that would alter evaluation metric semantics and needs a
separate operator GO.

## Infra-only repair

Catch `OverflowError` on the annualization power and return the existing catastrophic
non-finite Calmar sentinel. No strategy parameters, hypothesis, or PnL primitive change.

---
docs_token: DOCS_TOKEN_FORENSIC_PRODUCTIVE_PNL_OVERFLOW_CALMAR_ANNUALIZATION_V1
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
---
