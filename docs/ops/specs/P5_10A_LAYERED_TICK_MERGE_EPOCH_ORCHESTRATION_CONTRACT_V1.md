---
docs_token: DOCS_TOKEN_P5_10A_LAYERED_TICK_MERGE_EPOCH_ORCHESTRATION_CONTRACT_V1
status: active
scope: P5.10A layered trading epoch/tick merge orchestration contract only (no bind)
---

# P5.10A Layered Tick-Merge + Epoch Orchestration Contract v1

```text
LAYERED_TICK_MERGE_EPOCH_ORCHESTRATION_CONTRACT_V1_DEFINED=true
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=false
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=false
FINAL_D_T_FORMULA_SELECTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_SEMANTICS_CHANGED=false
P5_10_ACTIVATION_READY=false
```

Closes **B1** (layered tick merge orchestration authority) and the **minimal B5 temporal
boundary** required for that closure. Validators and epoch ordering only — no productive
wiring, no activation, no new trading algorithm.

| Surface | Owner |
| --- | --- |
| Epoch orchestration contract | `ops.p5_10a_layered_tick_merge_epoch_orchestration_contract_v1` |
| Layered seam + seal | `ops.p5_productive_layered_core_authority_seam_v1` |
| Phase / lifecycle (semantics) | `ops.p5_8b_regime_sidestate_projection_phase_authority_v1` |
| Regime-bound projection | `ops.p5_7_regime_sidestate_projection_mapping_contract_v1` |
| Mechanical FSM (validators) | `ops.p5_9d_layered_mechanical_sidestate_fsm_contract_v1` |
| CZ-4 delegation gate | `trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1` |
| Bind guards | `ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1` |

## External dependencies (not closed in this WP)

| ID | Status | Meaning |
| --- | --- | --- |
| B2 | `EXTERNAL_CLOSURE_REQUIRED` | Authorized ScopeEvent provenance for mechanical completion under layered mode |
| B3 | `EXTERNAL_CLOSURE_REQUIRED` | Persist/restore owner for P5.8B lifecycle alongside host carry-out |
| B4 | `EXTERNAL_CLOSURE_REQUIRED` | Productive bind from P5.7 + mechanical phase to `StateSwitchEvidenceV1` |

This contract **must not** invent B2/B3/B4 surfaces or imply activation when those remain open.

## Canonical layered trading epoch order (one tick)

Deterministic, fail-closed step order for a future `LAYERED_CORE_SEAL_DELEGATED` bind:

| Step | Phase | Primary owner |
| --- | --- | --- |
| 1 | Load prior persisted state | Host cursor + layered episode store (read) |
| 2 | Layered seam mechanical step + seal | `run_p5_layered_core_authority_seam_v1` |
| 3 | Lifecycle phase resolution | `resolve_regime_sidestate_projection_phase_v1` (P5.8B) |
| 4 | Regime-bound SideState projection | `project_regime_to_sidestate_v1` (P5.7) when epoch write is regime-bound |
| 5 | Mechanical SideState phase | P5.9D validators on mechanical transition attempt |
| 6 | Canonical `next_side_state` for epoch | Exactly one SideState writer (see below) |
| 7 | C4 + Entry/Exit consumption | Integrated replay consumers (bind-prep boundary only) |
| 8 | Durable carry-out | Host cursor + layered store (+ lifecycle when B3 closes) |

Naked MV2+Double-Play L1–L10 modules are unchanged; this contract **orders** existing artifacts only.

## State-field authority matrix (bind-prep)

| Field | Producer / writer | Pre value | Post value | Consumer (same epoch) | Next-cycle owner |
| --- | --- | --- | --- | --- | --- |
| `prior_side_state` | Host restore (occupancy/cursor); not core regime | persisted | unchanged until step 6 | P5.8B phase, P5.7 input, mechanical FSM prior | — |
| Layered episode + seal | P5 seam | prior episode | updated episode + `LayeredCoreAuthoritySealV1` | CZ-4 bind validator, P5.7 seal fields | `durable_state_v1` store |
| Lifecycle DTO | P5.8B (in-memory until B3) | parsed prior | `lifecycle_after` from phase resolution | P5.7 `phase` input | **B3 TBD** (not host cursor today) |
| `RegimeSideStateProjectionPhaseV1` | P5.8B resolution | n/a | resolved phase | P5.7 | — |
| Regime-bound projected SideState | P5.7 | `prior_side_state` | projected armed/pending/switch rows | Handoff to mechanical FSM prior | — |
| Mechanical transition | P5.9D-validated mechanical writer (future bind) | post-P5.7 prior | mechanical `next` | Feeds step 6 | — |
| `canonical_next_side_state` | **Single** regime-bound **or** mechanical writer | `prior_side_state` | epoch SideState outcome | C4 boundary, Entry/Exit direction, carry-out | Host cursor `side_state` |
| C4 composition inputs | C3 selected-lane artifacts | n/a | composition result | Entry/Exit policy | — |
| Entry/Exit direction | Entry/Exit policy evaluator | n/a | decision | downstream economics | — |

## Single-writer invariant

Per `trading_epoch`, at most **one** authorized SideState mutation writer may run:

- Regime-bound projection write (P5.7 epoch), **or**
- Mechanical FSM write (P5.9D-authorized row), **or**
- Hold (no mutation) when CZ-4 synthetic NOOP applies without a separate writer.

`transition_state` (**legacy** integrated replay SM) **must not** run in parallel as a second
SideState writer when layered bind mode is active (`P5.2` / `P5.9D` single-writer rules).

## B5 — C4 / Entry-Exit temporal semantics (adjudication)

**Legacy integrated replay** (`integrated_offline_trading_logic_replay_v1`) evaluates C4
**before** `transition_state`. That ordering is **NAVIGATION_ONLY** for layered mode and is
**not** layered epoch authority (`MV2_C4` chain documents legacy `Composition→State→Entry&#47;Exit`).

**P5.10A layered epoch authority (this contract):** step **6** (`canonical_next_side_state`)
precedes step **7** (C4 + Entry/Exit). Therefore:

```text
C4_ENTRY_EXIT_SIDESTATE_EPOCH=POST_CANONICAL_NEXT_SIDE_STATE
```

C4 and Entry/Exit **must** consume the SideState identity fixed at step 6 for the same
`trading_epoch`. Entry/Exit direction is derived from that same canonical value.

Bind-prep requests with `C4_ENTRY_EXIT_SIDESTATE_EPOCH=UNSPECIFIED` or attempts to run C4 on
a different SideState identity than step 6 → fail-closed.

## Activation

`P5_10_ACTIVATION_READY` remains false until B2, B3, B4 close **and** productive bind is
explicitly authorized. This WP does not flip `REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED`.

Code: `src/ops/p5_10a_layered_tick_merge_epoch_orchestration_contract_v1/contract_v1.py`
