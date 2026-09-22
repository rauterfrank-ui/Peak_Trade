---
docs_token: DOCS_TOKEN_P5_10_PRODUCTIVE_ACTIVATION_AND_BINDING_V1
status: active
scope: P5.10 productive layered-core bind into CURRENT productive cycle (Owner-GO)
---

# P5.10 Productive Activation and Binding v1

```text
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=true
P5_10_ACTIVATION_READINESS=READY
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=true
P5_AUTHORITY_CUTOVER_AUTHORIZED=false
PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED=false
EXTERNAL_EFFECT_AUTHORIZED=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
RUNTIME_AUTHORIZATION_EFFECT=NONE
B5_TEMPORAL_SEMANTICS=POST_CANONICAL_NEXT_SIDE_STATE
```

Owner-GO activation: binds adjudicated P5.10A/B contracts into the existing productive
`run_current_productive_master_v2_runtime_cycle_v1` path via a single seam (no parallel
decision writers). Per-cycle opt-in: `productive_layered_core_bind_requested` +
`layered_core_store_root`.

| Surface | Owner |
| --- | --- |
| Activation + bind seam | `ops.p5_10_productive_activation_and_binding_v1` |
| Bind enable constant | `ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1` |
| Productive cycle hook | `ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1` |
| B4 handoff | `ops.p5_10b_layered_epoch_remaining_authority_closure_v1` |
| P5 seam + seal | `ops.p5_productive_layered_core_authority_seam_v1` |
| CZ-4 delegation | `trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1` |

## Authority

- **Trading decision (entry/exit/composition):** unchanged integrated offline replay (naked MV2+DP).
- **Layered scope/R_t/d_t when bind requested:** P5 seal + CZ-4 skips legacy I-1..I-3 writers.
- **Canonical next SideState / StateSwitchEvidence:** P5.10B handoff only (`POST_CANONICAL_NEXT_SIDE_STATE`).

No `run_p5_layered_core_authority_seam_v1` in the cycle module; seam is invoked only inside the bind owner.

Code: `src/ops/p5_10_productive_activation_and_binding_v1/productive_cycle_bind_seam_v1.py`
