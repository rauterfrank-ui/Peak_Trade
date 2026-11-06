# Local implementation phase 7: same-episode average and quantity progress

Local uncommitted work on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`.
[Contract, variant decision and outstanding priority question](../specs/BOUNDED_SIMULATED_ACCOUNTING_EPISODE_PROGRESS_V1.md).

Final connected validation: **249 PASS, zero failures/errors/skips**, through
`./scripts/pt -m pytest`, in these distinct populations:

- New simulated episode-progress controls: 22.
- Offline episode session: 26.
- Initial Accounting source: 27.
- Retained Exit/cursor publication recovery: 18.
- Existing explicit episode continuity: 29.
- Exit restore integrity: 9.
- Existing Exit producer binding: 9.
- Occupied Scope continuity: 11.
- Occupied management dispatch: 25.
- Full-close handoff: 19.
- Existing decision-path atomic restart: 7.
- N5 runtime orchestrator: 17.
- Existing one-shot SideState/confirmation cursor join: 15.
- Canonical futures Accounting binding: 15.

The new long/short controls increase an actual Accounting position from 0.4 to
0.8, then partially reduce to 0.4. The updated average equals the original owner's
position basis, while opening time/episode key, initial source bytes and cursor
bytes remain unchanged. Identical history is idempotent. Reload verifies the
current archive and preserves current average instead of resetting to initial
source price. Subsequent real current-core decisions retain TimeExit behavior
when that signal is the highest applicable mandatory class.

A controlled equal-market price-basis intervention changes the actual original
ProfitProtection producer from triggered to untriggered, for both directions.
The pre-update branch selects the actual `profit_protection_exit` consumer class.
Separate long/short controls arm a real pending TimeExit first, advance average,
reload and retain the exact obligation through the following EXIT decision.

Two actual N1 controls run source increases/reductions before the existing N1/S7/
DP/full-close scenario. An incorrect observed 0.8 quantity rejects before creation
of the governed ledger or Exit mutation; the verified remaining 0.4 reaches the
original reduce-only full-close envelope with no permit/POST. No source quantity
is substituted for the observed ingress. Future fill progress blocks an earlier
market observation without committing Exit state.

Missing new time, full close, consistent-but-rewritten fill history and stale
handle reject without overwriting owner state. Contract multiplier, initial equity
and writer changes also reject despite a matching fill-body prefix. A competing
writer injected after archive retention preserves its newer pending obligation;
the losing update blocks its handle. An injected state/marker interruption blocks
reload without repairing the partial owner publication. Ordinary decision commit
still cannot change entry price. Explicit session update/reload keeps its original
attempt allowance; an interrupted technical source update requires review.

The initial 13-case focused run had four failed assertions: two used the wrong
existing ProfitProtection enum spelling, and two assumed TimeExit would always
dominate after a large average shift. The former expectations were corrected;
isolated TimeExit cases now avoid an additional Adverse trigger. A dedicated
countercase retains the real observed interaction: pending TimeExit identity and
signal remain active while the existing higher-priority Adverse class produces
final REDUCE. This is recorded as an unresolved domain acceptance question, not
hidden by the green regression control or approved as desired end-system behavior.
Neither priority nor Scope formula was changed to make tests pass.

Intermediate focused and 65-case connected runs are not added to the final 249
population. Scoped Ruff lint/format, runtime isolation, whitespace and final
source/report readback pass. JUnit and exact working-file hashes are retained in
the local phase-7 report. Phase-6 physical SIGKILL testing remains bound to its
technical pre-N1 checkpoint; it is not a new physical source-update crash proof.
Separately reproduced phase-2 baseline failures remain preserved there.

No source authentication, naturally occurring fill attribution, full confirmed-flat
lifecycle, all-owner transaction or system readiness is claimed. Existing Accounting
kernel, Exit producers/EntryExit rules, Scope formulas, configuration, original
ledgers and historical evidence are untouched. Changes remain in the explicit
composition/state-adapter boundaries. No credentials, venue requests, actual
orders, capital actions, activation, service installation, commit, push or publication.
