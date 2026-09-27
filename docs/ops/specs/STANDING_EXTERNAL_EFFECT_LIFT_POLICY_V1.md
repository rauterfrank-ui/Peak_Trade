---
docs_token: DOCS_TOKEN_STANDING_EXTERNAL_EFFECT_LIFT_POLICY_V1
status: active
scope: Standing External Effect Lift — governed gate standing only
workpackage_id: STANDING_EXTERNAL_EFFECT_LIFT_POLICY_V1
last_updated: 2026-09-27
---

# Standing External Effect Lift Policy V1

```text
WORKPACKAGE_ID=STANDING_EXTERNAL_EFFECT_LIFT_POLICY_V1
BASELINE_ORIGIN_MAIN_SHA=2309dbd5b04a2fc2b41d88d9905d96671e51b1e3
LIFT_ENVELOPE=GOVERNED_STANDING_EXTERNAL_EFFECT_GATE_LIFT
GOVERNED_STANDING_EXTERNAL_EFFECT_AUTHORIZED=true (via parameterized gate)
IMPORT_TIME_EXTERNAL_EFFECT_AUTHORIZED=false
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
PERMIT_MINT_AUTHORIZED=false
```

Owner record:
`config/governance/standing_external_effect_lift_policy_v1_record.json`

Owner GO:
`config/governance/standing_external_effect_lift_owner_go_v1_decision.json`

## Semantic contract

| Layer | Meaning |
| --- | --- |
| Prerequisites | Valid EXTERNAL_EFFECT_AUTHORIZATION_POLICY_V1 record + Owner GO (#6894). |
| Lift admission | `evaluate_standing_external_effect_lift_admission_v1()` — gate evaluated with `standing_external_effect_authorized=True`. |
| Import-time constant | `EXTERNAL_EFFECT_AUTHORIZED` in Full-Core constants **remains false** (census / envelope fail-closed). |
| Envelope seam | Unchanged — permit-bound send; rejects standing-true default path. |

## Authority lattice

```text
STANDING_LIFT => GOVERNED_GATE_STANDING_TRUE (parameterized evaluate only)
STANDING_LIFT -/-> PERMIT_MINT / CREDENTIAL / POST / REAL_VENUE_POST / AUTONOMY_CAN_POST
EXTERNAL_EFFECT_AUTHORIZATION_POLICY => LIFT PREREQUISITE
```

## Next Owner boundary

**EXTERNAL_EFFECT_PERMIT_MINT_OWNER_GO** — distinct from standing lift.

Code: `src/governance/standing_external_effect_lift_policy_v1.py`  
Gate binding: `src/governance/standing_external_effect_lift_gate_binding_v1.py`
