# Panel-loader alignment root cause (implementation-only)

## Observed failure

Canonical evaluate attempt (`PR #5428`) terminated `FAIL_CLOSED` with:

`UNEXPECTED:ValueError:ALIGNMENT_GAP:okx:linear_perpetual:1INCH:USDT:USDT:perp`

Run budget remains consumed (`RUN_COUNT=1`, `RUNNER_START_COUNT=1`). No retry authorization.

## First divergent boundary

`src/research/cross_sectional_relative_strength_momentum_v1_development_evaluation_v1/panel_loader_v1.py`

After timestamp-intersection alignment, the loader treated **any** NaN in the member
DataFrame as an alignment gap (via `aligned.isna().any().any()` + `dropna()`).

## Reproduced fact

On the sealed DEVELOPMENT archive:

- timestamp intersection length equals each member length (no missing timestamps)
- required OHLCV columns (`open/high/low/close/volume`) have **zero** NaNs on the grid
- auxiliary column `volatility_estimate` contains warmup NaNs (46–59 rows)

Therefore the fail-closed exit was caused by **auxiliary-column warmup NaNs**, not by
OHLCV timestamp misalignment / wide-vs-long / symbol-universe drift.

## Repair class

Implementation-only: validate alignment exclusively on columns required to materialize
`PanelBarV1`. Do not execute evaluation, do not reopen the run slot.
