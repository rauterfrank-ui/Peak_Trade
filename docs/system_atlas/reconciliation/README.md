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
inventories/           pass v2 reproducible search inventories
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

## Census pass v2 state

```text
CENSUS_STATUS=CENSUS_IN_PROGRESS
CENSUS_EXHAUSTION_PROVEN=false
CENSUS_CLOSED=false
KNOWN_SEARCH_ANCHORS=Landscape;Master V2;Double Play
```

Pass v2 walked unique tip trees by exact Git tree SHA, inventoried reachable
object path names, and file-inventoried `archive/PeakTradeRepo`. Git-history
blob contents remain unproven. Search anchors are still not ledger records
and still not census boundaries. No disposition. No reintegration.

Inventories live under `docs/system_atlas/reconciliation/inventories/`.

## Census pass v1 state (historical)

Pass v1 bound a repository-internal search universe and opened the first
ledger records in `DISCOVERED`/`EVIDENCE_BOUND` only. Exhaustion remained
unproven.

## Initial governance persist (historical)

The empty-ledger `CENSUS_NOT_STARTED` persist remains a valid schema state.
It is no longer the live tree state after census pass v1.

## Validation

```text
./scripts/pt -m pytest -q tests/ops/test_reconciliation_ledger_v1.py tests/ops/test_reconciliation_census_pass_v1.py tests/ops/test_system_atlas_v1.py
./scripts/pt scripts/ops/validate_system_atlas_v1.py
```

The Atlas validator also loads this tree when present. Failure is
fail-closed. This does not raise Atlas authority.
