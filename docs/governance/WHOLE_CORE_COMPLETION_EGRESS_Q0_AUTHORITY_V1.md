# Whole-Core completion egress + Q0 authority ratification v1

`AUTHORITY_EFFECT=NONE` · `RUNTIME_AUTHORIZATION_EFFECT=NONE`

Machine contract: `config/governance/whole_core_completion_egress_q0_authority_v1.json`

Source census: **WHOLE_CORE_E2E_AND_EXECUTE_EGRESS_CENSUS_V1**

## Scope

This package closes **CURRENT** completion debt only. It does **not** authorize
Live POST, wire send, continuous run, N>1, Learning productive apply, or
optimizer write-back.

## WP-A — F-01 egress proof

`current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py`
is an **intentionally isolated Owner-GO POST slice** (`POST_GO_STATUS=UNCONSUMED`).
It is classified in `pre_external_to_external_effect_boundary_bounded_wp_v1`
alongside other isolated POST slices. No productive CURRENT reachability without
the scoped POST Owner-GO.

## WP-B — F-02 fresh trusted economic basis

For the **Full-Core enter-live** path, F-02 is **governance truth repair** after
Treasury C08 (#6827):

1. On ENTER, `join_current_productive_enter_live_29p_before_venue_plan_v1` requires
   one trusted read-only balance GET (`details[ccy=USDC].availEq`).
2. The observation is delegated only through
   `execute_current_productive_treasury_single_source_capital_handoff_v1`
   (`FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT=1`,
   `TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE=false`).

The standalone Owner-GO module
`current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1`
remains a **separate evidence/Owner-GO surface**; it is not a second parallel
productive Q0 owner on the enter-live chain.

Read-only GET **≠** POST **≠** Live send.

## WP-C — Q0/Q1 ratification

- **Q0 (Full-Core productive):** `ops.governed_productive_account_equity_authority_producer_v1`
- **Q1 (MV2 intent-bound quantity algebra):** `src.governance.capital_risk_sizing_v1`
- **Q1 owner count (Full-Core CURRENT):** 1

Offline/scoped sizing surfaces remain inventory-scoped; they are not competing
CURRENT Full-Core Q1 owners.

## WP-D — Learning / Q6 / Q8

`CURRENT_PRODUCTIVE_Q6_OWNER=NONE`, `CURRENT_PRODUCTIVE_Q8_OWNER=NONE`,
`LEARNING_PRODUCTIVE_AUTHORITY=NONE`, no productive bypass proven.

## WP-E — C2

Companion C2 remains **UNRESOLVED**. It does **not** block Full-Core Q0/Q1 or
Treasury on the enter-live path (`C2_BLOCKS_CURRENT_Q0_Q1=false`,
`C2_BLOCKS_TREASURY=false`).

## Verification

- `prove_pre_external_to_external_effect_boundary_v1()` → `ok=true`
- `prove_whole_system_connection_closure_v1()` → `ok=true`
- `tests/ops/test_whole_core_completion_egress_q0_authority_v1.py`
