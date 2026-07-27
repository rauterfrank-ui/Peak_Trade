# Cross-sectional open-gap pressure fade research program v1

## Status

`PROGRAM_CLOSED_NO_FURTHER_RESEARCH` — closed after Open Gap Pressure Fade v1
terminal `DEVELOPMENT_FAIL` (PR #5496), with strategy implementation present
(PR #5495). Documentary/registry truth reconciled; no successor selected.

## Identity

- Program: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1`
- Workstream: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_WORKSTREAM_V1`
- Family: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE`
- Strategy identity: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1`
- Terminal hypothesis: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1`
- Signal family: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE`
- Target phenomenon: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE`

## Binding

- SSOT: `config/research/cross_sectional_open_gap_pressure_fade_research_program_v1.json`
- Validator: `src/research/cross_sectional_open_gap_pressure_fade_research_program_v1.py`
- Lane backlog: `config/research/cross_sectional_open_gap_pressure_fade_hypothesis_backlog_v1.json`
- Measurement contract: `config/research/cross_sectional_open_gap_pressure_fade_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Implementation binding: `config/research/cross_sectional_open_gap_pressure_fade_v1_strategy_implementation_binding_v1.json`
- Development evidence: `docs/evidence/evaluate_cross_sectional_open_gap_pressure_fade_development_v1/`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`

## Terminal truth (immutable; verified)

- `STRATEGY_IMPLEMENTATION_PRESENT=true` (PR #5495)
- `DEVELOPMENT_VERDICT=DEVELOPMENT_FAIL` (PR #5496)
- `DEVELOPMENT_RUN_COUNT=1` / `RUN_SLOT_CONSUMED=true`
- `EVALUATION_AUTHORIZED=false` / `RETRY_AUTHORIZED=false`
- `HOLDOUT_ACCESSED=false` / `SEALED_ACCESSED=false`
- `PROMOTION_ELIGIBLE=false` / `RUNTIME_BOUND=false`
- `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false`
- `STEP_29R_ELIGIBLE=false` / `AUTONOMY_IS_NEXT=false`

## Gates (closed)

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=1` / `RUNNER_START_COUNT=1` / `RUN_SLOT_CONSUMED=true`
- `HOLDOUT_FORBIDDEN=true`
- `ECONOMIC_GATE_OPEN=false`
- `PROMOTION_ELIGIBLE=false`
- `LIVE&#47;ORDERS&#47;SHADOW&#47;PAPER&#47;TESTNET&#47;SCHEDULER=false`
- Master V2 / Double-Play / risk / sizing / execution: consume-only, no mutation

## Next step

`NEW_DISTINCT_RESEARCH_PROGRAM_OR_FULL_CANONICAL_SYSTEM_BINDING_OR_OTHER_EVIDENCE_CLASS_REQUIRES_OPERATOR_RATIFICATION`

Open Gap Pressure Fade is not an implementation or DEVELOPMENT candidate.
No new research program or evidence class is selected here.

## Non-actions

- No strategy reimplementation or DEVELOPMENT rerun
- No Holdout / Sealed advance
- No promotion / activation / automatic selection
- No runtime / orders
- No successor invention in this slice

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1
STATUS: PROGRAM_CLOSED_NO_FURTHER_RESEARCH
scope: research, offline-only, non-authorizing, documentary-registry-truth-reconciliation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
