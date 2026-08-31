# Historical reconsolidation governance v1

```text
ATLAS_AUTHORITY=NONE
RECONCILIATION_AUTHORITY=NONE
RECONCILIATION_ROLE=GOVERNANCE_AND_EVIDENCE_NOT_RUNTIME
RUNTIME_AUTHORIZATION_EFFECT=NONE
CREATES_CANONICAL_AUTHORITY=false
```

This directory persists reconsolidation methodology, the search universe,
and the reconciliation ledger. It is Atlas-adjacent evidence, not Atlas
authority, not a second Master Runbook, and not a runtime, trading, risk,
or execution permit.

Canonical semantic authority remains
`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`.
The System Atlas remains topology and navigation with `ATLAS_AUTHORITY=NONE`.

Machine-readable sources:

```text
GOVERNANCE_V1.yaml     methodology, taxonomy, epistemic rules
census_status.yaml     census lifecycle
search_anchors.yaml    known names; not ledger records
ledger.yaml            reconciliation records
schema.yaml            field catalog
search_surfaces.yaml   bound repository-internal search universe
coverage.yaml          per-surface coverage matrix
discovery_candidates.yaml  hits below ledger threshold
relations.yaml         copied relation index
inventories/           pass v2/v3 reproducible search inventories
understand/            UNDERSTAND pass v2 historical evidence binding
evaluate/              EVALUATE_INDIVIDUALLY pass v1 current-system comparison
adjudicate/            INTEGRATE_OR_DISPOSITION pass v1 adjudication
evidence_resolution/   OPEN_EVIDENCE_RESOLUTION pass v1 (OPEN records only)
reevaluate/            REEVALUATE_OPEN_RECORDS pass v2 current; pass v1 snapshots frozen
evidence/understand_v1/ raw quotes separated from interpretation
evidence/reevaluate_v2/ raw quotes and command captures for pass v2
```

Governance persist baseline: `90dec7208554deb5d2af0a2021bb7bceaf5d6662`.
Census pass v2 bound against: `1b52df25b99a36b99eed91943c2a203ce84f1cad`.

## Sequence

```text
FIND COMPLETELY
→ UNDERSTAND
→ EVALUATE INDIVIDUALLY
→ INTEGRATE OR DISPOSITION
```

No final integrate-or-reject decision is allowed before the first three
steps are evidence-bound for that component.

### FIND COMPLETELY

Search is census-driven. Known names are search anchors, not census
boundaries. Remembered names such as Landscape, Master V2, and Double Play
may start a search. They must not stop it. The census must remain able to
discover `UNKNOWN_HISTORICAL_COMPONENTS`.

Later evidence surfaces may include historical trees, branches, commits,
persisted forensics, evidence, documentation, relations, tooling, and other
provable repository or corpus surfaces. Memory does not create a fact.

Census closure is not inferred from "we found many things", "all known
names appeared", "nothing obvious remains", or exhaustion of a single
branch or forensic corpus. Closure requires a bound search universe and
proven exhaustion. Unproven completeness remains unproven. The initial
state `CENSUS_NOT_STARTED` with `CENSUS_EXHAUSTION_PROVEN=false` is valid.

### UNDERSTAND

Before disposition, the component must be understood from evidence:

- historical identity, names/aliases, paths, and version/commit/ref if proven
- purpose and the problem it was meant to solve
- inputs, outputs, dependencies, consumers
- authority, safety, and runtime roles
- relations and invariants
- proven historical utility
- open or contradictory facts, preserved rather than normalized

If purpose is not sufficiently proven: `PURPOSE_UNDERSTOOD=false`. That
blocks a final integrate-or-reject decision. `INSUFFICIENT_EVIDENCE` stays
OPEN. Missing facts are not reconstructed.

### EVALUATE INDIVIDUALLY

Each component is compared one-by-one to the current system:

- current `origin/main`
- Repository System Atlas v1
- current authority, safety/fail-closed, and runtime/execution bounds
- current canonical SSOTs
- Master-V2 / Double-Play relations only where already evidence-bound
- already present replacement capabilities, proven rather than assumed
- semantic conflicts, functional coverage, and structural impact where proven

Historical purpose and current fit are separate questions. Current absence
does not prove historical irrelevance. Age, path, generation, or naming
schema is not a mass verdict.

### INTEGRATE OR DISPOSITION

Only after FIND + UNDERSTAND + COMPARE may a record receive a final class:

