# Local implementation phase 8: explicit simulated flat seal and successor

Local uncommitted work on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`.
[Contract, scope boundaries and identity finding](../specs/BOUNDED_SIMULATED_EPISODE_FLAT_SEAL_AND_SUCCESSOR_V1.md).

Final connected validation: **272 PASS, no failures/errors/skips**, through
`scripts/pt`. It contains the same 249-case phase-7 population at current affected
sources plus **23 new close/seal/successor controls**. Their per-file counts and
final JUnit are retained in the local phase-8 report; intermediate reruns are not
summed into a new certificate. Separately reproduced phase-2 baseline failures
remain recorded in their original scope.

New positive long/short controls first create a real current-core TimeExit
obligation, apply the original simulated full-close fill/accounting, observe
explicit flat and seal. Active Exit fields clear, while the audit retains the exact
old pending identity and prior owner bytes. Old cursor bytes and a retained
unrelated Outcome-obligation sentinel remain untouched. The sentinel proves no
purge at that path, not a real Outcome-owner closure or later supplier delivery.
Generic active restore of the sealed position rejects; dedicated audit inspection
validates its retained source and old/new state relation.

Two additional controls execute the actual N1/S7/DP/full-close path. Its envelope
side, native-contract quantity and reduce-only flag feed the existing simulated
fill model and actual Accounting owner. The resulting zero position and explicit
zero observations permit sealing. Permit/POST remain false/zero. This is controlled
numerical consumption of an actual close-plan result, not a real order, natural
venue fill or persistent original Decision-to-fill attribution certificate.

Ten interventions reject empty position response, absent pending response, pending
order, nonzero or duplicate-zero row, absent/open canonical portfolio, stale flag,
future observation and unapplied close without changing Exit state. Source archive
tampering invalidates inspection while leaving terminal owner state unchanged.
An injected state/marker publication fault blocks reload and preserves cursor
bytes. No automatic rollback, ledger purge or repair occurs.

Long/short successor controls extend the original closed fill journal with a new
opposite opening, use a different opening-derived episode key and new owner roots,
then bootstrap and run the original core with the new direction. Old owner/cursor
JSON remains unchanged; the old sealed handle cannot run an occupied cycle. Four
negative controls reject reused key, changed account, a descendant old state root
and a new source that forks the prior journal. A session seal preserves its
attempt allowance; recovery permits inspection but rejects runtime/source reentry.

The first 15-case run had two failed assumptions that old/new Scope IDs would
differ. Actual current-core bootstrap labels are identical across these roots;
their complete snapshots/digests and SideStates differ. The tests now retain that
countercase explicitly and assert separate episode identity/root plus actual new
direction. No Scope ID, formula or parameter was changed to obtain green tests.
Bare-label global attribution/deduplication is a new explicit integration question,
not dismissed as correct merely because it is existing behavior.

The original rotation/custody owner and artifact purge matrix were read. No global
release is claimed from their harness defaults or from local flat; their rules and
old ledgers remain unchanged. Persistent old resource registrations stay retained.
Session/Exit terminal status is scoped to that historical episode, not global
health, account-wide flat, capital availability or analytical-obligation completion.

Runtime isolation, scoped Ruff lint/format, whitespace and final source/report
readback pass. Exact working-file/protected-owner hashes and comparison to phase 7
are retained. No new physical seal-time or power-loss experiment, default service
activation, credentials, venue request, actual order, capital action, commit, push
or publication. The phase-7 Adverse/TimeExit question and other whole-system
acceptance obligations remain open.
