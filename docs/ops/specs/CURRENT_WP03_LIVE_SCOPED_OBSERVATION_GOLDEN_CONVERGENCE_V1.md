---
docs_token: DOCS_TOKEN_CURRENT_WP03_LIVE_SCOPED_OBSERVATION_GOLDEN_CONVERGENCE_V1
status: implemented_bounded_offline
authority: NONE
runtime_authorization_effect: NONE
---

# CURRENT-WP-03 — Live-Scoped Observation Golden Convergence V1

```text
AUTHORITY=NONE
WORK_PACKAGE_ID=current_wp03_live_scoped_observation_golden_convergence_v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
POST_ALLOWED=false
```

## Purpose

Close BLK-10/BLK-11: full `GOLDEN_TRACE_KEYS` runtime projection from the standing
N=1 supervisor path; bilateral LONG/SHORT/HOLD; ≥2 contiguous C1 confirmation epochs
under scoped read-only inject transport (not live venue POST).

## Dependencies

- CURRENT-WP-01 (`n1_standing_pre_external_runtime_supervisor_v1`)
- CURRENT-WP-02 (productive default Cap22 handoff when enabled on supervisor config)

## Entrypoints

- `project_supervisor_golden_trace_v1`
- `prove_wp03_golden_convergence_v1`
- `write_current_wp03_closure_evidence_v1`

## Current boundary evidence

The projection reads the current S6/S5 output through
[runtime boundary evidence](../../../src/ops/current_wp03_live_scoped_observation_golden_convergence_v1/runtime_boundary_evidence_v1.py).
The trace and sequencer terminal, counts, accepted C1 and durable cursor must
agree. The original S5 envelope and original pending Core decision are carried
by the current cycle record. Envelope integrity is checked by its original owner.
Canonical instrument identity belongs to the decision; the envelope carries the
native venue identity. A cycle ID is not an envelope ID. Decision knowledge time
can follow the accepted market event and is not relabelled as the same timestamp.

A historical natural_enter_decision label, requested side, missing old record
fields or a different run cannot promote HOLD to PRE_EXTERNAL. The projection
also cannot hide an actual boundary under a requested HOLD label. Bilateral
convergence compares expected LONG/SHORT/HOLD with the current decision and
boundary instead of comparing a trace with itself.

Two-epoch confirmation requires the actual consumed C1 timestamps, consistent
cycle counts and adjacent PT1M events. Counts alone, duplicates, reverse time or
gaps do not prove contiguous confirmation. Missing current HOLD observations are
not accepted as a successful HOLD scenario either.

The test harness uses the actual standing supervisor, original budget host,
original layered ARM preparation, matched instrument history and explicit
offline account/pretrade ports. These ports include existing productive-class
test fixtures; their labels do not prove venue contact or natural market quality.
Without fresh pretrade input, the actual Core may propose ENTRY while S5 remains
HOLD. Public/ranking and explicitly injected Cap24 provenance are not a newly
proved causal selection chain. No fill, permission or full restart admission is
created by observing the pre-external boundary.

The current record also carries the original sized canonical intent and the
canonical decision parent. Original-owner validation and exact parent, epoch,
instrument, action, side, reduce-only and quantity agreement are required.
An EXIT additionally requires the original close assessment/intent handoff.
Missing or contradictory PRE_EXTERNAL evidence is projected as UNPROVEN.

The offline acquisition clock is explicitly held within one synthetic snapshot.
The existing decision/capture-epoch conflict and repeated-read freshness defect
remain open; this fixture is not their repair or a natural-time acceptance.

The [dated implementation evidence](../evidence/WP03_CURRENT_CONSUMER_PROOF_2026_11_07.md)
records verification and remaining limits.