| Class | Meaning |
|---|---|
| `RETAIN_AS_IS` | Still useful and compatible; largely unchanged reintegration is justifiable. |
| `ADAPT_AND_REINTEGRATE` | Purpose remains valuable; implementation or embedding must be adapted. |
| `CAPABILITY_ALREADY_COVERED` | Purpose remains legitimate; a current capability provably covers it. |
| `HISTORICALLY_VALID_BUT_INCOMPATIBLE` | Proven historical purpose; incompatible with current invariants. |
| `INSUFFICIENT_EVIDENCE` | Not proven enough. OPEN. Not a rejection. |
| `REJECT_FOR_CURRENT_SYSTEM` | Positive, reviewable reason against adoption. Not age or absence. |

Historical existence is not automatic authority, not automatic
reintegration, and not rejection grounds. A lost component is an
investigation trigger. Rejection requires a positive reason.
Contradictions remain system facts.

## Ledger lifecycle

```text
DISCOVERED
→ EVIDENCE_BOUND
→ PURPOSE_UNDERSTOOD
→ CURRENT_SYSTEM_COMPARED
→ ADJUDICATED
→ DISPOSITION_DECIDED
```

Then, depending on the decision: `REINTEGRATED`, `COVERED`,
`INCOMPATIBLE`, `REJECTED`, or `OPEN`.

Advancement is not automatic because fields exist.
`INSUFFICIENT_EVIDENCE` may remain `OPEN` indefinitely.

Stable IDs are `RCN-000001`, `RCN-000002`, … . IDs are not reused and are
not rewritten when a name changes. Name is not identity. If two finds may
be the same component, keep separate records and a `POSSIBLE_SAME_AS`
relation until evidence supports identity. Do not deduplicate early.

Claims must use exactly one of:

```text
CANONICAL_CURRENT_FACT
FORENSIC_RAW_FACT
HISTORICAL_FACT
ADJUDICATED_CONCLUSION
INTERPRETATION
HYPOTHESIS
OPEN_QUESTION
CONTRADICTION
```

A hypothesis must not be serialized as a fact. Evidence should point at
repository paths, commit SHAs, refs, persisted forensics, Atlas
entities/relations, or other inspectable sources. Do not invent sources.

## Census pass v3 state (current)

```text
CENSUS_STATUS=CENSUS_CLOSED
CENSUS_EXHAUSTION_PROVEN=true
CENSUS_CLOSED=true
KNOWN_SEARCH_ANCHORS=Landscape;Master V2;Double Play
SURFACES_EXHAUSTION_PROVEN=17
SURFACES_EXHAUSTION_UNPROVEN=0
```

Pass v3 bound two git-history universes (`origin/main` vs `refs&#47;heads` +
`refs&#47;remotes&#47;origin` + `refs&#47;tags`), SHA-deduped unique blobs, content-scanned
relevant text blobs, and exhausted bound commit subjects and bodies.
`git rev-list --all` is not the bound universe. Extra local stash/review/tmp
refs and LOSS_REGISTER-derived unreachable blobs remain documented out of
scope. Atlas `COMPLETE` flags and a stale Atlas `census_meta` SHA are not
authority for this census. No EVALUATE, disposition, or reintegration in that census closeout.

## INTEGRATE_OR_DISPOSITION pass v1 state (frozen)

```text
PASS_ID=INTEGRATE_OR_DISPOSITION_PASS_V1
ADJUDICATE_BOUND_AGAINST_SHA=64aa353073ae7971a966e2f7a1e2a8d3e3c9e6d2
CENSUS_CLOSED=true
LEDGER_RECORD_COUNT=53
ADJUDICATION_ATTEMPTED_RECORD_COUNT=53
DISPOSITION_DECIDED_RECORD_COUNT=18
INSUFFICIENT_EVIDENCE_COUNT=35
RETAIN_AS_IS_COUNT=18
ADAPT_AND_REINTEGRATE_COUNT=0
CAPABILITY_ALREADY_COVERED_COUNT=0
HISTORICALLY_VALID_BUT_INCOMPATIBLE_COUNT=0
REJECT_FOR_CURRENT_SYSTEM_COUNT=0
IDENTITY_MERGES_PERFORMED=0
REINTEGRATION_PERFORMED=false
```

Each of the 53 ledger records was adjudicated against the persisted
EVALUATE_INDIVIDUALLY_PASS_V1 comparison and UNDERSTAND evidence.
`INSUFFICIENT_EVIDENCE` remains `OPEN` and is not a rejection.
`ADAPT_AND_REINTEGRATE` would be a candidate label only; this pass assigned
none. Reintegration, identity fusion, runtime mutation, commit, push, and PR
are not authorized by this persist. UNDERSTAND snapshots under `understand&#47;`
and EVALUATE snapshots under `evaluate&#47;` remain phase-frozen. Census
`current_presence` is not rewritten.

Repository taxonomy names (obeyed; not renamed):
`CAPABILITY_ALREADY_COVERED` (not `ALREADY_COVERED`);
`INSUFFICIENT_EVIDENCE` (not `OPEN_INSUFFICIENT_EVIDENCE`).

