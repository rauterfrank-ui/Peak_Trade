# Numerical execution supplier probes — 2026-11-04

Source pin `965b9255f`. Continuation of Blueprint 78, with no production-code
change. These are actual calls into existing local simulator/statistics/sensitivity
owners on explicitly synthetic bars. They are separate supplier studies; the
previous Search fixture candidate has not become an executed canonical experiment.

## Parameter names and actual consumer

The previous control uses `fast`/`slow`. The existing strategy binding permits
`fast_window`/`slow_window` and registered `fast_period`/`slow_period` aliases;
it rejects both short-name regions. Search is generic and did not promise that
these fixture keys were executable. No silent conversion or retroactive identity
rewrite was added. New engine studies declare native parameter names explicitly.

Actual source flow: configured strategy execution → family-specific suitability
agreement material → existing replay input → integrated offline replay → mapped
MV2 signal series → BacktestEngine. Every observed raw strategy signal equals
its supplied agreement cycle signal. Both engine signal digests equal their
respective actual MV2 replay signal digests. Different window values change the
raw signals, replay signals and engine input, so the configured strategy has a
causal role; replacing the final engine series with replay is not proof it is unused.
This older research path also constructs agreement-bound price paths; it is not
a direct authenticity or attribution proof for today's complete productive core.

## Sizing and actual numerical outcomes

256 hourly synthetic bars use close = 100 + 5 sin(i/12) + 0.01 i, with all required
context columns declared by the probe. Native fast window 10, slow 50 versus 100:
raw nonzero bars 181 versus 103. Under the original fixture risk 0.02, default
stop distance 0.02 requests approximately 100% notional, exceeding the 25% cap.
The existing sizer rejects; engine blocks 94 versus 54 attempts, no trades/return.
This is an explained fixture-policy interaction, not an implementation defect
or an instruction to raise a limit.

A separately declared synthetic scenario reduces risk per trade to 0.002, while
keeping stop/cap/costs otherwise fixed. Both variants execute two simulated trades.
Net returns: 0.007232849008339326 versus 0.006416554138432548. The second is lower;
no improvement is claimed. Raw engine Sharpe: 0.8809916112497889 versus
0.8502516695451859. Existing hourly supplier Sharpe: 4.315959830468766 versus
4.16536548667041. The basic stats owner uses factor 365 for Sharpe, whereas the
full hourly supplier recomputes Sharpe with 8760. Its CAGR still comes from the
basic 365-factor owner; do not call the entire metrics map frequency-correct.
Sortino is nonfinite in this probe and is explicitly represented as supplier
nonfinite evidence, never replaced with a fabricated numeric value.

Both cost flags retain `economic_interpretation_allowed=False`, funding is
NOT_BOUND, and the replay trace retains unresolved capital-risk evidence.
Simulated trades do not certify those unresolved boundaries, natural market
profitability, policy applicability, correct futures economics or productive readiness.

## Existing sensitivity owner, actually executed

The original 24-bar test fixture generates PIPELINE_PASS while all four points
are FAILED: the training split has 12 bars but the default strategy requires 50.
The record already preserves those failures. Pipeline status describes completion
of evidence collection, not successful numerical evaluation.

A separately declared native-name grid on 768 synthetic hourly bars has two
actually EVALUATED points, zero failed points. Minimum chronological split size
is 192, sufficient for the largest slow window. Both OOS net returns are
0.006799355001851109 and both have two trades; floating-point expectancy/PF
noise is not a meaningful superiority result. All grid points remain persisted.
The owner computes train/validation/OOS metrics internally, then serializes OOS
metric fields and split references only. It does not expose the full split-Sharpe
observations needed by the canonical robustness consumer. WALK_FORWARD remains
NOT_COMPUTED. Point result digest binds point/status/references, not numeric metric
fields; the enclosing full result digest binds the serialized points. Do not use
an isolated point digest as proof of numerical content or as canonical experiment ID.

## Reproduction and next boundary

[Probe source](probe.py), [summary](summary.json), [bar inputs](synthetic_bars.json),
[short-name denials](short_name_denials.json), [sizing rejection](original_sizing_rejection.json),
[original grid](original_small_grid_result.json), [native grid](native_grid_result.json),
[native grid configuration](native_grid_input_cfg.json), [receipt](receipt.json).
[Original sizing slow50](original_fixture_sizing_slow50.json),
[original sizing slow100](original_fixture_sizing_slow100.json),
[lower-risk slow50](explicit_lower_risk_synthetic_scenario_slow50.json),
[lower-risk slow100](explicit_lower_risk_synthetic_scenario_slow100.json)
contain actual provenance, signals, per-bar transitions, equity, trades and both
stats surfaces. Reproduction uses canonical Python from the repository root,
feeding the probe file on stdin. No network/account/service access is required.

Four direct engine studies, two real short-name denials, existing-size rejection,
four persisted failed grid points and two evaluated native grid points checked.
The native-grid bounds were corrected to the existing MA schema (a singleton
axis does not imply equal lower/upper admissibility bounds); earlier successful
engine studies were reused unchanged rather than rerun. Ruff and format checked.
No production source change or new pytest/full-suite claim.

Next binding must start with a native, explicit hypothesis/schema and actual
experiment identity, retain measured split metrics/units/frequency/finite status,
and feed existing Phase10/Meta owners without inventing missing outcomes. A
recorded reference does not recover discarded numbers. Historical fixed cohorts,
M6 projection boundary, original learning ledger, U04 and GAP-0370 are unchanged.
