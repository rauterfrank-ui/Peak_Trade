---
docs_token: DOCS_TOKEN_M9_VOLATILITY_NUMERIC_MAX_AGE_NUMERIC_PRODUCTIVE_TARGET_NORMATIVE_V1
status: active
scope: Owner-ratified M9 numeric productive target class only
workpackage_id: M10_M9_NUMERIC_PRODUCTIVE_TARGET_OWNER_RATIFICATION_V1
last_updated: 2026-09-19
---

# M9 — Numeric Productive Target V1

```text
OWNER_DECISION=NUMERIC_PRODUCTIVE_PARAMETER
PRODUCTIVE_TARGET_ID=peak_trade.governance.productive_target.m9_volatility_numeric_max_age_seconds/v1
OPTIMIZATION_SURFACE_ID=VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1
SOURCE_CANDIDATE_PARAMETER=max_age_seconds
TARGET_POLICY_PARAMETER=numeric_max_age_seconds
TARGET_UNIT=SECONDS
```

Machine-readable decision:
`config/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1.json`

Owner module:
`src/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1.py`

## Semantics

- **NUMERIC_PRODUCTIVE_PARAMETER** ratifies the *target class* and registry entry only.
- Target registration **does not** authorize productive apply, threshold value selection, or enforcement.
- Optimization candidate values, governance review admission, and evidence **do not** authorize policy mutation.
- Universe / surface membership **does not** imply productive target authorization.

## Consumer (CURRENT)

- Policy contract: `trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1`
- Productive path: `double_play_runtime_typed_volatility_presence_gate_v1` → `evaluate_canonical_volatility_estimate_age_policy_v1`

## Non-goals

- M10 explicit productive authorization
- Governed productive configuration materialization
- Candidate apply or optimizer value ratification
- Enforcement enablement
- Trading-core / Double Play semantic change
