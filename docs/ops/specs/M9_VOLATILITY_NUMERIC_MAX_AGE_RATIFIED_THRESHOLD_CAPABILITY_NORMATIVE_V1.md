---
docs_token: DOCS_TOKEN_M9_VOLATILITY_NUMERIC_MAX_AGE_RATIFIED_THRESHOLD_CAPABILITY_NORMATIVE_V1
status: active
scope: M9 ratified numeric threshold capability (semantic contract only)
workpackage_id: M10_M9_NUMERIC_PRODUCTIVE_TARGET_OWNER_RATIFICATION_V1
last_updated: 2026-09-19
---

# M9 — Ratified Numeric Max-Age Threshold Capability V1

```text
CAPABILITY_ID=M9_VOLATILITY_NUMERIC_MAX_AGE_RATIFIED_THRESHOLD_CAPABILITY_V1
CONCRETE_THRESHOLD_VALUE_RATIFIED=false
ENFORCEMENT_ENABLED=false
THRESHOLD_SELECTION_BY_CAPABILITY=false
```

Owner module:
`src/governance/m9_volatility_numeric_max_age_ratified_threshold_capability_v1.py`

## Allowed

- Typed representation of a **future** explicitly authorized `numeric_max_age_seconds`
- Unit: seconds; positive finite values in the M9 discrete domain
- Provenance / authorization digest fields (fail-closed validation)
- Explicit separation `UNRESOLVED_MAX_AGE` vs `RATIFIED_NUMERIC_THRESHOLD`

## Forbidden

- Selecting or defaulting a concrete threshold value
- Promoting M9 optimization candidates into productive policy
- Setting global `NUMERIC_MAX_AGE_DECIDED=true` without authorized value materialization
- Enabling enforcement in this capability
- Removing unresolved fallback behavior on the CURRENT hot path

## Distinctions

- Capability existence ≠ threshold value authorization
- Target registration ≠ productive apply authorization
- Review admission ≠ authorization
- Authorization (future M10) ≠ automatic apply
