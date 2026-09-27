---
docs_token: DOCS_TOKEN_REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1
status: active
scope: Real Keychain / credential material load — governed ephemeral acquisition
workpackage_id: REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1
last_updated: 2026-09-27
---

# Real Keychain Access / Credential Material Load Policy V1

```text
WORKPACKAGE_ID=REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1
BASELINE_ORIGIN_MAIN_SHA=ce883bb52163db2a9cd29c5029c29215be2afd90
LOAD_ENVELOPE=GOVERNED_EPHEMERAL_KEYCHAIN_OPAQUE_MATERIAL_LOAD
REAL_KEYCHAIN_ACCESS_AUTHORIZED=true (policy/ephemeral path only)
STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED=false
CREDENTIAL_MATERIAL_LOAD_AUTHORIZED=true (policy admission)
REAL_CREDENTIAL_ACCESS_PERFORMED=false (until governed acquisition invoked)
SECRET_DISCLOSED=false
POST_ALLOWED=false
REQUEST_SIGNING_AUTHORIZED=false
```

Owner record:
`config/governance/real_keychain_access_or_credential_material_load_policy_v1_record.json`

Owner GO:
`config/governance/real_keychain_access_or_credential_material_load_owner_go_v1_decision.json`

## Semantic contract

| Layer | Meaning |
| --- | --- |
| Prerequisites | Valid CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_V1 (#6897). |
| Policy admission | `evaluate_real_keychain_access_or_credential_material_load_admission_v1()`. |
| Runtime acquisition | `attempt_governed_credential_material_acquisition_v1()` — ephemeral consumer + explicit backend; wipe on exit. |
| Standing pins | Module `REAL_KEYCHAIN_ACCESS_*` and `MATERIAL_LOADED_TRUE_REACHABLE` remain false. |

## Authority lattice

```text
CREDENTIAL_ACCESS_POLICY => MATERIAL_LOAD_POLICY PREREQUISITE
MATERIAL_LOAD_POLICY => EPHEMERAL_KEYCHAIN_ACQUISITION (in-memory opaque)
MATERIAL_LOAD_POLICY -/-> REQUEST_SIGNING / K1_PARSE / POST / PERMIT_MINT_PERFORMED
```

## Next Owner boundary

**OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1** — K1 UTF-8 parse + opaque signing handle (distinct from material-load policy).

Code: `src/governance/real_keychain_access_or_credential_material_load_policy_v1.py`  
Acquisition: `src/governance/real_keychain_access_governed_credential_material_acquisition_v1.py`
