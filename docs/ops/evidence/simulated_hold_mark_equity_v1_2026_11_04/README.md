# Simulated HOLD mark equity and drawdown consistency — 2026-11-04

Source pin 481c11d6a. Small internal correction after source-role reconstruction,
not speculative connection of distinct Learning ports or a new trading policy.

## Intended role, actual failure and minimum correction

The existing wallclock bridge acceptance contract requires a portfolio persistent
across cycles with PnL/equity/drawdown evidence. The simulated model already owns
mark-to-market and equity/drawdown reduction. Its non-actionable HOLD branch
updates unrealized PnL for the supplied price but returned before the equity reducer.
Thus metrics/snapshot exposed a new unrealized PnL alongside stale equity and peak
or drawdown. The actual replay adapter and V2 idempotent wrapper delegate to this
same branch; neither corrected the missing reduction.

The change adds one call to the existing equity/drawdown reducer immediately after
mark-to-market in the HOLD branch. It consumes no new data or policy and creates
no fill, cost, order, funding application or learning decision. Existing cash,
position and fees remain intact. Peak/drawdown now reflect observed hold marks,
including a later recovery retaining the worst observed drawdown. This repairs
consistency within this particular simulated model; it is not certification of
its financial conventions, the separate futures accounting owner or real execution.

## Validation and preserved boundaries

Six new regressions cover Long and Short across direct model, actual replay
adapter (controlled non-actionable result) and V2 idempotent wrapper. Each checks
current signed mark PnL, cash-plus-unrealized equity, peak/worst drawdown, snapshot
propagation and unchanged cash/position/fills/cost/funding/completed-trade counts.
All six fail before the change and pass after it. These controlled tests are not
a natural canonical-decision cycle or observed market run.

The connected package has 64 passes and one failure; a further 24 directly related
wallclock/economic pipeline tests pass. Total 88 distinct passing tests, including
the six new cases. The outstanding existing test is
`test_warmup_complete_true_features_ok_false_no_required_window_incomplete`:
its scope initializer raises `gge_base_geometry_unavailable:volatility_non_positive`
before portfolio processing. An isolated process reinstating the exact original
model method reproduces that failure. No unrelated core change or weakened test
was made. This is not an overall green-suite claim.

Controlled Long/Short entry-close paths without HOLD produce identical complete
fills/snapshot output before and after. Ruff passes for both changed Python files.
Original source, patch, failing/passing XML and comparison JSON are preserved. The
first baseline probe failed during alias import; its error is retained, then a
corrected process-local original-method probe produced the independent-failure
XML. Neither probe replaces source on disk or changes protected runtime data.

[Receipt/hashes/results](receipt.json), [before source](model_before.py.txt),
[patch](change.diff), [initial failures](before.xml), [connected result](after.xml),
[additional connected result](additional_connected.xml),
[baseline probe](baseline_probe.py.txt), [independent baseline failure](baseline_unrelated.xml),
[unchanged non-HOLD before](non_hold_before.json), [after](non_hold_after.json).
No session, service, network/account operation, original Learning ledger write,
activation, push or full outer-loop completion claim. U04/GAP-0370 remain deferred.
