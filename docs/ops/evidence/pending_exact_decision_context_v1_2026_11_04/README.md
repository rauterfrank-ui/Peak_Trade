# Exact normal decision context for Pending — 2026-11-04

Source revision: 5161a5c86. Observation transport only; no trading authority.

## Existing construction and implementation

The normal adapter already supplies the canonical mark to S7/MV2. The replay's
intermediate object contains both the consumed CanonicalMarketContextV1 and the
EntryExitPolicyDecisionV0. The existing T2 dispatcher retains last_invocation
per dispatcher, already consumed by the N1 join. DDO capture constructs its cycle
identity from the same runtime cycle_id and outgoing cursor now_tick. Its existing
projection serializes the full producer decision, including policy identity,
instrument, trading epoch, input digest and exact ENTER semantics.

## Change and consumer effect

A frozen observation DTO copies the consumed market price, existing decision_time,
market context reference, instrument/native identity, exact canonical DP payload
and DDO cycle identity. The normal S5 runner returns it from last_invocation; S6
preserves it per cycle. Reporting with this context requires exactly one matching
cycle AND full canonical producer payload. No ordinal/epoch fallback is permitted
for an available context. The normal launcher uses the correlated context after
instrument/native checks and no longer reads optional ENTER traces for this fact.
Absent context leaves zero inputs and the existing explicit creation rejection.
Legacy context-free reporting callers retain their old reporting behavior.

Decision timestamp is the consumed CMC decision_time, not the earlier C1 event
or the mark receipt/event clock. The adapter currently derives that time from C1+1;
this change transports its actual semantics and does not certify source freshness.

## Verification and limits

83 transport/reporting/orchestration cases: 79 PASS, 4 failures. Two existing Atlas
pin checks lack their S5/S6 seam strings in the baseline catalog; a historical
report is absent; one old bootstrap test supplies insufficient finalized history.
The latter error is reproduced by executing the original baseline convergence
module with that test in a temporary root. No synthetic historical report or
fictitious runtime Atlas edge was added to turn these checks green.

25 Pending creation/legacy cases PASS. The 17 new cases include exact match with
nonmatching ordinal, changed policy/instrument/epoch/digest/outcome/side/eligibility,
wrong cycle, duplicates, invalid price/time and unrelated later ENTER. The existing
real local S8/S7/S5/S6 fixture path now asserts consumed price/time, exact persisted
DPO selection and Pending creation. Explicit injected input is not a natural-run
or public-source authenticity witness. A seed-price assertion initially failed
because the observation helper supplies a different mark; final assertions follow
the actual injected observation contract.

The full DP/cycle join does not yet validate DecisionEvent parent content or prove
complete episode/economic-label equivalence. GAP-0370 source freshness and U04
remain deferred. No original ledger mutation, live/testnet run, orders, push or
service activation.

[Receipt](receipt.json), [transport XML](transport_tests.xml),
[Pending regression](pending_regression.xml),
[baseline prerequisites](baseline_prerequisites.json),
[original bootstrap reproduction](baseline_bootstrap_reproduction.json).
