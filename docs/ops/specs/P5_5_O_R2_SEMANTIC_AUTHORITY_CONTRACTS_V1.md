---
docs_token: DOCS_TOKEN_P5_5_O_R2_SEMANTIC_AUTHORITY_CONTRACTS_V1
status: active
scope: P5.5 O-R2 semantic authority contracts only (no cutover; no productive bind)
---

# P5.5 O-R2 Semantic Authority Contracts v1

```text
SIDESTATE_CUTOVER_MODEL=O-R2
L1_L10_BULL_BEAR_DECISION_AUTHORITY=SOLE
SIDESTATE_AS_COMPETING_BULL_BEAR_AUTHORITY=FORBIDDEN_IN_LAYERED_MODE
SIDESTATE_DOWNSTREAM_PROJECTION_LIFECYCLE_OCCUPANCY_ROLE=PRESERVED
VENUE_POSITION_OCCUPANCY_TRUTH=PRESERVED
BULL_TO_LONG_ACTIVE_IMPLICIT_MAPPING=FORBIDDEN
BEAR_TO_SHORT_ACTIVE_IMPLICIT_MAPPING=FORBIDDEN
LEGACY_TRANSITION_STATE_AUTHORITY=PRESERVED_UNTIL_EXPLICIT_CUTOVER
D_T_FORMULA_SELECTED=false
MISSING_AUTHORIZED_D_T=FAIL_CLOSED
PRODUCTIVE_BIND_ENABLE=false
AUTHORITY_CUTOVER=false
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=false
P5_AUTHORITY_CUTOVER_AUTHORIZED=false
PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED=false
P4_PRODUCTIVE_BINDING=false
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=false
FINAL_D_T_FORMULA_SELECTED=false
NUMERIC_FORMULA_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_GEOMETRY_CHANGED=false
PRODUCTIVE_DECISION_PATH_CHANGED=false
```

Owner architecture decision **O-R2**: in future **layered** cutover mode, L1–L10 is the sole
Bull/Bear **trading decision** authority. `SideState` remains a subordinated downstream surface
(lifecycle, occupancy, confirmation, recovery, projection). This WP does **not** activate cutover,
bind, or seam invoke.

| Surface | Owner |
| --- | --- |
| O-R2 contracts + guards | `ops.p5_5_o_r2_semantic_authority_contracts_v1` |
| Bind prep (unchanged) | `ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1` |
| CURRENT productive cycle | `ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1` |

## Authority modes

### LEGACY (CURRENT productive default)

- `trading.master_v2.double_play_state.transition_state` remains canonical SideState/Switch writer.
- No change to integrated replay ordering or semantics.

### LAYERED (future, explicitly authorized only)

- L1–L10 (+ valid seal / CZ-4 delegation) = sole Bull/Bear decision authority.
- Competing SideState Bull/Bear **decision** writers forbidden.
- SideState may be produced only via authorized **projection** from core + occupancy/confirmation
  evidence — projection mechanism is **not** defined in this WP; missing authorized projection
  ⇒ fail-closed.

## Host-seed boundary

```text
Venue truth → observation / occupancy / reconciliation (never L4/L10 regime writer)
Cursor → recovery evidence (never core regime writer)
L1–L10 episode / seal → trading decision authority
```

- No legacy→core fallback on missing core state.
- Occupancy may gate entry/exit/risk/execution downstream; it must not overwrite core Bull/Bear.

## SideState projection boundary

- Projection may **read** core regime and occupancy/confirmation as needed.
- Projection must **not** write core state (no backflow).
- `ACTIVE` must not arise from `NakedRegimeV1` alone.
- No total Regime↔SideState bijection; no implicit `BULL→LONG_ACTIVE` or `BEAR→SHORT_ACTIVE`.
- No mapping table in this WP.

## D_t authority gate

- Legacy `CANONICAL_*_DISTANCE` config is not D_t authority in layered mode.
- `ExplicitDtProposalV1` remains proposal/transport only (`NUMERIC_FORMULA_AUTHORITY=NONE`).
- Missing authorized `proposed_d_t` ⇒ no valid layered seal / cutover path (fail-closed).

## R-01 / R-02 / R-03 closure

| ID | Encoding |
| --- | --- |
| R-01 | O-R2 boundary + projection-not-implemented ⇒ fail-closed |
| R-02 | Valid layered seal forbids parallel legacy scope/CM writers |
| R-03 | Full-Core CURRENT first consumer = `run_current_productive_master_v2_runtime_cycle_v1`; wallclock `decision_economics_cycle_bridge_v1` is not second Full-Core authority |

Code: `src/ops/p5_5_o_r2_semantic_authority_contracts_v1/contract_v1.py`
