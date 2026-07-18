# Surface-P Smoke Composition Alignment v1

**Slice:** `fix/surface-p-smoke-composition-alignment-v1`  
**Base (post #5327 merge):** `660da90f03081b5f93e072c2da23b9cb0ea94e01`  
**Failure:** `test_surface_p_four_way_parity_smoke_assessment_v0` → `integrated_scenario_composition_not_aligned`  
**Mode:** test/harness fixture alignment only; offline; non-authorizing

## Summary

`evaluate_surface_p_four_way_parity_v0` always evaluates the scenario lane as
`SideState.CHOP_GUARD_BLOCK`. The smoke test previously passed an integrated
envelope from default `_run(price_path=(3500.0, 3600.0))`, which yields
`composition_status=long_selected`. Non-authority assert routing from PR #5327
already passed (`integrated_lane_bound=true`); alignment failed on composition.

Fix: `build_surface_p_four_way_smoke_integrated_envelope_v0` binds the integrated
smoke fixture to the same CHOP_GUARD scenario-matrix evaluation used by the
four-way harness (single composition truth).

## Safety

- `LIVE_AUTHORIZED=false`
- `ORDERS_ENABLED=false`
- No runtime / orders / live activation
- Generic `assert_non_authority_boundary_v0` unchanged
- CRS/Order-Intent envelope-effect dispatch from #5327 preserved
