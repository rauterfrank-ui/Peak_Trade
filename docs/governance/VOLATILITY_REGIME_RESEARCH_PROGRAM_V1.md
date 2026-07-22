# VOLATILITY_REGIME_RESEARCH_PROGRAM_V1

Definition-only research-program SSOT for operator-authorized volatility-regime hypotheses.

## Active posture

- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Status: `DEFINITION_ONLY_PROGRAM_OPEN`
- Lane backlog status: `POST_TERMINAL_OPERATOR_DECISION_REQUIRED`
- Last strategy identity (historical): `VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1`
- `strategy_id=volatility_expansion_pullback_continuation` (SSOT drift reconciled)
- Active hypothesis inventory empty
- `development_evaluation_authorized=false`
- Canonical decision packet:
  `docs/governance/VOLATILITY_REGIME_POST_VEPC_LANE_LIFECYCLE_OPERATOR_DECISION_PACKET_V1.md`

## Terminal predecessors (retry forbidden)

Includes VCB, VEP, VDB, VDBX, `VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1`, and
`VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1`
(`FAIL_CLOSED_NO_RETRY` / `CONSUMED_NO_RETRY` / `UNPAIRABLE_ENTRY_NO_EXIT`).

## Safety

- `DEVELOPMENT_RUN_COUNT=1` (historical VEPC slot)
- `DEVELOPMENT_SLOT_CONSUMED=true`
- `DEVELOPMENT_EVALUATION_EXECUTED=false`
- `EVALUATION_RETRY_AUTHORIZED=false`
- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `HOLDOUT_ACCESSED=false`
- Master V2 / Double-Play / Risk / Sizing / Execution unchanged

## Next step

`OPERATOR_ENUMERATED_DECISION_REQUIRED_VIA_POST_VEPC_LIFECYCLE_DECISION_PACKET_V1`

Separate operator GO required to apply exactly one enumerated post-terminal decision.
No VEPC evaluation retry.

docs_token: DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
