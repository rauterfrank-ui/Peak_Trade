---
docs_token: DOCS_TOKEN_REGIME_SIDESTATE_MAPPING_PRODUCTIVE_AUTHORIZATION_V1
status: active
scope: Authorize existing P5.7 mapping for productive layered-bind regime switch ticks only
---

# Regime→SideState Mapping Productive Authorization v1

```text
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=true
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=true
P5_AUTHORITY_CUTOVER_AUTHORIZED=false
PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED=false
EXTERNAL_EFFECT_AUTHORIZED=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Owner-GO slice: flips the P5.2 standing authorization flag only. Uses the existing
`project_regime_to_sidestate_v1` contract (P5.7) and P5.10B `POST_CANONICAL_NEXT_SIDE_STATE`
handoff. Unblocks CZ-4 delegation on L10 regime-switch ticks and P5.10A activation mapping gate.

Does **not** enable default productive bind, cutover, wire POST, or new mapping semantics.

| Surface | Owner |
| --- | --- |
| Authorization constant | `ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.constants_v1` |
| Mapping semantics | `ops.p5_7_regime_sidestate_projection_mapping_contract_v1` |
| CZ-4 switch gate | `validate_cz4_delegation_authority_bind_v1` |
| Canonical SideState epoch | `ops.p5_10b_layered_epoch_remaining_authority_closure_v1` |
