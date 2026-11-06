# Numerical feedback control aligned to declared nonannual Sharpe — 2026-11-04

Source pin `af0d0bdf3`. Corrects an imprecision in our earlier Blueprint 78
control source. Its hourly return data was passed to the full stats owner using
the default 8760 annualization, but the target canonical robustness policy declares
MEAN_OVER_SAMPLE_STD_NO_ANNUALIZATION. The common scaling leaves the split collapse
ratio and the observed region-selection effect unchanged; it does not make the
original metric labeling exact. Historical evidence is preserved, not overwritten.

The controlled test helper now calls the same existing stats owner with explicit
periods_per_year=1. Both memory Sharpe and supplied split Sharpes use that explicit
unit. No production adapter guesses a source's frequency or risk-free convention;
no global stats policy, full-map CAGR semantics or natural outcome is changed.

The new semantic assertion compares the declared policy and the source Sharpe to
mean/sample-standard-deviation on the known return array. It fails against the
original helper source. Train Sharpe changes from 77.85632371783784 to
0.8318439070608391; the ratio is sqrt(8760). Before/after full actual Meta/Search
records are retained. Both controls change the actually PROPOSED region from
fast10/slow50 to fast10/slow100 at equal budget. Both no-collapse countercontrols
emit no parameter-region proposal. One region proposal remains in each collapsed
case. All 90 connected tests PASS (the previous 89 plus the semantic regression).
Ruff/format PASS. Old recorded metrics are not rewritten or retroactively certified.

[Alignment summary](alignment_summary.json), [original control source](control_before.py.txt),
[before feedback](before_computed_feedback.json), [aligned feedback](after_computed_feedback.json),
[before no-collapse control](before_no_collapse_feedback.json),
[aligned no-collapse control](after_no_collapse_feedback.json),
[patch](change.diff), [test XML](tests.xml), [receipt/checks](receipt.json).

Generic source identity/metric-definition labels do not prove that a producer
actually used matching units. The adapter's structural checks and content integrity
are not a universal metric-semantics verifier. Source-specific binding remains
required. Shared synthetic trial data, ancillary fixture identities, short-name
Search control schema, no natural profitability proof and no automatic next
canonical experiment execution remain explicit. Existing native split observations
and consumer study retain their own distinct inputs. No original ledger mutation,
new activation, policy threshold, M6 analyzer join, account/order/service or push.
