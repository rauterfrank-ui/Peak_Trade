---
docs_token: DOCS_TOKEN_CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_POLICY_GOVERNED_LIVE_C1_CONTINUOUS_RUN_V1
status: active
scope: Policy-governed persistent Natural-ENTER continuous run with public readonly Fresh-C1 GET
workpackage_id: CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_POLICY_GOVERNED_LIVE_C1_CONTINUOUS_RUN_V1
last_updated: 2026-11-04
---

# Policy-governed persistent Natural-ENTER live Fresh-C1 continuous run V1

```text
WORKPACKAGE_ID=CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_POLICY_GOVERNED_LIVE_C1_CONTINUOUS_RUN_V1
BASELINE_ORIGIN_MAIN_SHA=dd4c23da1f3f519413fe8c9f04ddd0050ff3f026
CONTINUOUS_RUN_AUTHORIZED_MODULE_PIN=false
RUNTIME_AUTHORIZATION_EFFECT=BOUNDED_PRE_EXTERNAL_ONLY
```

Owner-GO decision:
`config/governance/current_productive_bounded_continuous_run_and_fresh_c1_get_owner_go_v1_decision.json`

Scoped tokens (consume via evidence; module pins unchanged):

- `OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_RUN_V1`
- `OWNER_GO_S4A_EH_EXACTLY_ONE_PUBLIC_READONLY_FRESH_C1_GET_V1`

## Path

S8 Cap24 handoff → `run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1`
→ `run_policy_governed_current_productive_continuous_cycle_run_v1`
→ S6 poll (`LiveFreshC1ContinuousObservationSourceV1` or test double)
→ N1/S5/S7 → **PRE_EXTERNAL** terminal.

## Non-implications

No EXTERNAL_EFFECT, POST, permit mint, credentials, Actual-Venue-POST GO reuse,
or `CONTINUOUS_RUN_AUTHORIZED=true` module pin.

## Productive entry (PRE_EXTERNAL only)

`scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py`

Bounded observation flags (`--max-cycles`, `--max-run-duration-seconds`) apply to the
**S6 sequencer only**; see
`docs/ops/specs/CURRENT_PRODUCTIVE_CONTINUOUS_OBSERVATION_BUDGET_V1.md` for
`TOTAL_WALLCLOCK_SECONDS` vs `SEQUENCER_ELAPSED_SECONDS` report fields.

Run-scoped evidence under `runtime&#47;current_productive&#47;` (untracked). Cold-lane bootstrap
uses Cap24-bound `native_id` for the first public Fresh-C1 GET before sidestate cursor
persist; S6 then waits for strictly newer finalized 1m bars. Auth-free scope injects
flat occupancy payloads (no credential positions GET).

## Verification

- `tests/ops/test_current_productive_persistent_natural_enter_policy_governed_live_c1_v1.py`
- `tests/ops/full_core_live_path_composition_root_v1/test_pre_external_convergence_runtime_duration_transparency_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/current_productive_bounded_continuous_run_owner_go_wiring_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py`


## Pending-outcome mark clock binding — 2026-11-04

The existing observation wrapper binds price and integer-millisecond ts from the
same successful, single, native-instrument mark row. Candle-open time is not the
mark event clock. Immediately after the inner poll returns, local epoch time is
measured as wrapper receipt and explicitly passed to the aggregate resolver.
It is not an exact HTTP receipt or a venue snapshot/freshness guarantee. Unknown,
ambiguous, nonfinite, noninteger-millisecond or future mark time cannot advance
pending outcomes; the original observation is returned unchanged. Aggregate
resolver callers must supply finite positive event time and finite receipt no
earlier than event time. No fabricated receipt fallback remains there.

Premature finalization, Horizon capture knowledge time, source classification and
complete durable measurement retention remain separate open contracts; no natural
outcome or restart closure follows. See [scoped evidence](../evidence/pending_mark_clock_binding_v1_2026_11_04/README.md).


## Pending elapsed-bar/source admission — 2026-11-04

