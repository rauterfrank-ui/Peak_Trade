# Local implementation phase 3: position episode and Exit continuity

Local uncommitted changes on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`.
[Contract, historical comparison and limits](../specs/BOUNDED_POSITION_EPISODE_EXIT_CONTINUITY_V1.md).

## Observed defects and correction

Four new restore controls first reproduced acceptance of a foreign instrument,
an empty manifest, a missing marker treated as fresh state, and a marker that
disagreed with its state. They now reject at the existing restore boundary.
Malformed resealed state controls additionally reject truthy/nonboolean position
flags, boolean price, nonfinite time and missing sequence. An integer-valued
historical price roundtrip remains valid; normalized floating representation is
not substituted when verifying the original persisted digest.

Explicit episodes now retain their original entry time and pending Exit identity
through the existing owner and reload. Actual current core intervention controls
compare known versus unknown entry time at equal market inputs, for both long and
short. Only the known original time activates the existing TimeExit; the core
input digest and actual EntryExit result change accordingly. Unknown entries do
not acquire a current mark or observation timestamp as a replacement anchor.

Actual N1/S7/core/DP/full-close controls use supplied observations and an open
remaining quantity of 0.4. The long and short cases produce TimeExit, EXIT, then
the full remaining reduce-only quantity with opposite order side. Entry sizing
is guarded by a forbidden-call spy, while the management/Exit owners execute.
The actual venue-plan binder receives INTERNAL_SIMULATED_EXECUTION from the
episode scope; no LIVE substitution. A different lane rejects before creation
of the governed-cycle ledger. Foreign accounts/modes, side/flat transitions and
changed time policy cannot silently repurpose the episode.

Stale writer controls preserve the newer generation/obligation. An injected
interruption between state and marker publication blocks both the current handle
and reload, without repairing original files. Failed replay leaves episode files
unchanged. These are controlled failure cases, not exhaustive crash proof.

## Final connected validation

**126 PASS, zero failures/skips**, using `./scripts/pt -m pytest -q` over:

- `test_position_episode_exit_continuity_v1.py`: 29.
- `test_exit_policy_restore_integrity_v1.py`: 9.
- `test_exit_policy_producer_binding_v1.py`: 9.
- `test_current_productive_occupied_scope_continuity_v1.py`: 11.
- `test_current_productive_occupied_management_dispatch_v1.py`: 25.
- `test_current_productive_full_close_execution_handoff_v1.py`: 19.
- `test_full_decision_path_atomic_restart_closure_v1.py`: 7.
- `test_current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.py`: 17.

JUnit receipt is retained with source hashes in the local phase-3 implementation
report. Runtime isolation, scoped Ruff lint/format and Git whitespace checks pass.
Phase-2's separately reproduced twelve baseline failures remain recorded there;
they are not erased by this passing, different test population. Phase counts are
not summed into a system certificate.

## Default-path comparison and its limits

An isolated differential loaded the exact original core source from Git, SHA256
`4aff801579dd534182d94005a7f40b2b07b42a8feeb0e9bbd1e7be543cff1e95`.
Ten complete result projections matched: five default-path cycles per direction,
including three entry and two occupied cycles, with exact equal prior filesystem
state and equal exogenous seal nonce. No new episode arguments were supplied.

Initial naive comparisons did not match: the existing LayeredCore authority seam
uses `uuid.uuid4().hex`, which propagates into references and result digests.
Restoring the filesystem alone does not equalize that input. The successful probe
therefore replaced only the seam module's UUID provider in its isolated process
with equal deterministic nonces in old/new runs. No checkout source or global UUID
module was modified. This proves controlled default parity at equal nonce, not
raw independent-run byte identity, natural determinism or whole-system semantics.

## Preserved boundaries

No trading formulas, Scope parameters, configuration, original ledgers or previous
evidence are modified. The historical producer and EntryExit/quantity authorities
remain owners. Tests use temporary state, synthetic injected observations and no
network or credentials. No actual order, capital movement, service activation,
commit, push or publication. Entry-source authenticity, full lifecycle and the
cross-owner recovery boundary remain explicitly unaccepted.
