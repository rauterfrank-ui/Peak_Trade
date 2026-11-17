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

The POST Owner-GO string names the capability. The direct runtime requires the
original pending-order observation before private preflight GETs and rechecks
it before consuming POST Owner-GO. The operator CLI offers the local
pre-live checklist. It refuses the historical submit flag before envelope
read or K1 access because it cannot supply the original account observer.

The consume record binds the string and repository baseline to the selected
store root. A separate permit binds the envelope digest and has its own
durable consume record. The transport rechecks the safety veto and the
original execution context before signing and before opening the socket.

The current POST Owner-GO verifier checks the consume record in the supplied
root. Admission requires a complete writer record with a JSON boolean
`consumed=true`, both retry flags false, a hexadecimal Git revision and a
valid UTC consume timestamp. An invalid record denies admission before durable
permit consumption, K1 access or HTTP. Its timestamp records the local
consume time. The record carries no authenticated per-order grant ID, expiry
or revocation check. The consume writer synchronizes the complete record,
publishes it atomically without replacing a record at the destination, and
synchronizes the directory entries before returning success. Concurrent
callers sharing that store root can consume the Owner-GO only once. A
published record also blocks a retry if a later synchronization step fails.
The envelope permit has a separate writer lock scoped to its own store.
Independent store roots have independent consume records. In an offline
probe at `678dea7a4`, the same Owner-GO and order envelope reached the fake
HTTP opener once in each of two roots. A fresh process retrying the first root
stopped with `CONSUMED_PERMIT` before the fake K1 backend or opener. A partial
record with the string `"false"` previously also reached the opener. The
regression check now rejects that record through the actual admission call.

An unattended mandate across store roots requires an independently verified
issuer and current grant, scoped to the account, execution environment and
exact order or explicitly authorized order set. Admission needs one atomic
consume decision against shared durable state, including revocation, that
survives process restart. The [original budget attempt](PORTFOLIO_OWNED_EXECUTION_IDENTITY_V2.md)
tracks decision and transport lineage in its own store. [FILEGATE](FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM_V1.md)
provides the safety veto. These owners retain their respective scope.

## Shared POST grant for ENTER and L10-Close

Both direct POST entry points accept an explicit signed grant and a trusted,
owner-provisioned store binding. The binding pins the local database and
independent checkpoint paths, store ID, issuer and Ed25519 public key
independently of the signed grant.
The grant binds its ID and validity window to the original account, OKX EEA,
execution environment, action and exact envelope digest. Grants and
revocations sign the store binding digest, including the canonical path and
the fresh generation created at provisioning. A fresh database cannot accept
an earlier grant even if the operator reuses its path, store ID and key. A
process restart keeps the original generation and consumption records.

One SQLite transaction checks the current grant and revocation state and
consumes the grant ID. The commit precedes the local Owner-GO witness, permit
consumption and K1 access. The local witness carries the claim digest, so
admission and transport require the same claim and attempt. An authenticated
revocation can block consumption or block the already consumed claim before
dispatch. The final transaction immediately before the socket marks the one
permitted dispatch. A process restart cannot obtain a new claim or send the
same grant again. A crash can leave a grant consumed with no socket attempt.
The original permit, Budget state and Reconciliation still record their own
facts. An ambiguous send stays subject to the original Reconciliation.

### POST authority restore

The owner provisions the checkpoint in a separate directory and retains it
outside the POST database's backup and restore scope. Every shared authority
operation compares the database generation binding and the digest of all
consumptions, dispatch starts and revocations to that checkpoint. A missing,
unreadable or mismatched checkpoint denies authority. A database restored from
a backup can reopen only when its state matches the retained checkpoint.
Previously consumed and revoked grants still deny on that state.

A mutation commits the checkpoint before the database. If the database commit
is interrupted after the checkpoint advances, the mismatch blocks both entry
points until the owner can restore the exact anchored state or explicitly
provision a new generation and checkpoint. Reprovisioning requires fresh
signatures for the new generation. Historical shared databases without an
independent checkpoint cannot acquire one through readback or restore.

For restore, stop the shared POST workers and install a consistent SQLite
snapshot at the bound database path. Preserve the current independent
checkpoint and verify the store binding before restarting the workers.
Rolling both files back together can recreate an indistinguishable pair.

The existing manually bounded V1 path and historical witness readers retain
their original contract. The shared path requires an explicitly provisioned,
authoritative database on the submitting host. The implementation adds no
standing issuer, host configuration or activation. The offline tests use
generated keys, temporary stores and injected transport.

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
