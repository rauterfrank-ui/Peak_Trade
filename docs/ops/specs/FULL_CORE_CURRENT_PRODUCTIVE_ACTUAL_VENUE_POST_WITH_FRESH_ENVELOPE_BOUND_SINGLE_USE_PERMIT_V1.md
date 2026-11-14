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
revocation check. The consume writer uses a file replacement and has no
common lock across its read and write. The envelope permit has a separate
writer lock scoped to its own store. The single-attempt checks therefore
provide evidence for the bound store and transport attempt. A mandate for
unattended operation across processes, store roots and restarts would require
an independently verified grant and a shared consumption boundary.

The governance policy evaluators and this explicit submit path are separate.
A denied PRE_EXTERNAL policy proof blocks that policy admission. The explicit
submit path evaluates its own POST admission and transport checks.
The submit join reads `post_admission_granted` from that evaluation. The
current evaluator can return a granted boolean with a denial status string.
That contradiction leaves the status string unreliable as an audit signal.
The transport result records whether a send was attempted.

Owner records:
`config/governance/current_productive_actual_venue_post_owner_go_v1_decision.json`,
`config/governance/current_productive_actual_venue_post_admission_v1_decision.json`.

K1 runtime binding (pre-live, no POST):
`docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_K1_RUNTIME_BINDING_TO_ONE_SHOT_ACTUAL_VENUE_POST_PRE_LIVE_BOUNDARY_V1.md`

Code:
`src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py`
