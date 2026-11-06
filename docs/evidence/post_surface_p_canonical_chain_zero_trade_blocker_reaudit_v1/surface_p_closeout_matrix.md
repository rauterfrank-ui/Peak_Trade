# Surface-P Closeout Matrix

**HEAD:** `43558204d4f7bcab30ce9e8357d2513a9a5f0970`  
**PR #5327:** `660da90f` — CRS/OI envelope-effect dispatch  
**PR #5328:** `43558204` — smoke integrated envelope = CHOP_GUARD scenario composition

## Harness owners

| Surface | Owner |
|---------|--------|
| Full-system / 4-way parity | `src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py` |
| Contract suite | `tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py` |
| Full bar-sequence completion | `tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py` |
| Runtime bridge bound-not-activated | `tests/trading/master_v2/test_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py` |

## Key asserts (preserved)

| Assert | Role |
|--------|------|
| `assert_non_authority_boundary_v0` | Unbound: `execution_eligible=false`, `quantity_status==NOT_BOUND`, effects `NONE` |
| `assert_capital_risk_sizing_non_authority_boundary_v0` | CRS `BOUND_OFFLINE` → `quantity_status ∈ {PASS,REDUCE,BLOCK}` |
| `assert_canonical_order_intent_non_authority_boundary_v0` | OI `BOUND_OFFLINE` → ref present; still non-authority |
| `assert_surface_p_integrated_envelope_non_authority_boundary_v0` | Effect-based dispatcher (not lane-exception) |
| `build_surface_p_four_way_smoke_integrated_envelope_v0` | Same CHOP_GUARD matrix as scenario lane |

## Closeout confirmations

| Invariant | Status | Evidence |
|-----------|--------|----------|
| No generic assert weakening | **CONFIRMED** | Generic path still requires `NOT_BOUND`; CRS path is additive dispatch |
| No lane-specific exception hiding wrong semantics | **CONFIRMED** | `AssertionError` → `integrated_lane_bound=False` + fail reason |
| No Direction/Quantity from Non-Authority path | **CONFIRMED** | Scenario/smoke envelopes composition-only; qty only under CRS `BOUND_OFFLINE` |
| No asymmetric Long/Short treatment | **CONFIRMED** | Long/Short parity + CRS/OI symmetric dispatch tests |
| No Execution Eligibility change | **CONFIRMED** | Bound/unbound remain `execution_eligible=false` |
| Non-Authority Dispatch preserved | **CONFIRMED** | Dispatcher routes CRS / OI / generic |
| CRS-aware asserts preserved | **CONFIRMED** | #5327 path intact |
| Order-Intent-aware asserts preserved | **CONFIRMED** | #5327 path intact |
| UNBOUND/NOT_BOUND fail-closed | **CONFIRMED** | Generic + leak contracts |
| Integrated lane bound | **CONFIRMED** | Smoke composition aligned; 4-way bound |
| Quantity statuses PASS\|REDUCE\|BLOCK when CRS bound | **CONFIRMED** | CRS assert + bar-sequence contracts |
| LIVE_AUTHORIZED / ORDERS_ENABLED false | **CONFIRMED** | Unchanged governance defaults |

## Composition alignment (#5328)

- Scenario lane: `evaluate_scenario_matrix_for_side_state_v0(SideState.CHOP_GUARD_BLOCK)`
- Integrated smoke: `build_surface_p_four_way_smoke_integrated_envelope_v0` uses the **same** matrix evaluation
- Alignment predicate: `integrated_envelope.composition_status == scenario_env.composition_status`
- Smoke quantity remains `NOT_BOUND` (unbound CHOP path)

## Prior evidence reused

- `docs/evidence/surface_p_smoke_composition_alignment_v1/`
