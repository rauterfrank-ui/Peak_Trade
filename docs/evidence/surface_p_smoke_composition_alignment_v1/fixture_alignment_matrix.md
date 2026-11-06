# Fixture Alignment Matrix

## Before

| Field | Scenario lane (`evaluate_surface_p_four_way_parity_v0`) | Integrated smoke (`_run(3500→3600)`) |
|-------|--------------------------------------------------------|-------------------------------------|
| Side / matrix input | `SideState.CHOP_GUARD_BLOCK` | default / long path |
| `composition_status` | `chop_guard_block` | `long_selected` |
| `quantity_status` | `NOT_BOUND` | `REDUCE` |
| `risk_sizing_effect` | `NONE` | `BOUND_OFFLINE` |
| `order_intent_effect` | `NONE` | `BOUND_OFFLINE` |
| Non-authority assert | PASS (generic unbound) | PASS (CRS-aware dispatch) |
| `integrated_lane_bound` | — | `true` |
| Composition aligned | — | `false` |
| Fail reason | — | `integrated_scenario_composition_not_aligned` |

## After

| Field | Scenario lane | Integrated smoke (`build_surface_p_four_way_smoke_integrated_envelope_v0`) |
|-------|---------------|-----------------------------------------------------------------------------|
| Matrix owner | same `evaluate_scenario_matrix_for_side_state_v0(CHOP_GUARD_BLOCK)` | **same call pattern / single truth** |
| `composition_status` | `chop_guard_block` | `chop_guard_block` |
| `quantity_status` | `NOT_BOUND` | `NOT_BOUND` |
| `risk_sizing_effect` | `NONE` | `NONE` |
| `order_intent_effect` | `NONE` | `NONE` |
| Non-authority assert | PASS | PASS (dispatcher → generic unbound) |
| `integrated_lane_bound` | — | `true` |
| Composition aligned | — | `true` |
| Fail reason | — | none (`integrated_scenario_composition_not_aligned` absent) |

No second scenario truth: helper reuses the identical CHOP_GUARD matrix evaluation
as `evaluate_surface_p_four_way_parity_v0`.
