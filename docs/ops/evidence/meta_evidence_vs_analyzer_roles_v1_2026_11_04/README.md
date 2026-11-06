# Meta evidence projection versus numeric analyzer — 2026-11-04

Pin ff9d11380; Blueprint 70. Read-only continuation of Runbook-first role review.

M6's subordinate contract explicitly declares CANONICAL_META_LEARNING_V1_EXECUTOR
NOT_INVOKED_IN_M6. Current code imports the analyzer's constants and records its
reference/schema, while canonical_analyzer_invoked remains false. It projects M5
slices into typed Meta evidence; source_experiment_ids comes from the search slice
and support_count is its length. Repeated-pattern text describes challenger
classification/failure count. Predictive features, uncertainty and optimization
family can remain UNKNOWN_UNAVAILABLE. Such a reference is not execution of the
analyzer, and a support_count is not a numeric predictive association sample.

The Phase11 analyzer instead takes caller-supplied MetaLearningExperimentUnitV1
records. Each unit binds experiment identity, research family/hypothesis/search
space/parameter region, regime, time horizon, market universe, robustness statuses
and backtest metrics. Optional parameter_stability is a finite supplied scalar;
its numeric producer/measurement definition is not established by this DTO.
Optional later_outcome binds named metric/value/surface/time; the current temporal
validator requires evidence_created_at <= observed_at <= analysis created_at.
Comparison SSOT partitions comparable cohorts before analysis.

For metric association, an experiment contributes one pair to the bucket named
by its later outcome only when the backtest has that same metric key. It counts
same/opposite signs, not a correlation coefficient or causal effect. A zero
value remains a paired observation but does not count as same/opposite sign.
For robustness-gap association, each test_id bucket counts experiment-level
status/gap pairs. Stability counts known supplied stability observations, not
missing observations. Thus experiments, metric/test-specific pairs, input bars
and fills are different sample units; they must not be combined to satisfy a
threshold. Current per-bucket/missingness guards have a basis in these question
and sample contracts, but those guards do not prove metric production or the
original numerical meaning of stability. Original master Phase11 asks research
process questions; it does not supply a stability formula to invent here.

M7 converts M6 support_count into bounded research_budget_units via its existing
clamped rule and can preserve an opaque hypothesis_pattern_ref. It does not
thereby create Phase11 research_proposals, an experiment sample or a measured
search result. M7's spec prohibits synthesizing UNKNOWN fields. M8 later replay
lineage cannot make these quantities interchangeable.

A separate explicit Phase11→M4→Search input already exists and is documented in
Blueprint39 evidence. That controlled synthetic case demonstrated a supplied
proposal changing actual candidate selection; its scope is retained at its
original revision, not re-tested or expanded to a natural loop here. Exact-symbol
src/scripts search in this scope locates the Phase11 builder definition, but no
call constructing its units/request outside the owner. This is a bounded caller
finding, not global absence or proof the analyzer should be installed in M6.

Smallest coherent integration candidate: reuse the existing explicit priority
input after proving a suitable experiment-unit supplier and proposal semantics.
Do not wire M6 support_count or opaque M7 pattern text into numeric analysis by
name, and do not treat sample counts as search-budget units. No new schema,
formula, automatic scheduler, runtime source mutation or activation in this scope.
[Sources](sources.json), [bounded calls](bounded_analyzer_calls.json),
[receipt/checks](receipt.json). Whole feedback function remains incomplete.
