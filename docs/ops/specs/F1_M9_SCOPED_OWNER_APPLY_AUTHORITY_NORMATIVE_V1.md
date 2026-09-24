---
docs_token: DOCS_TOKEN_F1_M9_SCOPED_OWNER_APPLY_AUTHORITY_NORMATIVE_V1
status: active
scope: F1/M9 scoped Owner Productive Apply authority (Owner-ratified)
workpackage_id: F1_M9_SCOPED_OWNER_PRODUCTIVE_APPLY_AUTHORITY_V1
last_updated: 2026-09-24
---

# F1/M9 Scoped Owner Apply Authority V1

```text
WORKPACKAGE_ID=F1_M9_SCOPED_OWNER_PRODUCTIVE_APPLY_AUTHORITY_V1
OWNER_APPLY_POLICY=SCOPED_APPLY_WITH_DEDICATED_RECORD
RUNTIME_APPLY_AUTHORITY_VALUE=F1_M9_SCOPED_OWNER_APPLY_AUTHORITY_V1
EXTERNAL_EFFECT_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
```

Decision: `config/governance/f1_m9_scoped_owner_apply_authority_v1_decision_v1.json`

Owner policy ratification:
`config/governance/f1_m9_owner_apply_policy_owner_adjudication_v1_decision_v1.json`

Owners:

- `src/governance/f1_m9_scoped_owner_apply_authority_v1.py`
- `src/governance/f1_m9_owner_apply_authorization_record_v1.py`
- `src/governance/f1_m9_productive_apply_ledger_v1.py`

## Chain extension

```text
MATERIALIZED_GOVERNED_PRODUCTIVE_CONFIGURATION
  → F1/M9 Owner Apply Authorization (dedicated record + ledgers)
  → runtime_applied=true with runtime_apply_authority=F1_M9_SCOPED_OWNER_APPLY_AUTHORITY_V1
  → Authorized Productive Parameter Seam
  → Runtime transport → MV2 Double Play presence gate
```

Explicit Productive Authorization **does not** imply Productive Apply.

Threshold/Numeric Value Authorization remains **separate**; `runtime_applied=true`
does not ratify hot-path threshold effectiveness.

## Non-goals

- Global optimization join, promotion, self-deploy
- Optimization direct write
- Trading/Risk/Selection authority change
- External effect or enforcement
- `PRODUCTIVE_NUMERIC_VALUES_SET>0` or `NUMERIC_MAX_AGE_DECIDED=true`

## Verification

`tests/governance/test_f1_m9_scoped_owner_apply_authority_v1.py`
