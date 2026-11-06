# Specialized research as numeric supplier candidates — 2026-11-04

Pin d511f5e46. Runbook-first continuation, Blueprint 72. This is a source/contract
review, not a new campaign or competing research authority.

## Existing calculation path and original scope

The cross-sectional single-slot research orchestrator computes version-bound
panel scores/rankings and rotation events. Its backtest adapter simulates trades,
costs, equity and delegates statistics to the existing backtest owner. Its economic
wrapper binds dataset/period/cost/policy evidence and calls existing Monte Carlo
and stress owners. This is an actual static numeric calculation path, not merely
an ACK/hash chain. It evaluates its declared research strategy; it does not by
itself supply attribution to today's canonical MV2/Double-Play decisions or the
B-stage MI forecast/calibration research target. Broader research strategies and
the canonical-core learning target can coexist without silently substituting one.

The historical scope/binding/closeout documents describe a specific 2024 full-panel
cohort and a completed negative economic result, with primary-only parameters and
no same-binding rescue/retry. Those are historical claims at the recorded merge,
not today's reverified execution. The exact documented original evidence directory
is absent at that local path; no broad or external search was started. Existing
old instrument filters/cohort constraints are not a new global policy; the current
common-asset alignment remains a separate target. STEP29M's current Runbook
contract separately consumes persisted post-selection output, not these panel
rankings as selection authority. No runner or account source was invoked.

## Producer meaning versus consumer expectation

[Field-level findings](field_role_findings.json) bind concrete definitions. Trade
PnL/expectancy and accumulated costs use absolute quote-currency amounts; net
return is a fraction, and turnover is a rotation event count. Funding's presence
in binding metadata does not calculate funding: the inspected result has no
funding_drag and the evidence projection preserves None. Do not silently fill it.
Stats use the default hourly annualization (8760); preserve frequency/version and
not just a Sharpe field name in any proposed bridge.

The field named gross_return uses total_return from the same cost-bearing equity
curve, starting at its first recorded point. It is not a separately computed
pre-cost gross return. If the first recorded point follows an entry cost, its base
also differs from initial_cash used by net_return. The separate accounting owner
has explicit gross/entry/exit/net components; that is a reuse candidate to inspect,
not proof this projection has already consumed reconciliation. No historical
result was relabeled or recomputed.

The producer's max_drawdown is nonpositive. The canonical robustness owner's
internal max_dd is a nonnegative magnitude and its risk gate checks an upper
limit. Raw rename/copy would change meaning. An explicit governed conversion,
matching observation source and metric-version contract are needed before use.

This research wrapper's walk_forward_results are chronological slices of one
completed equity curve. They contain net returns/trade/bar counts, and the wrapper
counts nonnegative periods (including training) for its pass ratio. The canonical
suite's WALK_FORWARD consumer instead requires train/test Sharpe observations per
window plus sample size, and explicitly states the reoptimization runner is not
bound. These artifacts cannot be made equivalent by renaming a key. Empty slices
return zero in the older scoped producer; do not reinterpret that as sufficient
measured OOS evidence at the newer consumer.

Parameter sensitivity is explicitly BOUND_PRIMARY_ONLY_NO_SEARCH. The economic
wrapper supplies parameter_robustness_pass=True and neighbor degradation 0.0,
but no neighbor sweep is run in this path. This is a scoped convention requiring
care in interpretation, not a measured parameter-stability source for Phase11.
No new formula, stricter gate or retroactive verdict was introduced.

## Smallest supported next step

Reuse existing numeric owners for their declared strategy/dataset rather than
build another metrics engine. Identify the chosen hypothesis/candidate and desired
question, then bind units, signs, frequency, horizon, dataset/split identity and
explicit missingness to the existing input owner. Preserve research-only rankings
and fixed historical cohorts. Data-bearing output exists, but the exact canonical
observation/Meta-unit adapter is not yet ratified; mere structural compatibility
would not close the causal loop. Independent core-native suppliers remain to
investigate. [Sources/history/lookup](sources.json), [receipt/checks](receipt.json).
No runtime code changed; no new test or natural-run completion claim.