## REEVALUATE_OPEN_RECORDS pass v2 state (current)

```text
PASS_ID=REEVALUATE_OPEN_RECORDS_PASS_V2
PREDECESSOR_PASS_ID=REEVALUATE_OPEN_RECORDS_PASS_V1
PREDECESSOR_BOUND_SHA=f9618c73f1834b68588ceab586da4d6408962a10
BASELINE_ORIGIN_MAIN_SHA=7426af2daa4019e7986584a4c53d40b5e182673d
INPUT_OPEN_RECORD_COUNT=35
NEW_FINAL_DISPOSITION_COUNT=5
REMAINING_INSUFFICIENT_EVIDENCE_OPEN_COUNT=30
NEW_HISTORICALLY_VALID_BUT_INCOMPATIBLE_COUNT=1
NEW_REJECT_FOR_CURRENT_SYSTEM_COUNT=4
RCN_000052_REMAINS_OPEN=true
IDENTITY_MERGES_PERFORMED=0
REINTEGRATION_PERFORMED=false
RUNTIME_MUTATION_PERFORMED=false
FROZEN_V1_SNAPSHOTS_UNCHANGED=true
```

This additive persist re-evaluates the 35 records that remained
`INSUFFICIENT_EVIDENCE` / `OPEN` after pass v1. Five records receive a
new final disposition (`RCN-000015`, `RCN-000044`, `RCN-000045`,
`RCN-000046`, `RCN-000051`). `RCN-000052` remains
`INSUFFICIENT_EVIDENCE` / `OPEN` with `CONTRADICTION_ID=C052-1`. The
other 29 open records and the 18 `RETAIN_AS_IS` records are unchanged.
Pass v1 files under `reevaluate&#47;pass_v1_status.yaml`,
`reevaluate&#47;index.yaml`, and `reevaluate&#47;records&#47;` remain phase-frozen.
No identity merge, reintegration, or runtime mutation.

## REEVALUATE_OPEN_RECORDS pass v1 state (historical)

```text
PASS_ID=REEVALUATE_OPEN_RECORDS_PASS_V1
INPUT_PASS_ID=OPEN_EVIDENCE_RESOLUTION_PASS_V1
REEVALUATE_BOUND_SHA=f9618c73f1834b68588ceab586da4d6408962a10
INPUT_RECORD_COUNT=35
NEW_FINAL_DISPOSITION_COUNT=0
REMAINING_INSUFFICIENT_EVIDENCE_OPEN_COUNT=35
IDENTITY_MERGES_PERFORMED=0
REINTEGRATION_PERFORMED=false
```

This pass re-evaluates and adjudicates the 35 records that remained
`INSUFFICIENT_EVIDENCE` / `OPEN` after INTEGRATE_OR_DISPOSITION pass v1,
using OPEN_EVIDENCE_RESOLUTION_PASS_V1 as bound forensic input. A stronger
terminal class is assigned only when that class's burden of proof is met.
This persist assigned none; all 35 remain `INSUFFICIENT_EVIDENCE` / `OPEN`.
That outcome is not a rejection. Reintegration, identity fusion, runtime
mutation, commit, push, and PR are not authorized. UNDERSTAND snapshots
under `understand&#47;`, EVALUATE snapshots under `evaluate&#47;`, INTEGRATE_OR_DISPOSITION
snapshots under `adjudicate&#47;`, and OPEN_EVIDENCE_RESOLUTION snapshots under
`evidence_resolution&#47;` remain phase-frozen. Census `current_presence` is not
rewritten, including the RCN-000052 contradiction.

## OPEN_EVIDENCE_RESOLUTION pass v1 state (historical)

```text
PASS_ID=OPEN_EVIDENCE_RESOLUTION_PASS_V1
EVIDENCE_RESOLUTION_BOUND_SHA=f9618c73f1834b68588ceab586da4d6408962a10
INPUT_OPEN_RECORD_COUNT=35
FINAL_DISPOSITION_CHANGES_PERFORMED=0
IDENTITY_MERGES_PERFORMED=0
REINTEGRATION_PERFORMED=false
```

This pass exhausts repository-internal evidence for the 35 records that
remained `INSUFFICIENT_EVIDENCE` / `OPEN` after INTEGRATE_OR_DISPOSITION
pass v1. It records an evidence-resolution status per OPEN record. That
status is not a new terminal disposition. UNDERSTAND snapshots under
`understand&#47;`, EVALUATE snapshots under `evaluate&#47;`, and INTEGRATE_OR_DISPOSITION
snapshots under `adjudicate&#47;` remain phase-frozen. Census
`current_presence` is not rewritten, including the RCN-000052 contradiction.