Pending v2 mark events reuse the existing O4 elapsed-event-time finalizer and
persist every accepted in-progress sample. Only bars starting at/after decision
count, matching the existing snapshot selector. Legacy mark histories without
v2 contract remain preserved and fail closed; no automatic replay migration.
Fixture histories may produce isolated bars but cannot invoke productive outcome
evaluation/learning. Unknown/mixed source classes, invalid identity/price/time and
out-of-order samples are denied. Public-input class alone is not authenticity;
actual source proof remains open. Closure uses measured invocation knowledge time
no earlier than all recorded receipts. Global evaluator defaults, durable journal/
index publication and complete measurement persistence remain separate contracts.
[Scope and tests](../evidence/pending_elapsed_horizon_and_source_gate_v2_2026_11_04/README.md).


## Pending journal publication — 2026-11-04

The existing store's validated append journal owns pending state. Index is derived;
readers never adopt it as authority and do not repair it on read. Journal framing,
record identity/version and allowed progress must validate. Canonical mutation uses
one cooperating local kernel flock, explicit expected prior record and journal
append/flush/fsync before derived index publication. Append/index uncertainty does
not permit blind replay. Complete root loss, rollback/authenticity, power-loss and
cross-DDO-ledger atomicity remain unproven; no automatic corrupt-tail truncation.
[Bounded process tests](../evidence/pending_journal_authority_v2_2026_11_04/README.md).


## Complete Pending measurement references — 2026-11-04

Complete existing supplier artifacts precede evaluation/learning. Storage remains
with the Pending owner, bound to decision, instrument, horizon, source history and
knowledge time. File fsync/atomic publication/readback and immutable retry protect
later reference resolution. Closure retains full bundle digest plus measurement
and information-set refs. Rechecking CLOSED without valid complete content refuses
verification while retaining historical records. Natural authenticity, exact DPO/
episode lineage and atomic cross-ledger closure remain separate proof questions.
[Implementation and tests](../evidence/pending_measurement_artifact_persistence_v1_2026_11_04/README.md).


## Pending creation context — 2026-11-04

Creation requires supplied finite positive decision time and reference price;
boolean/missing/invalid inputs return explicit PENDING_DECISION_CONTEXT_UNBOUND
before state access. This guards validity only. The normal launcher still needs
exact price/selected-DPO/cycle/episode lineage independent of optional forensic
traces. Do not infer exact producer ENTER from a generic DecisionEvent enum.
[Source boundary and tests](../evidence/pending_creation_context_admission_v1_2026_11_04/README.md).


## Exact normal Pending context — 2026-11-04

Supersedes the normal return-path gap above: S7 invocation replay CMC and DP
producer payload travel through S5 runner and S6 cycle record. Reporting requires
one exact cycle/full canonical DP match when context exists; no cursor/ordinal
fallback on mismatch. Launcher uses matched CMC price/decision_time after instrument
checks; optional trace is no price authority. Missing context remains unbound.
Legacy reporting without context is retained. DecisionEvent parent/episode and
source freshness remain distinct open boundaries.
[Implementation and verification](../evidence/pending_exact_decision_context_v1_2026_11_04/README.md).


## Stored Pending DecisionEvent parent — 2026-11-04

Context-bound creation resolves stored DPO/parent through the existing DDO ledger
reader and checks present producer, identity, time, correlation, reason and generic
enum contracts. Input price/time/context/instrument and side must match transported
facts. Failure returns PENDING_DECISION_LINEAGE_UNBOUND before Pending mutation.
Context-free legacy admission is unchanged. Reporting preserves explicit boolean
false. Missing DecisionEvent input snapshots and episode/target equivalence remain
open. [Evidence](../evidence/pending_decision_parent_lineage_v1_2026_11_04/README.md).


## Stored Pending correlation and producer decision id — 2026-11-04

Context-bound creation copies correlation_id from the validated stored DecisionEvent
and policy_decision_id from the exact validated DPO producer payload. A conflicting
optional caller decision_id rejects. Do not reconstruct a stored correlation from
cycle naming. Resolver passes this value through evaluation, Learning and export.
Legacy/context-free calls and old stored records are not silently migrated.
[Verification](../evidence/pending_bound_decision_identity_v1_2026_11_04/README.md).
