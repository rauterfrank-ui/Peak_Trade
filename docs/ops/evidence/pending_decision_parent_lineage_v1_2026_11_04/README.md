# Pending DecisionEvent parent admission — 2026-11-04

Baseline: 85491657b. Read-only owner access before context-bound Pending creation.

The existing capture emits a generic DecisionEvent and a typed DPO observation
from the same producer call. Both share capture time, correlation and cycle; the
DPO explicitly references the DecisionEvent as causal parent. Exact DP ENTER uses
the existing generic UNKNOWN mapping. DecisionEvent has no policy_decision_id or
raw market/feature snapshot in this path. Those absent fields cannot be validated
by inventing equivalences.

Context-bound creation now uses AppendOnlyDdoLedgerV0.read_all, including existing
schema/hash/chain checks, then resolves the stored DPO and DecisionEvent. Exact
producer payload/cycle, report projection, parent reference, cycle/correlation/time,
producer/owner, captured reason codes and the existing generic enum mappings must
agree. Pending input instrument/native, price, decision time, market context and
side must agree with the bound context/report. Mismatch reports
PENDING_DECISION_LINEAGE_UNBOUND before Pending mutation. Original ledgers are
never repaired or rewritten. Context-free legacy callers retain their old behavior;
this gate does not certify their lineage.

A further reporting correction retains typed execution_eligible=False as the
explicit string false. Previously the parser converted it to an empty string.
This preserves producer meaning and does not change execution eligibility.

16 new cases PASS; 15 fail when the original baseline creation function is loaded
for those same tests. Baseline XML is retained. The positive case uses the actual
existing capture, not a hand-invented DecisionEvent. Negative cases include
schema-valid, newly chained ledgers with changed parent fields, missing records,
damaged owner history, substituted Pending inputs and report side. The existing
S8/S7/S5/S6 local fixture still reaches exact DPO selection and Pending creation.
Connected final scope: 77 PASS, one failure for the already absent historical
report in the old reporting test. The command and source hashes are in the receipt.

Existing-field agreement is not proof of cryptographic public-source authenticity,
missing DecisionEvent input snapshots, original episode construction, or equality
of economic measurement/prognosis windows. GAP-0370 and U04 remain deferred. No
live/testnet operation, orders, service activation, publication or push.

[Receipt](receipt.json), [baseline XML](baseline_tests.xml),
[baseline creation](creation_v1.before.txt).
