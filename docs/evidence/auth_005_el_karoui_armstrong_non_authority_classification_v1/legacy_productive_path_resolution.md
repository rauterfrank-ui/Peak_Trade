# Legacy Productive Path Resolution (before=1 → after=0)

| Field | Value |
|---|---|
| File | `src/strategies/ecm.py` |
| Function | `generate_signals` / `calculate_ecm_phase` |
| Loader key | `ecm_cycle` (functional-only; no OOP `StrategySpec`) |
| Callers | `load_strategy("ecm_cycle")` offline/demo/scripts; not Master V2 imports |
| Reachability | Available via functional loader; not Spec-gated live-ready |
| Effect | Can emit ENTRY/EXIT events offline; **not** ratified side authority (OBL_B05 KEEP_NONE) |
| Relation | Armstrong/ECM CYCLE_INFORMATION family; parallel to OOP `armstrong_cycle` |
| Treatment | `LEAVE_UNCHANGED_WITH_EVIDENCE` + clarifying Non-Authority docstring |
| Reclassification | `LEGACY_FUNCTIONAL_NON_AUTHORITY_FAIL_CLOSED` (not productive MV2 authority) |

`LEGACY_PRODUCTIVE_COUNT_AFTER=0` (no remaining productive-authority legacy path in this scope).
