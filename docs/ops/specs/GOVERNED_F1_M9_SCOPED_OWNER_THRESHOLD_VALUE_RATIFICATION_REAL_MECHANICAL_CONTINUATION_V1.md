---
docs_token: DOCS_TOKEN_GOVERNED_F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_RATIFICATION_REAL_MECHANICAL_CONTINUATION_V1
status: active
scope: F1/M9 Owner threshold value ratification (600 SECONDS; no activation)
workpackage_id: GOVERNED_F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_RATIFICATION_REAL_MECHANICAL_CONTINUATION_V1
last_updated: 2026-09-27
---

# Governed F1/M9 Scoped Owner Threshold Value Ratification Real Mechanical Continuation V1

```text
WORKPACKAGE_ID=GOVERNED_F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_RATIFICATION_REAL_MECHANICAL_CONTINUATION_V1
OWNER_THRESHOLD_VALUE_RATIFICATION_AUTHORIZED=true
RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS=600
THRESHOLD_HOT_PATH_RATIFIED=true
REAL_P4_TO_F1_M9_JOIN_NOT_CANONICAL=true
PRODUCTIVE_ACTIVATION_AUTHORIZED=false
EXTERNAL_EFFECT=false
```

Owner WP:
`config/governance/governed_f1_m9_scoped_owner_threshold_value_ratification_wp_v1_owner_decision_v1.json`

Decision:
`config/governance/governed_f1_m9_scoped_owner_threshold_value_ratification_real_mechanical_continuation_v1_decision_v1.json`

## Chain

```text
POST-REAL-CAMPAIGN durable evidence (600s candidate)
  → governed productive configuration (600s numeric)
  → Owner Apply record + runtime_applied
  → digest-sealed Owner Threshold Value Authorization record (600 SECONDS)
  → f1_m9_scoped_owner_threshold_value_authority_v1 adjudication + ledger
  → scoped_owner_threshold_value_authorized on configuration
  → authorized productive parameter seam (RATIFIED_NUMERIC; non-enforcing)
  → STOP before Productive Activation
```

## State distinctions preserved

- **VALUE_ADMISSIBLE** — discrete domain `[60…7200]`
- **VALUE_SELECTED** — campaign proposal `CANDIDATE_600_S` (≠ ratification)
- **VALUE_OWNER_RATIFIED** — Owner GO 600 SECONDS + sealed threshold record
- **CONFIGURATION_RUNTIME_APPLIED** — separate Apply chain (required predecessor)
- **PRODUCTIVE_ACTIVATION** — not authorized

## Non-implications

- No Real-P4 ↔ F1/M9 join
- No venue POST / wire send / credentials
- No global `NUMERIC_MAX_AGE_DECIDED=true` or enforcement activation

## Verification

- `tests/governance/test_governed_f1_m9_scoped_owner_threshold_value_ratification_real_mechanical_continuation_v1.py`
- `tests/governance/test_f1_m9_scoped_owner_threshold_value_authority_v1.py`
