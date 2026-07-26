# Cross-sectional short-horizon return-reversal research program v1

## Status

`PROGRAM_CLOSED_NO_FURTHER_RESEARCH` — closed after CSRHR v1 terminal
`DEVELOPMENT_FAIL` via explicit `CLOSE_LANE_NO_FURTHER_RESEARCH`.
No successor. Historical implementation and Development evidence preserved.

## Identity

- Program: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1`
- Family: `CROSS_SECTIONAL_RETURN_REVERSAL`
- Strategy identity: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1`
- Terminal hypothesis: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1`
- Signal family: `CROSS_SECTIONAL_RETURN_REVERSAL`
- Target phenomenon: `SHORT_HORIZON_CROSS_SECTIONAL_RELATIVE_RETURN_REVERSAL`

## Binding

- SSOT: `config/research/cross_sectional_short_horizon_return_reversal_research_program_v1.json`
- Validator: `src/research/cross_sectional_short_horizon_return_reversal_research_program_v1.py`
- Lane backlog: `config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json`
- Measurement contract: `config/research/cross_sectional_short_horizon_return_reversal_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Decision packet: `config/research/cross_sectional_short_horizon_return_reversal_program_definition_operator_decision_packet_v1.json`
- Development evidence: `docs/evidence/evaluate_cross_sectional_short_horizon_return_reversal_development_v1/`
- Closeout evidence: `docs/evidence/csrhr_v1_terminal_retirement_closeout_v1/`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`

## Terminal truth (immutable)

- `DEVELOPMENT_VERDICT=DEVELOPMENT_FAIL`
- `ECONOMIC_VALIDITY_STATUS=FAIL`
- `RUN_SLOT_CONSUMED=true`
- `RERUN_PERFORMED=false`
- `HOLDOUT_ACCESSED=false`
- `SEALED_ACCESSED=false`
- `ACTIVATION_ELIGIBLE=false`
- `AUTOMATIC_SELECTION_ENABLED=false`
- `PROMOTION_PERFORMED=false`

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

`LANE_CLOSED_NO_FURTHER_RESEARCH_NO_EXECUTABLE_GO`

New research requires a separately operator-authorized program identity.

## Non-actions

- No Development reevaluation of CSRHR v1
- No Holdout / Sealed advance
- No promotion / activation / automatic selection
- No runtime / orders
- No successor invention in this slice

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1
STATUS: PROGRAM_CLOSED_NO_FURTHER_RESEARCH
scope: research, offline-only, non-authorizing, terminal-retirement-closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
