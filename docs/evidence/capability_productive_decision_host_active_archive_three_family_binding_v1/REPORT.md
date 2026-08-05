<!-- docs_token: DOCS_TOKEN_CAPABILITY_PRODUCTIVE_DECISION_HOST_ACTIVE_ARCHIVE_THREE_FAMILY_BINDING_V1 -->
# REPORT — CAPABILITY_PRODUCTIVE_DECISION_HOST_ACTIVE_ARCHIVE_THREE_FAMILY_BINDING_V1

## Verdict

`HOST_IMPLEMENTED` with active-archive binding for `dynamic_scope` and
`canonical_decision`. Double Play remains
`HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH` because productive
`IntegratedOfflineReplayIntermediateV1` does not expose the Decision-typed
inputs required by `build_dashboard_display_snapshot` without inventing new
mapping semantics.

## Smoke

- ok=true
- instrument=`SATS-USDT-SWAP` from archive selection authority
- cycles_committed=8
- dashboard PID unchanged=737
- `LONG_RUNNING_PHASE_9_2_PROVEN=false`

## Families

- dynamic_scope: exported=true materialized=true loader_ok=true
- canonical_decision: exported=true materialized=true loader_ok=true
- double_play: HARD_STOP (not exportable)

## Boundaries

O2 remains `dashboard-only`. No order/credential path. Dashboard remains
read-only consumer (`DASHBOARD_AUTHORITY_EFFECT=NONE`).
