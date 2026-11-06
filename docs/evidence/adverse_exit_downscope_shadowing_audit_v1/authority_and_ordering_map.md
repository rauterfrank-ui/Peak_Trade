# Authority and Ordering Map

## Canonical owners (unchanged)

| Role | Owner |
|------|-------|
| Direction / Switch | `trading.master_v2.double_play_state.transition_state` |
| Composition | `trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1` |
| Scope event evidence | `trading.master_v2.deterministic_scope_event_generator_v1.generate_deterministic_scope_event` |
| Entry/Exit policy | `trading.master_v2.double_play_entry_exit_policy_v0` |
| Research distance binding | `src.backtest.mv2_research_wiring_v1.compute_mv2_research_scope_distances_absolute_from_mark_v1` (inputs only) |

## Productive integrated bar ordering

```text
update_dynamic_boundaries (pre)
  -> generate_deterministic_scope_event
  -> _canonical_scope_event_to_scope_event   *** VALUE-LOSS BOUNDARY for ADVERSE_EXIT ***
  -> DA / survival / suitability (bull+bear)
  -> evaluate_double_play_composition_matrix_v1
  -> transition_state(mapped_event)
  -> update_dynamic_boundaries (post)
  -> derive_scope_adverse_exit_signal_v0     *** exit signal preserved on parallel path ***
  -> evaluate_double_play_entry_exit_policy_v0
```

No later adapter overwrites `next_side_state` after `transition_state`.

## Shadowing chain (research path, adverse < up)

```text
price <= downscope_threshold
  => matched includes DOWNSCOPE and ADVERSE_EXIT
  => _select_directional_kind prefers ADVERSE_EXIT
  => event_type = adverse_exit_candidate
  => mapped_event = SCOPE_UNKNOWN
  => transition_state FAIL_CLOSED (SideState frozen)
  => PolicySignal adverse_exit may still trigger entry/exit exit class
  => DOWNSCOPE_* never reaches SideState machine
```

## Second authority

None found for Direction/Switch/Composition. Runtime bridge remains `BOUND_NOT_ACTIVATED`.
