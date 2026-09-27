---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_K1_RUNTIME_BINDING_TO_ONE_SHOT_ACTUAL_VENUE_POST_PRE_LIVE_BOUNDARY_V1
status: active
scope: K1 PRE-POST runtime binding to one-shot Enter POST pre-live boundary; no venue POST
capability: FULL_CORE_CURRENT_PRODUCTIVE_K1_RUNTIME_BINDING_TO_ONE_SHOT_ACTUAL_VENUE_POST_PRE_LIVE_BOUNDARY_V1
last_updated: 2026-09-27
---

# Full Core Current Productive K1 Runtime Binding To One Shot Actual Venue Post Pre Live Boundary V1

Derived spec. Non-SSOT. Co-presents two distinct Owner-GO literals:

- `OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1`
- `OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1`

```text
BASELINE_ORIGIN_MAIN_SHA=c93ea739848963b0c971161d44538be19292317c
K1_OWNER_GO_DURABLE_CONSUMED=false
POST_OWNER_GO_DURABLE_CONSUMED=false
PRE_LIVE_PROOF_ONLY=true
REAL_VENUE_POST_ATTEMPTED=false
PERMIT_CONSUMED_DURABLE=false
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED=false
```

Authority chain: K1 productive PRE-POST chain (ephemeral Keychain → signing → PRE-POST envelope)
→ `prove_pre_live_actual_venue_post_readiness_v1` (POST Owner-GO literal check only; no durable consume)
→ stop before `execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1`.

Runtime ops:

- `scripts/ops/run_current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1.py`
- `scripts/ops/run_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py`
  (`--pre-live-only` + optional `--k1-backend macos`)

Code:
`src/ops/full_core_live_path_composition_root_v1/current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1.py`
