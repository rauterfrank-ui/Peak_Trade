# Root Cause

## Symptom

```
test_surface_p_four_way_parity_smoke_assessment_v0
assert assessment.integrated_scenario_composition_aligned is True
fail_closed_reasons=('integrated_scenario_composition_not_aligned',)
```

## Not the cause

- Not a Non-Authority assert failure after PR #5327.
- `assert_surface_p_integrated_envelope_non_authority_boundary_v0` PASSES on the
  previous long_selected integrated envelope.
- `integrated_lane_bound` was already `true` once the CRS-aware dispatch was in place.

## Cause

Composition lane mismatch:

| Lane | Source | composition_status |
|------|--------|--------------------|
| Scenario (harness) | `evaluate_scenario_matrix_for_side_state_v0(CHOP_GUARD_BLOCK)` | `chop_guard_block` |
| Integrated (smoke before) | `_run(price_path=(3500.0, 3600.0))` | `long_selected` |

Alignment predicate in harness:

```python
integrated_envelope.composition_status == scenario_env.composition_status
```

Documented elsewhere (`test_3_both_confirmed_chop_guard_parity_v0`): integrated
default path does not emit Scope-CHOP and is not required to mirror the conflict
fixture. Smoke therefore must bind its integrated fixture to the harness CHOP_GUARD
lane explicitly rather than using a default long entry replay.