## EVALUATE_INDIVIDUALLY pass v1 state (historical)

```text
EVALUATE_PASS_ID=EVALUATE_INDIVIDUALLY_PASS_V1
EVALUATE_BOUND_AGAINST_SHA=0e6cbb860f716d527873d97556d0968df4a197bf
CENSUS_CLOSED=true
UNDERSTAND_PHASE_STATUS=EVIDENCE_EXHAUSTED
LEDGER_RECORD_COUNT=53
CURRENT_SYSTEM_COMPARED_RECORD_COUNT=53
ADJUDICATED_RECORD_COUNT=0
DISPOSITION_DECIDED_RECORD_COUNT=0
IDENTITY_MERGES_PERFORMED=0
```

Each of the 53 ledger records was compared one-by-one to `origin&#47;main` at
the bound SHA. Historical purpose and current fit remain separate questions.
Current absence is not irrelevance. A later path with a similar name is not a
proven replacement. UNDERSTAND snapshots under `understand&#47;` stay unevaluated.
No disposition, reintegration, identity fusion, runtime mutation, or merge in
that EVALUATE closeout. Live ledger later advanced under INTEGRATE_OR_DISPOSITION
pass v1; the `evaluate&#47;` snapshot tree remains comparison-only.

## UNDERSTAND pass v2 state (historical)

```text
UNDERSTAND_PASS_ID=UNDERSTAND_PASS_V2
UNDERSTAND_BOUND_AGAINST_SHA=a70bed0dc1586bedb58642fe7f6c6fef760b2478
CENSUS_CLOSED=true
CURRENT_SYSTEM_COMPARED_RECORD_COUNT=0
ADJUDICATED_RECORD_COUNT=0
DISPOSITION_DECIDED_RECORD_COUNT=0
IDENTITY_MERGES_PERFORMED=0
```

UNDERSTAND pass v2 exhausted remaining OPEN/PARTIAL records against
repository-internal historical evidence. `evidence_exhausted=true` may coexist
with PARTIAL/OPEN when the bound evidence does not carry the missing statement.
Clusters under `understand&#47;clusters.yaml` are navigation only, not identity
groups. `POSSIBLE_SAME_AS` remains hypothesis. Archive presence is not obsolete.
Historical revert is not disposition. No EVALUATE, current-system comparison,
disposition, reintegration, or identity fusion in that UNDERSTAND closeout.

## UNDERSTAND pass v1 state (historical)

```text
UNDERSTAND_PASS_ID=UNDERSTAND_PASS_V1
UNDERSTAND_BOUND_AGAINST_SHA=a70bed0dc1586bedb58642fe7f6c6fef760b2478
```

UNDERSTAND binds historical purpose/inputs/outputs/relations from repository
evidence. Purpose requires a non-empty statement plus at least one fact-class
claim with evidence. Unproven purpose stays `PURPOSE_UNDERSTOOD=false` with
open questions.

Inventories live under `docs/system_atlas/reconciliation/inventories/`.

## Census pass v2 state (historical)

```text
CENSUS_STATUS=CENSUS_IN_PROGRESS
CENSUS_EXHAUSTION_PROVEN=false
CENSUS_CLOSED=false
KNOWN_SEARCH_ANCHORS=Landscape;Master V2;Double Play
```

Pass v2 walked unique tip trees by exact Git tree SHA, inventoried reachable
object path names, and file-inventoried `archive&#47;PeakTradeRepo`. Git-history
blob contents remained unproven after that pass.

## Census pass v1 state (historical)

Pass v1 bound a repository-internal search universe and opened the first
ledger records in `DISCOVERED`/`EVIDENCE_BOUND` only. Exhaustion remained
unproven.

## Initial governance persist (historical)

The empty-ledger `CENSUS_NOT_STARTED` persist remains a valid schema state.
It is no longer the live tree state after census pass v1.

## Validation

```text
./scripts/pt -m pytest -q tests/ops/test_reconciliation_ledger_v1.py tests/ops/test_reconciliation_census_pass_v1.py tests/ops/test_reconciliation_understand_pass_v1.py tests/ops/test_reconciliation_understand_pass_v2.py tests/ops/test_reconciliation_evaluate_pass_v1.py tests/ops/test_reconciliation_adjudicate_pass_v1.py tests/ops/test_reconciliation_evidence_resolution_pass_v1.py tests/ops/test_reconciliation_reevaluate_open_records_pass_v1.py tests/ops/test_reconciliation_reevaluate_open_records_pass_v2.py tests/ops/test_system_atlas_v1.py
./scripts/pt scripts/ops/validate_system_atlas_v1.py
```

The Atlas validator also loads this tree when present. Failure is
fail-closed. This does not raise Atlas authority.
