---
docs_token: DOCS_TOKEN_P5_10B_LAYERED_EPOCH_REMAINING_AUTHORITY_CLOSURE_V1
status: active
scope: P5.10B B2+B3+B4 authority closure only (no productive bind)
---

# P5.10B Layered Epoch Remaining Authority Closure v1

```text
LAYERED_EPOCH_REMAINING_AUTHORITY_CLOSURE_V1_DEFINED=true
B1_CONTRACT_CLOSED=true
B2_CONTRACT_CLOSED=true
B3_CONTRACT_CLOSED=true
B4_CONTRACT_CLOSED=true
B5_TEMPORAL_SEMANTICS=POST_CANONICAL_NEXT_SIDE_STATE
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=true
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=false
FINAL_D_T_FORMULA_SELECTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_SEMANTICS_CHANGED=false
P5_10_ACTIVATION_READINESS=READY
```

Closes **B2**, **B3**, and **B4** left open by P5.10A. Validators, durable lifecycle codec, and
handoff materialization only — no productive wiring, no activation flags, no C4/Entry-Exit bind.

| Surface | Owner |
| --- | --- |
| B2+B4 closure orchestration | `ops.p5_10b_layered_epoch_remaining_authority_closure_v1` |
| P5.8B lifecycle persist/restore (B3) | `ops.p5_8b_regime_sidestate_projection_phase_authority_v1.persistence_v1` |
| Mechanical FSM (reference) | `ops.p5_9d_layered_mechanical_sidestate_fsm_contract_v1` |
| Epoch order (B1/B5) | `ops.p5_10a_layered_tick_merge_epoch_orchestration_contract_v1` |
| Scope-event producer (B2) | `trading.master_v2.deterministic_scope_event_generator_v1` |
| CZ-4 synthetic NOOP marker | `trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1` |

## B2 — Layered mechanical completion provenance

**CANONICAL_AUTHORITY:** MECH_T8–T14 completion requires
`MechanicalScopeEventProvenanceV1.LEGACY_DETERMINISTIC_SCOPE_EVENT_GENERATOR` from the
deterministic scope-event generator (`SCOPE_EVENT_GENERATOR_POLICY_VERSION` binding on evidence).

**ALREADY_ADJUDICATED:** `CZ4_SYNTHETIC_NOOP` (`p5_cz4_delegated_noop` matched condition) cannot
authorize completion or side change (P5.9D).

Chain (bind-prep): producer evidence → `classify_mechanical_scope_event_provenance_from_evidence_v1`
→ `validate_layered_mechanical_completion_provenance_chain_v1` → P5.9D FSM.

Unknown or unauthorized producer → fail-closed (`UNSPECIFIED` not normalized).

## B3 — P5.8B lifecycle durability

**Owner:** `persistence_v1` under P5.8B (single persist/restore owner).

- Versioned envelope + atomic JSON/manifest write (reuse pattern from layered episode store).
- No reconstruction from legacy host cursor fields; nested lifecycle uses existing P5.8B codec.
- Fail-closed on schema/version/instrument/`layered_episode_snapshot_id` binding mismatch.
- Restart parity: persist → restore under same `RegimeSidestateProjectionLifecyclePersistBindingV1`.

## B4 — Canonical SideState handoff

**CANONICAL_AUTHORITY:** `execute_layered_epoch_canonical_sidestate_handoff_v1` orders:

P5.8B phase → P5.7 projection → P5.9D mechanical validation (when requested) →
`canonical_next_side_state` → `StateSwitchEvidenceV1` materialization (same digest/id algorithm as
integrated replay; **not** reconstructed from legacy `transition_state`).

**Single writer:** at most one of regime-bound P5.7 write or mechanical FSM write per epoch;
parallel `legacy_transition_state` writer rejected when layered bind mode is active.

`P5_10_ACTIVATION_READINESS=READY` means a separate activation WP may start; this WP does not
enable bind or flip mapping authorization.

Code: `src/ops/p5_10b_layered_epoch_remaining_authority_closure_v1/contract_v1.py`
