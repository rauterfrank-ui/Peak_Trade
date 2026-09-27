---
docs_token: DOCS_TOKEN_CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_V1
status: active
scope: Checkout-independent credential access — governed policy admission
workpackage_id: CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_V1
last_updated: 2026-09-27
---

# Checkout-Independent Credential Access Policy V1

```text
WORKPACKAGE_ID=CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_V1
BASELINE_ORIGIN_MAIN_SHA=e92e5cb088f0e1dbdb83d37f40b9e90293cca127
ACCESS_ENVELOPE=GOVERNED_CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY
CREDENTIAL_ACCESS_POLICY_AUTHORIZED=true (lineage record + Owner GO)
CREDENTIAL_ACCESS_AUTHORIZED=true (policy admission only)
CREDENTIAL_ACCESS_PERFORMED=false
REAL_CREDENTIAL_ACCESS_PERFORMED=false
REAL_SECRET_LOAD_PERFORMED=false
CREDENTIAL_MATERIAL_LOADED=false
REAL_KEYCHAIN_ACCESS_AUTHORIZED=false (standing pins)
POST_ALLOWED=false
PERMIT_MINT_PERFORMED=false
```

Owner record:
`config/governance/checkout_independent_credential_access_policy_v1_record.json`

Owner GO:
`config/governance/checkout_independent_credential_access_owner_go_v1_decision.json`

## Semantic contract

| Layer | Meaning |
| --- | --- |
| Prerequisites | Valid EXTERNAL_EFFECT_PERMIT_MINT_POLICY_V1 (#6896) + governed permit mint. |
| Policy admission | `evaluate_checkout_independent_credential_access_admission_v1()` — no secret load. |
| Capability seam | `checkout_independent_credential_capability_v1` — offline contract; provider-ref only. |
| OS native acquisition | Module present; `REAL_KEYCHAIN_ACCESS_*` standing pins remain false. |

## Authority lattice

```text
PERMIT_MINT_POLICY => CREDENTIAL_ACCESS_POLICY PREREQUISITE
CREDENTIAL_ACCESS_POLICY => GOVERNED_CAPABILITY_ADMISSION (policy layer)
CREDENTIAL_ACCESS_POLICY -/-> REAL_SECRET_LOAD / REAL_KEYCHAIN / MATERIAL_LOADED / POST / PERMIT_MINT_PERFORMED
```

## Next Owner boundary

**REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_OWNER_GO** — distinct from policy admission.

Code: `src/governance/checkout_independent_credential_access_policy_v1.py`  
Gate binding: `src/governance/checkout_independent_credential_access_gate_binding_v1.py`
