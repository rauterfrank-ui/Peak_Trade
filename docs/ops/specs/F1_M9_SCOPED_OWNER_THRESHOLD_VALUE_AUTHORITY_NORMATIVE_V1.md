---
docs_token: DOCS_TOKEN_F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_AUTHORITY_NORMATIVE_V1
status: active
scope: F1/M9 scoped Owner Threshold Value authority (Owner-ratified)
workpackage_id: F1_M9_THRESHOLD_VALUE_AUTHORITY_AND_HOT_PATH_ADMISSION_CLOSURE_V1
last_updated: 2026-09-24
---

# F1/M9 Scoped Owner Threshold Value Authority V1

```text
WORKPACKAGE_ID=F1_M9_THRESHOLD_VALUE_AUTHORITY_AND_HOT_PATH_ADMISSION_CLOSURE_V1
OWNER_THRESHOLD_POLICY=DEDICATED_DIGEST_SEALED_THRESHOLD_VALUE_AUTHORIZATION_RECORD_SEPARATE_FROM_F1_APPLY
RUNTIME_THRESHOLD_AUTHORITY_VALUE=F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_AUTHORITY_V1
CONCRETE_THRESHOLD_VALUE_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
NUMERIC_MAX_AGE_DECIDED=false
```

Decision: `config/governance/f1_m9_scoped_owner_threshold_value_authority_v1_decision_v1.json`

Owner policy: `config/governance/f1_m9_owner_threshold_value_policy_owner_adjudication_v1_decision_v1.json`

## Chain extension

```text
F1/M9 Owner Apply (runtime_applied)
  → F1/M9 Owner Threshold Value Authorization (dedicated record + ledgers)
  → ProductiveNumericMaxAgePolicyAdmissionV1
  → validate_policy_admission_request_v1
  → resolve_canonical_volatility_max_age_policy_for_evaluation_v1
  → Authorized Productive Parameter Seam → Presence Gate (non-enforcing)
```

Materialized configuration numeric **≠** Owner-ratified threshold value. Seam numeric alone **must not** produce `RATIFIED_NUMERIC`.

## Non-goals

- Choosing or defaulting a concrete seconds value in this WP
- Enforcement, Alpha blocking, trading/risk/selection authority change
- Global `NUMERIC_MAX_AGE_DECIDED=true` or `PRODUCTIVE_NUMERIC_VALUES_SET>0`
- Optimization/promotion/self-deploy/global join

## Verification

`tests/governance/test_f1_m9_scoped_owner_threshold_value_authority_v1.py`
