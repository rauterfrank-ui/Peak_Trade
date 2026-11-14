---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1
status: active
scope: One bounded Enter-order POST to eea.okx.com via envelope-bound single-use permit
capability: FULL_CORE_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1
last_updated: 2026-11-14
---

# Full Core Current Productive Actual Venue POST With Fresh Envelope Bound Single Use Permit V1

Derived spec. Non-SSOT. Consumes Owner-GO
`OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1`.

```text
BASELINE_ORIGIN_MAIN_SHA=fca07afa1fa74a94cdecde3876c9c30ad79ba828
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

## Scope of the current controls

The POST Owner-GO string names the capability. The operator CLI supplies that
string after explicit confirmation. The consume record binds the string and
repository baseline to the selected store root. A separate permit binds the
envelope digest and has its own durable consume record. The transport rechecks
the safety veto and the original execution context before signing and before
opening the socket.

The current POST Owner-GO verifier checks the consume record in the supplied
root. Its record carries no authenticated per-order grant ID, expiry or
revocation check. The consume writer synchronizes the complete record,
publishes it atomically without replacing a record at the destination, and
synchronizes the directory entries before returning success. Concurrent
callers sharing that store root can consume the Owner-GO only once. A
published record also blocks a retry if a later synchronization step fails.
The envelope permit has a separate writer lock scoped to its own store.
Independent store roots have independent consume records. A mandate for
unattended operation across store roots would require an independently
verified grant and a shared consumption boundary.

A denied PRE_EXTERNAL policy proof blocks its policy admission. The explicit
submit join calls the POST admission evaluator with a single-use permit for
the same Owner-GO. That evaluator checks the durable Owner-GO consume record
and reports `REAL_VENUE_POST_ADMISSION_GRANTED_ONE_SHOT` on success. The join
requires that status, a true `post_admission_granted`, and an empty list of
denial reasons before permit consumption or signing. The forensics report
preserves the admission decision and its reasons. The transport result
records whether a send was attempted.

Owner records:
`config/governance/current_productive_actual_venue_post_owner_go_v1_decision.json`,
`config/governance/current_productive_actual_venue_post_admission_v1_decision.json`.

K1 runtime binding (pre-live, no POST):
`docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_K1_RUNTIME_BINDING_TO_ONE_SHOT_ACTUAL_VENUE_POST_PRE_LIVE_BOUNDARY_V1.md`

Code:
`src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py`
