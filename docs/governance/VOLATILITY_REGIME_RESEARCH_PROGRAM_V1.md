# VOLATILITY_REGIME_RESEARCH_PROGRAM_V1

Definition-only research-program SSOT for operator-authorized volatility-regime hypotheses.

## Active posture

- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Status: `DEFINITION_ONLY_PROGRAM_OPEN`
- Lane backlog status: `AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS`
- Last strategy identity (historical): `VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1`
- `strategy_id=volatility_expansion_pullback_continuation` (SSOT drift reconciled)
- Active hypothesis inventory empty
- `development_evaluation_authorized=false`
- Explicit waiting decision applied; no successor identity created
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

`AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS_ENUMERATED_FOLLOW_ON_REQUIRED_CLOSE_LANE_OR_CREATE_SUCCESSOR_VIA_POST_VEPC_PACKET_V1`

Separate operator GO required to apply exactly one remaining enumerated follow-on
(`CLOSE_LANE_NO_FURTHER_RESEARCH` or `CREATE_SUCCESSOR_HYPOTHESIS` with identity+mechanism).
No VEPC evaluation retry. No implicit CLOSE/CREATE authorization.

docs_token: DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
