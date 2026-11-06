# Incremental research immediate predecessor binding — 2026-11-04

Baseline dda30913c. Phase-22 origin 453506965, 2026-09-26. The existing closure
promises immediate-predecessor-only comparisons. Sorting alone allowed B0→B2 and
labelled the supplied B0 information set as B1's predecessor. Direct stage calls
had the same mismatch; duplicate baselines were also accepted.

An active stage now checks a supplied predecessor's actual stage_id against the
existing predecessor_stage_id_v1 mapping before projection/plane work. B0 cannot
consume a predecessor. A missing predecessor remains explicitly insufficient.
The existing early DEFERRED B5 route performs no comparison/plane work and remains
reachable. Initial admission placed this check too early and broke that deferred
control (22 PASS/1 FAIL retained); the guard was moved after its early return.

Three failures before; final 23 connected cases PASS. Complete valid B0→B1 and
B0→DEFERRED B5 closure outputs/digests compare identical against baseline. This
binds actual topology, not numeric incremental value or full predecessor content.
The current challenger_delta still comes from caller-supplied champion/challenger
scores in the stage M4 request. No equivalence to a measured immediate-predecessor
score, dataset/window equality or new numeric formula is inferred.

Read-only source followthrough also finds the normal Loop-C wrapper already calls
the actual adaptation producer with its validated Meta input and passes that result
directly into the plan builder. A duplicate new source owner/replay API is not
needed to establish this static path. It returns next_learning_evidence; the
bounded src/scripts search of that schema/class/id found its builder/wrapper but
no separately demonstrated next numeric adaptation consumer. This is not a global
absence claim or a runtime proof. Representation/quality numerical source remains
open, as do Meta units/target-surface equivalence.

No original-ledger/historical-record mutation, activation, new agents or push.
U04/GAP-0370 deferred.

[Receipt](receipt.json), [before](before.xml), [after](after.xml),
[deferred admission correction](initial_deferred_admission_failure.xml),
[valid/deferred comparison](valid_and_deferred_comparison.json).
