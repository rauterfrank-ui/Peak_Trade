# Representation plan requires supplied context — 2026-11-04

Baseline df6f5af25; continues Phase-23 producer/Phase-24 consumer construction.
The existing adaptation producer emits one applicable item with pattern_ref and
nonempty learning_representation_lineage_ref, or a separate fail-closed decision.
The plan builder previously replaced absent items/payload/pattern with the known
positive feature-usefulness fixture and silently selected the first of many items.
This could bypass the newly strict unknown-label evaluator by inventing its input.

PROPOSE_REPRESENTATION_RESEARCH_CONTEXT now requires exactly one list/tuple item,
a mapping payload, a supplied nonempty string pattern and representation lineage.
Existing error type reports explicit missing-context/cardinality reasons. Missing
facts cannot create an implicit positive fixture. Existing NO_ACTION_FAIL_CLOSED
path remains separate; known explicit fixture inputs remain supported.

Ten before-failures now PASS; connected scope 37 PASS, including actual Phase-24
Loop-C wrapper and governance tests. Seven complete known plan outputs/digests
compare identical against baseline. This is structural/semantic input admission,
not full independent revalidation of the upstream adaptation decision digest or
measurement of representation quality. A real numerical evaluator and useful
next adaptation remain open. No source/lineage facts are synthesized.

This supersedes the prior scope's historical statement that factory default
fixtures remain: implicit defaults for missing applicable context are removed.
The named default fixture remains available only as an explicit supplied value.
No historical records/original-ledger mutation, activation, extra agents or push.
U04/GAP-0370 deferred.

[Receipt](receipt.json), [before](before.xml), [after](after.xml),
[known plan comparison](known_plan_output_comparison.json).
