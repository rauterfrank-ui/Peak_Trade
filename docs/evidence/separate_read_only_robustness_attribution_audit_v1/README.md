# SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1

```text
AUDIT_ID=SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1
BASE_SHA=891044056537a4033e6136ba01652a0a2c6e76b7
REFERENCE_PR=5349
STATUS=PASS
ECONOMIC_CLASS=INCONCLUSIVE_UNSTABLE
ECONOMIC_MEASUREMENT_VALID=true
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
PRODUCTIVE_FILES_CHANGED=false
LIVE_AUTHORIZED=false
ORDERS=false
NEXT_RECOMMENDED_ACTION=ACQUIRE_LONGER_CHRONOLOGICAL_PIT_DATASET
```

## Purpose

Forensic read-only explanation of why the post-#5349 *validly measured*
canonical MV2 / Double-Play chain remains economically
`INCONCLUSIVE_UNSTABLE` with thin net economics.

## Reproduction

Shared-book metrics reproduced from sealed reference artifacts
(`checkpoint_baseline_wf.json` trades_compact + `portfolio_equity.csv`) with
CRS scale `1/118`. Full 118-member panel was **not** re-executed (806s probe
already sealed in #5349).

| Metric | Reference | Reproduced match |
|---|---:|:---:|
| Total trades | 454 | yes |
| LONG / SHORT | 69 / 385 | yes |
| Net return | 0.00232538607176469 | see baseline_reproduction.json |
| Sharpe | 0.1909766065222959 | see baseline_reproduction.json |
| PF net | 1.1135430312470467 | see baseline_reproduction.json |
| MaxDD | -0.020480218347394656 | see baseline_reproduction.json |

## Headline attribution

- LONG net PnL (shared book): `57.678107`
- SHORT net PnL (shared book): `-34.424246`
- Top positive instrument: `TURBO`
- Top negative instrument: `ORDI`
- Exit pattern: stop_loss dominates losses; end_of_data concentrates wins
- Cost drag ≈ half of gross edge; modelled cost stress flips return negative
- Scope/Composition: DATA_GAP (no classifier invented)

## Safety

No strategy / parameter / runtime / order / live changes.
Master V2 remains sole direction authority. Gate stays closed.
