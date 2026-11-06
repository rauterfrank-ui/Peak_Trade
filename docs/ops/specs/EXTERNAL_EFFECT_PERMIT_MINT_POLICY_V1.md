---
docs_token: DOCS_TOKEN_EXTERNAL_EFFECT_PERMIT_MINT_POLICY_V1
status: active
scope: External Effect Permit Mint — governed policy admission on standing lift
workpackage_id: EXTERNAL_EFFECT_PERMIT_MINT_POLICY_V1
last_updated: 2026-09-27
---

# External Effect Permit Mint Policy V1

```text
WORKPACKAGE_ID=EXTERNAL_EFFECT_PERMIT_MINT_POLICY_V1
BASELINE_ORIGIN_MAIN_SHA=03727c3cd09504beeedf4839b40dab3a26234331
MINT_ENVELOPE=GOVERNED_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_PERMIT_MINT
PERMIT_POLICY_AUTHORIZED=true (via lineage-bound record + Owner GO)
PERMIT_MINT_AUTHORIZED=true (policy admission only)
PERMIT_MINT_PERFORMED=false
CREDENTIAL_ACCESS_AUTHORIZED=false
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
AUTONOMY_CAN_MINT_PERMIT=false
```

Owner record:
`config/governance/external_effect_permit_mint_policy_v1_record.json`

Owner GO:
`config/governance/external_effect_permit_mint_owner_go_v1_decision.json`

## Semantic contract

| Layer | Meaning |
| --- | --- |
| Prerequisites | Valid STANDING_EXTERNAL_EFFECT_LIFT_POLICY_V1 (#6895) + governed standing. |
| Policy admission | `evaluate_external_effect_permit_mint_admission_v1()` — fail-closed; no runtime mint. |
| Permit producer | `external_effect_permit_v1.issue_external_effect_permit_v1` remains gated by import-time LIVE predicates. |
| Binding | `evaluate_permit_mint_bound_external_effect_permit_seam_v1()` — digest lineage only. |

## Authority lattice

```text
STANDING_LIFT => PERMIT_MINT_POLICY PREREQUISITE
PERMIT_MINT_POLICY => GOVERNED_PERMIT_MINT_ADMISSION (policy layer)
PERMIT_MINT_POLICY -/-> PERMIT_MINT_PERFORMED / CREDENTIAL / POST / REAL_VENUE_POST / AUTONOMY_CAN_MINT_PERMIT
```

## Next Owner boundary (superseded by credential-access WP)

Credential access policy admission: `CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_V1`.
Next seam: **REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_OWNER_GO**.

Code: `src/governance/external_effect_permit_mint_policy_v1.py`  
Gate binding: `src/governance/external_effect_permit_mint_gate_binding_v1.py`
