# Representation adaptation decision witness admission — 2026-11-04

Baseline 449901986. The existing Phase-23 owner already defines complete adaptation
decision payload, identity derivation and result digest. The Phase-24 builder
formerly read only schema plus selected fields, so changed parent identity/domain/
digest and contradictory no-mutation fields could still mint a valid plan.

A validator in the existing adaptation owner reconstructs its canonical item and
full decision envelopes through its existing builders, compares parent/item
identity and result digest, and checks its existing dispositions/outcomes/source-id
shape and no-effect metadata. Plan creation consumes this validated witness,
translating failure through the existing plan error type. No second decision owner,
new hash domain, measurement, class or capability is introduced.

Old plan/evaluator test helpers supplied arbitrary placeholder parent identities
and incomplete decisions. They now build explicit synthetic fixtures through the
actual existing owner payload/item builders. Fail-closed fixture uses the actual
existing missing-evidence producer. This supplies valid contract fixtures without
claiming underlying natural Meta evidence. The real Loop-C path still uses its
actual Meta/adaptation producer. Original evidence snapshots remain immutable.

Ten new before-failures; 65 connected cases PASS, plus two distinct resealed missing
pattern/lineage controls PASS. These recompute both existing decision identity and
result digest before checking required semantic facts; tests do not merely reject
stale hashes. Three complete valid-owner plan outputs/digests compare identical
against baseline. Total 67 distinct cases across those runs. No natural numeric
evaluation, useful adaptation, external-origin authenticity or end-system claim.

This closes the earlier local upstream-decision-witness gap. Valid self-consistent
caller assertions do not prove source truth; broader Meta target/units, numeric
representation evaluation and consumers remain separate. Historical records and
original learning ledger preserved. U04/GAP-0370 deferred; no activation or push.

[Receipt](receipt.json), [before](before.xml), [after](after.xml),
[resealed contexts](resealed_context.xml), [valid owner comparison](valid_owner_plan_comparison.json).
