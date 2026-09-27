---
docs_token: DOCS_TOKEN_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1
status: active
scope: K1 opaque signing handle, request signing, PRE-POST envelope — no venue POST
workpackage_id: CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1
last_updated: 2026-09-27
---

# Current Productive K1 Real Keychain Access and Opaque Signing Handle PRE-POST V1

```text
WORKPACKAGE_ID=CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1
BASELINE_ORIGIN_MAIN_SHA=4e31703f888fec81cca97f51376429088e022f3d
PRE_POST_ENVELOPE=GOVERNED_K1_OPAQUE_SIGNING_REQUEST_SIGNING_PRE_POST
REAL_KEYCHAIN_ACCESS_AUTHORIZED=true (Owner-GO ephemeral K1 path only)
STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED=false
REQUEST_SIGNING_AUTHORIZED=true (policy admission)
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
SECRET_DISCLOSED=false
```

Owner record:
`config/governance/current_productive_k1_opaque_signing_handle_pre_post_policy_v1_record.json`

Owner GO:
`config/governance/current_productive_k1_opaque_signing_handle_pre_post_owner_go_v1_decision.json`

## Semantic contract

| Layer | Meaning |
| --- | --- |
| Prerequisites | Valid REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1 (#6898). |
| Policy admission | `evaluate_current_productive_k1_opaque_signing_handle_pre_post_admission_v1()`. |
| Opaque handle | `attempt_governed_k1_opaque_signing_handle_construction_v1()` — ephemeral Keychain → parse → bind; wipe on exit. |
| Request signing | OKX venue auth headers via opaque handle; no secret export. |
| PRE-POST envelope | `build_and_validate_current_productive_k1_pre_post_request_envelope_v1()`. |
| POST admission | `evaluate_real_venue_post_admission_v1()` — fail-closed without actual-POST Owner-GO. |

## Authority lattice

```text
MATERIAL_LOAD_POLICY => K1_PRE_POST_POLICY PREREQUISITE
K1_PRE_POST_POLICY => OPAQUE_SIGNING_HANDLE + REQUEST_SIGNING + PRE_POST_ENVELOPE
K1_PRE_POST_POLICY -/-> POST_ADMISSION / REAL_VENUE_POST / PERMIT_CONSUME_SEND
```

## Next Owner boundary

**OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1** — real venue POST with fresh envelope-bound single-use permit.

Runtime binding (pre-live only, no POST):  
`docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_K1_RUNTIME_BINDING_TO_ONE_SHOT_ACTUAL_VENUE_POST_PRE_LIVE_BOUNDARY_V1.md`

Code: `src/governance/current_productive_k1_opaque_signing_handle_pre_post_policy_v1.py`  
Construction: `src/governance/k1_opaque_signing_handle_governed_construction_v1.py`  
PRE-POST: `src/governance/current_productive_k1_pre_post_request_envelope_v1.py`  
Runtime join: `src/ops/full_core_live_path_composition_root_v1/current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1.py`
