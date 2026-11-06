# Audit Summary — ADVERSE_EXIT_DOWNSCOPE_SHADOWING_AUDIT_V1

## Verdict

**FAIL** — productive Shadowing/Value-Loss (class F) on the MV2 integrated research path:

1. Generator priority selects `ADVERSE_EXIT` over `DOWNSCOPE` whenever both match.
2. Research mark-relative distances preserve `adverse = 0.5 * up`, so any downscope hit also matches adverse.
3. Replay mapper `_canonical_scope_event_to_scope_event` drops `ADVERSE_EXIT_CANDIDATE` to `SCOPE_UNKNOWN`.
4. `transition_state` fail-closes on `SCOPE_UNKNOWN` → no SideState progress toward SHORT.
5. Adverse exit is **not** fully lost for exits: `derive_scope_adverse_exit_signal_v0` still feeds entry/exit policy.

## Counts

| Class | Count | Notes |
|-------|------:|-------|
| A Canonical Authority | 4 | generator select, transition_state, composition/entry-exit owners, quarantine constants |
| B Consumer/Projection | 4 | adverse signal derive/resolve, research distance helper, scope_direction projection |
| C Test/Fixture/Offline | 3 | LONG_ARMED seed, parity harness absolutes, generator fixtures adverse>up |
| D Legacy unreachable | 1 | runtime bridge absolute distances while BOUND_NOT_ACTIVATED |
| E Productive bypass / 2nd authority | 0 | none |
| F Shadowing / value-loss | 2 | adverse priority + SCOPE_UNKNOWN mapping |
| G Evidence-only | 1 | post-#5338 probe counts |

## Reachability

- `SHORT_EXIT_REACHABLE`: **true** via entry-exit `ADVERSE_SCOPE_EXIT` signal path.
- `DOWNSCOPE_REACHABLE` (SideState): **true** in fixtures with `adverse > up`; **effectively false** on research path with `adverse < up` (shadowed).
- `LONG_DEFAULT_FOUND`: **true** (pre-existing research `LONG_ARMED` seed).
- `SECOND_AUTHORITY_FOUND`: **false**.
- `CLASSIC_ENGINE_BYPASS_FOUND`: **false**.

## Non-findings

- No productive second Direction/Composition authority.
- No post-`transition_state` overwrite of SideState.
- Runtime bridge not activated; bridge absolute distances classified D.
- `entry_side=NONE` preserved (OPTION_D).

## Next fix workstream (not executed here)

`FIX_ADVERSE_EXIT_TO_SCOPE_EVENT_MAPPING_AND_DOWNSCOPE_PRIORITY_V1`

Minimal intent:
- Map `ADVERSE_EXIT_CANDIDATE` to an explicit SM-consumable event **or** keep it off the SM path without inventing `SCOPE_UNKNOWN` loss; and/or
- Ensure nested `adverse < up` cannot permanently suppress `DOWNSCOPE` transitions required for SHORT arming,
without creating a second Direction authority.
