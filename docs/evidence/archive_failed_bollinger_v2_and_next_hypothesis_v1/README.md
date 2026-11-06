# Bollinger v2 sealed long-panel terminal economic fail archive + next hypothesis v1

```text
SLICE=ARCHIVE_FAILED_BOLLINGER_V2_AND_NEXT_HYPOTHESIS_V1
BASE_SHA=31ef4529aeaf4cc1e1d70df6193712e5f1294e5a
SOURCE_PR=5354
SOURCE_EVIDENCE=offline_economic_reevaluation_sealed_long_panel_v1
ECONOMIC_CLASS=FAIL_ECONOMIC
PROMOTION_ELIGIBLE=false
ECONOMIC_GATE_OPENED=false
IMPLEMENTATION=false
RUNTIME=false
ORDERS=false
```

## Purpose

1. Append-only archive of `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
   as terminal `FAIL_ECONOMIC` after sealed 65-instrument long-panel evaluation.
2. Evidence-grounded root-cause synthesis (no new full-panel backtest).
3. Define exactly one research-only successor hypothesis:
   `REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1`.
4. Reserve the sealed panel as final holdout; forbid tuning/selection on it.

## Archive truth

Binding fields updated in-place with preserved prior statuses under
`terminal_economic_archive_v1` (append-only; no history delete). Closeout owner:
`config/research/bollinger_bands_v2_sealed_long_panel_terminal_economic_fail_archive_and_next_hypothesis_v1.json`.

## Safety

No productive trading-logic change beyond research binding archival metadata.
No strategy implementation, no parameter search, no promotion, no runtime.
