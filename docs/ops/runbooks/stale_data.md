# Data Freshness & Gap Detection — Hard Gate

## Goal
Block or degrade trading when market/data inputs are stale or have gaps.

## Definitions
- **Freshness**: maximum allowed age of last datapoint per symbol/timeframe.
- **Gap**: missing expected bars/ticks beyond tolerance.

## Gate Behavior
- **HARD BLOCK** (default): if freshness/gap fails → `NO_TRADE=true` and record reason.
- **DEGRADE MODE** (optional future): allow trading only with reduced risk budget.

## Evidence
- Gate emits structured decision payload: `gate_id`, `status`, `reasons[]`, `asof_utc`, `inputs{...}`.
