---
docs_token: DOCS_TOKEN_COMPANION_C2_FRACTION_TO_UNITS_RUNTIME_COMPLETION_V1
status: active
scope: Companion C2 Fraction→Units runtime completion scaffold (fail-closed; no shadow/live binding)
workpackage_id: COMPANION_C2_FRACTION_TO_UNITS_RUNTIME_COMPLETION_V1
last_updated: 2026-09-27
---

# Companion C2 Fraction→Units Runtime Completion V1

```text
WORKPACKAGE_ID=COMPANION_C2_FRACTION_TO_UNITS_RUNTIME_COMPLETION_V1
DEPENDENCY_CLOSURE_OWNER_GO=OWNER_GO_C2_COMPANION_CONVERSION_DEPENDENCY_CLOSURE_V1
DEPENDENCY_CLOSURE_OWNER_GO_STATUS=CONSUMED
CONVERSION_READY=true
COMPANION_RUNTIME_CONVERSION_ENABLED=false
RUNTIME_CONVERSION_IMPLEMENTED=false
SHADOW_SESSION_BINDING_PRESENT=false
LIVE_SESSION_BINDING_PRESENT=false
NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false
C2_AUTHORITY_ADDED=false
EXTERNAL_EFFECT_AUTHORIZED=false
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
```

Mechanical continuation after
[`RISK_SIZING_C2_COMPANION_CONVERSION_DEPENDENCY_CLOSURE_V1.md`](../../governance/RISK_SIZING_C2_COMPANION_CONVERSION_DEPENDENCY_CLOSURE_V1.md).
Adds a **fail-closed runtime conversion module** that reuses the existing read-binding
and algebra owners. Does **not** mutate `shadow_session.py`, `live_session.py`, or
`ExecutionPipeline.signal_to_orders`.

Decision:
`config/governance/companion_c2_fraction_to_units_runtime_completion_v1_decision_v1.json`

Runtime module:
`src/ops/companion_shadow_live_fraction_to_units_input_binding_v1/runtime_conversion_v1.py`

## Passthrough default (CURRENT)

While `COMPANION_RUNTIME_CONVERSION_ENABLED=false`, companion paths keep passing
`position_fraction` through to `signal_to_orders` unchanged (legacy pass-through).

## Conversion path (not activated)

When a future scoped Owner-GO sets `COMPANION_RUNTIME_CONVERSION_ENABLED=true` **and**
`NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=true`, the runtime module may convert a
governed producer bundle to lot-floored quantity base units via the existing algebra.
That activation is **not** part of this workpackage.

## Next genuine blocker

Scoped Owner-GO for **shadow/live producer binding** (`SHADOW_BINDING_REQUIRES_SEPARATE_GO`,
`LIVE_BINDING_REQUIRES_SEPARATE_GO`, `FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO` per
[`RISK_SIZING_GOVERNED_PRODUCER_OBSERVATION_ADAPTER_CONTRACT_V1.md`](../../governance/RISK_SIZING_GOVERNED_PRODUCER_OBSERVATION_ADAPTER_CONTRACT_V1.md)).
