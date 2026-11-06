# Local implementation phase 2: N5 completion and recovery transport

Local uncommitted change on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`.
[Contract and semantic proof limits](../specs/BOUNDED_SYSTEM_N5_COMPLETION_AND_RECOVERY_TRANSPORT_V1.md).
Phase 1 code and its historical receipts are preserved.

Two new actual one-/five-slot optional-completion controls fail before the fix
with CYCLE_AUTHORIZATION_REPLAY in the second readiness/cycle call. The corrected
orchestrator consumes the first results instead. Four new projection/consumer
binding controls reject before filesystem changes. The two-slot durable-context
transport control first exposes the public consumer's unsupported argument; two
lines now expose and forward its already existing private T2 parameter.
The new transport test initially lacked parent directories; that fixture error was
corrected before reproducing the actual unsupported-argument defect.

Final connected run: **110 PASS / 12 FAIL**, no skipped tests, across 122 cases in:

- Productive N5 orchestrator: all 15 PASS, including seven new cases.
- Standalone N5 completion: 5 PASS / 9 FAIL.
- Portfolio budget host: 12 PASS / 3 FAIL.
- Durable portfolio budget recovery: all 22 PASS.
- Outer entry budget policy: all 15 PASS.
- Checked lane selection publication: all 39 PASS.
- Cap24 canonical price provenance composition: both cases PASS.

After inspection of the legacy fixture failures, two additional disjoint controls
exercise the actual standalone entry using valid native inputs from real Cap23/24
preparation. Both PASS (one/five slots). The current orchestrator test population
therefore has 17 verified cases, nine newly added: 15 from the connected run and
these two additional controls. Union of these current checks is **112 PASS /
12 FAIL across 124 distinct cases**. The extra focused run deselects the already
verified 15 cases; it does not count those deselections as passes or skips. The
122-case connected run above remains preserved with its original result.

The nine standalone-completion failures occur before completion at the unchanged
core's native-contract admission: the historical fixture uses VENUE-HARNESS /
VENUE-* identities that are not accepted futures identities. An isolated canonical
Python process loads the exact original completion source from Git and runs the
same unchanged test file: the identical nine case IDs fail, five pass. No instrument
guard, source identity or expected result is weakened to obtain green tests.

The three budget-host failures also reproduce with the exact original public
consumer source loaded in an isolated canonical process. Their mocked governed
runner returns None; the existing Pending-context handoff calls dataclasses.replace
on that result and raises TypeError. These cases do not reach their intended
assertions and are not counted as passing position-management proof.

The initial original-source loading probe lacked inspect source text for one
source-inspection assertion, producing an extra harness failure. The final baseline
probe attaches the exact Git bytes through Python linecache and yields the bound
5 PASS / 9 FAIL result above. Neither probe overwrites checkout source. Original
test failures remain visible, not deselected from the connected current run.

Existing recovery/entry controls in the connected suite exercise real original
durable owner recovery, retained holds, sizing and policy checks with injected
observations. They are not relabeled as a complete successful N5 ENTER/restart.
All new runs use disposable state and injected public/private observations. No
network request, credential access, real order, capital movement or external message.

Canonical runtime validation PASS before tests. Scoped Ruff lint/format and Git
whitespace checks PASS. No commit/push or activation. Scope formulas/parameters and
original ledgers remain outside the changed path set. Evidence counts from phase 1
and intermediate reruns are not summed into a new whole-system certificate.
