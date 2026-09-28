---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1
status: active
scope: One bounded Enter-order POST to eea.okx.com via envelope-bound single-use permit
capability: FULL_CORE_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1
last_updated: 2026-09-27
---

# Full Core Current Productive Actual Venue POST With Fresh Envelope Bound Single Use Permit V1

Derived spec. Non-SSOT. Consumes Owner-GO
`OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1`.

```text
BASELINE_ORIGIN_MAIN_SHA=cf3aa15f098827a9e60de8eb84e5bdd9eb54cca2
MAX_EXTERNAL_EFFECT_CARDINALITY=1
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
STANDING_POST_AUTHORITY_CREATED=false
AUTONOMY_CAN_POST=false
CONTINUOUS_RUN_AUTHORIZED=false
STEP_29Q_STATUS=PLAN_ONLY
```

Authority chain: durable POST Owner-GO consume → `evaluate_real_venue_post_admission_v1` →
one-shot join → durable `SENT_INITIATED` → K1 opaque signing →
`FullCoreProductiveHttpTradeOrderTransportV1` (host `eea.okx.com`, path `/api/v5/trade/order`).

Real execution is explicit via
`execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1`
(`perform_real_venue_post=true`). Unit tests use injected openers only.

Owner records:
`config/governance/current_productive_actual_venue_post_owner_go_v1_decision.json`,
`config/governance/current_productive_actual_venue_post_admission_v1_decision.json`.

K1 runtime binding (pre-live, no POST):
`docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_K1_RUNTIME_BINDING_TO_ONE_SHOT_ACTUAL_VENUE_POST_PRE_LIVE_BOUNDARY_V1.md`

Code:
`src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py`
