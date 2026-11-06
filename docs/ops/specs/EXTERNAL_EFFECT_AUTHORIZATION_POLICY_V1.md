---
docs_token: DOCS_TOKEN_EXTERNAL_EFFECT_AUTHORIZATION_POLICY_V1
status: active
scope: External Effect authorization policy — PRE_EXTERNAL to standing gate seam only
workpackage_id: EXTERNAL_EFFECT_AUTHORIZATION_POLICY_V1
last_updated: 2026-09-27
---

# External Effect Authorization Policy V1

```text
WORKPACKAGE_ID=EXTERNAL_EFFECT_AUTHORIZATION_POLICY_V1
BASELINE_ORIGIN_MAIN_SHA=b5e0fd94bbf7ba5f1742c98086e548d450ab4d2b
AUTHORIZATION_ENVELOPE=PRE_EXTERNAL_TO_STANDING_EXTERNAL_EFFECT_GATE_POLICY
STANDING_EXTERNAL_EFFECT_AUTHORIZED=false
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
PERMIT_MINT_AUTHORIZED=false
CREDENTIAL_ACCESS_PERFORMED=false
```

Owner record:
`config/governance/external_effect_authorization_policy_v1_record.json`

Owner GO:
`config/governance/external_effect_authorization_policy_owner_go_v1_decision.json`

Closeout decision:
`config/governance/external_effect_authorization_policy_v1_decision_v1.json`

## Semantic contract

| Layer | Meaning |
| --- | --- |
| Policy authorization | Singular owner `governance.external_effect_authorization_policy_v1`; lineage-bound record + Owner GO. |
| Prerequisites | Valid Productive Activation + Continuous Run policies; forensic review #6893; PRE_EXTERNAL static proof. |
| Runtime admission | `evaluate_external_effect_policy_admission_v1()` — fail-closed; re-proves PRE_EXTERNAL census + standing gate. |
| Gate binding | `evaluate_policy_bound_external_effect_gate_v1()` — policy digest + `evaluate_external_effect_v1()` decision. |
| Standing flags | **Not lifted** (`EXTERNAL_EFFECT_AUTHORIZED=false` in Full-Core constants). |

## Authority lattice (preserved)

```text
PRE_EXTERNAL_REACHABILITY -/-> STANDING_EXTERNAL_EFFECT_AUTHORIZED
EXTERNAL_EFFECT_POLICY -/-> PERMIT_MINT_AUTHORIZED
EXTERNAL_EFFECT_POLICY -/-> CREDENTIAL_ACCESS_PERFORMED
EXTERNAL_EFFECT_POLICY -/-> POST_ALLOWED / REAL_VENUE_POST_ALLOWED
EXTERNAL_EFFECT_POLICY -/-> AUTONOMY_CAN_MINT_PERMIT / AUTONOMY_CAN_POST
PRODUCTIVE_ACTIVATION + CONTINUOUS_RUN => POLICY PREREQUISITE ONLY
```

## Next Owner boundary

First authority required to lift standing `EXTERNAL_EFFECT_AUTHORIZED` or mint permits:
**scoped EXTERNAL_EFFECT standing-lift Owner-GO** (distinct from this policy WP).

Code: `src/governance/external_effect_authorization_policy_v1.py`  
Gate binding: `src/governance/external_effect_authorization_policy_gate_binding_v1.py`
