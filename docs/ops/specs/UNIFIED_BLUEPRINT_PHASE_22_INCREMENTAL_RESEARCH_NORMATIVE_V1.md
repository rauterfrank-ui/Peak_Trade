---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 22 incremental information research (B0–B5)
capability: UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_V1
last_updated: 2026-11-22
---

# Unified Blueprint Phase 22 — Incremental Research Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Prerequisite: Phase 21 Loop A `PROVEN` on `origin&#47;main`.

Owners (offline research; AUTHORITY=NONE):

- Information-set identity: `src/learning/market_intelligence_forecast_calibration_offline_stack_v1/incremental_information_set_v1.py`
- Incremental research evidence: `src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_22_incremental_research_evidence_v1.py`

Established Optimization reuse (unchanged ownership):

- MI-enriched M4 intake: `src/experiments/canonical_optimization_universe_mi_enriched_m4_intake_v1.py`
- Experiment plane: `src/experiments/canonical_optimization_universe_experiment_plane_v1.py`
- Meta-learning ingest projection: `src/experiments/canonical_meta_learning_ingest_v1.py`

Integration closure:

`config/governance/unified_blueprint_phase_22_incremental_research_v1.json`

## Verification

- `tests/learning/test_incremental_information_set_v1.py`
- `tests/learning/test_phase_22_incremental_research_evidence_v1.py`
- `tests/governance/test_unified_blueprint_phase_22_incremental_research_v1.py`
- `prove_unified_blueprint_phase_22_incremental_research_v1`


## Actual immediate predecessor — 2026-11-04

Active stage processing checks supplied predecessor stage_id against the existing
immediate-predecessor mapping before projection/plane work. Baseline cannot consume
a predecessor; missing predecessor remains insufficient. The early DEFERRED B5
route has no comparison/plane execution and stays reachable. Ordering alone does
not prove this edge. Numeric score/dataset/window equivalence and full predecessor
content remain distinct proof questions.
[Verification](../evidence/incremental_immediate_predecessor_binding_v1_2026_11_04/README.md).

## Original predecessor content admission — 2026-11-21

An active stage admits a supplied original predecessor before projection or the
existing M4 plane: native schema, authority NONE, disposition vocabulary and the
complete stored stage-body digest must hold. Its information set and dataset
identity are reconstructed by their existing native metadata builders. Original
IDs/digests and bodies must agree, and stage/predecessor, dataset information-set
reference, horizon and behavior-contract version must be internally consistent.
Rehashing an inconsistent outer record does not repair a nested identity or join.

No predecessor replay, research execution, new record owner, ID formula or numeric
classification rule is introduced. B0 still forbids a predecessor, absence remains
INSUFFICIENT_EVIDENCE, and the early B5 DEFERRED route still consumes no predecessor
or plane. Existing consistent original/JSON packets and their output digests stay
unchanged; stored records are not rewritten.

These checks establish intrinsic record integrity and declared reference
consistency, not source authenticity or measured incremental value. Dataset
temporal flags remain the metadata builder's declarations, not evidence of actual
training/OOS execution. This legacy wrapper still uses caller-supplied M4
champion/challenger scores; it does not establish their equality to a measured
immediate-predecessor score. A different internally consistent predecessor horizon
is not newly prohibited: cross-stage sample/window/target comparability remains
unproven here. The separate paired-market research owner is not replaced or
certified by these checks. Failure-memory labels and formulas are unchanged.

[Offline verification](../../../tests/learning/test_incremental_predecessor_content_admission_v1.py)
rejects altered or crosswired original predecessors before the actual M4 consumer
and preserves valid ordered, JSON, missing-family and deferred cases.

## Separate paired-market clock admission — 2026-11-22

The separate paired-market owner compares B0 price/flow and B1's additional OHLCV
proxy on the same original market cases. It already reads original freezes,
contexts and measurements, enforces target/unit/source-generation consistency,
fits the existing chronological prefixes and computes LOG_RETURN holdout RMSE.
It does not use the legacy wrapper's supplied champion/challenger scores.

Its existing forecast/evaluation, FIT/HOLDOUT boundary, label-availability and
sequential nonoverlap checks now use the source decoder's exact clock ordering.
Existing UTC admission remains in force, including UTC-offset-zero inputs. Case
sorting and strict time uniqueness use each original bound context's `as_of`,
not a rounded display string. A late FIT or holdout label remains explicitly
LABEL_NOT_AVAILABLE_AT_CUTOFF without a numeric target and prevents fitting;
contradictory forecast/split/overlap inputs reject before the next consumer.

The existing `context_as_of` case/matrix field retains its canonical microsecond
display for artifact compatibility. It is not the chronology authority; full
original time is available through the bound context/job and its digest. Distinct
pending instants may share that display while retaining distinct original
identities. They remain incomplete evidence, not newly admitted training samples.

No new time tolerance, source-age limit, feature, fitter, validation fraction,
coefficient/RMSE calculation, record schema or digest/ID formula is introduced.
The Meta handoff already reproduces the original comparison before routing;
measured results remain a Learning-Research question and plan, while missing,
pending or blocked comparisons retain their unresolved route. A single
chronological holdout is not independent quality, economic PnL, promotion or
productive apply. Original artifacts are not rewritten or retrospectively
time-certified by this change.

Original owners:

- `src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_22_paired_market_research_v1.py`
- `src/meta/learning_loop/paired_market_representation_meta_v1.py`

[Offline boundary and full-packet verification](../../../tests/learning/test_paired_market_exact_clock_admission_v1.py)
uses synthetic original jobs and retains the existing source admission APIs.

## Recorded cohort declaration and original-clock binding — 2026-11-22

The recorded representation adapter already binds its declared cohort to original
freezes, contexts, measured predecessor outcomes and successor plans/links. The
Meta owner reproduces the stored comparison before forming its typed question,
router decision and Learning-Research plan. These content joins remain in place.

The successor and cohort producer now check the existing hourly grid against the
original input's full fractional second. An instant 1 or 999 nanoseconds after an
exact hour is not an hourly start. Canonical plan serialization still follows the
existing producer; the admission check runs before that serialization can discard
the fraction. The Meta adapter compares each declared start with its original
frozen target and each successor request using the same exact source clock.
Resealing a conflicting declaration cannot make its start equal to the original.
UTC admission is retained; zero fractions and UTC-offset-zero spellings remain
equivalent. Existing spacing, split, feature and measurement rules are unchanged.

Original owners:

- `scripts/ops/run_offline_learning_representation_sequence_v1.py`
- `scripts/ops/route_offline_paired_market_representation_meta_v1.py`

[Focused offline checks](../../../tests/ops/test_representation_cohort_clock_binding_v1.py)
reject contradictions before the next original consumer without changing stored
files. The focused Meta fixture substitutes capture advancement with native
calibration readback; it is not independent evidence of the capture adapter.
The existing [synthetic integration checks](../../../tests/ops/test_capture_offline_learning_representation_context_v1.py)
cover actual capture/readback, comparison, Meta, follow-up and cold replay with
fixture HTTP responses and a network-rejecting cold replay.

This scope certifies neither all other timing relations in the cohort/follow-up
scripts nor source authenticity, independent research quality or productive
apply. Original stores, schemas, digest/ID formulas and operational authority are
unchanged. No operational collection or research campaign is started.

## Follow-up declaration and original-answer chronology — 2026-11-22

The follow-up adapter already reconstructs the original Meta handoff, checks its
research purpose/lineage and retains the target contract, split and feature
versions. A later repetition reads the stored plan and rebuilds its complete
answer from the original parent and follow-up cohorts. The construction originates
in commits `03871e22dd00be319a9926a50bc6d8b2f3814826` and
`02248b61d0b94e99d80a9958a37994ed2d86c99e`; these content joins remain unchanged.

Its five existing temporal gates now preserve source-clock precision: admission
to the hourly grid, a context strictly later than the parent's evaluation,
declaration at or after schedule verification, replay of that declaration, and original
answer readback. The existing order is parent evaluation < new context <= forecast
verification <= declaration < first window. Equality at the parent/context or
declaration/window boundary remains forbidden; equality at verification/declaration
remains allowed. A truly later context within the same microsecond is no longer
rejected as simultaneous. A declaration before verification by 1 or 999 ns cannot
reach the plan writer or answer consumer. The hourly check uses the raw inputs
before the existing plan serialization can discard a fraction.

UTC admission, equivalent zero fractions/UTC-offset-zero spellings, spacing,
canonical plan bytes, IDs/digests and numeric methods retain their existing rules.
The adapter still records a research answer with independent_quality_proven and
productive_apply_authorized false. Temporal consistency grants no operational
authority, independent predictive quality or account PnL.

[Focused boundary checks](../../../tests/ops/test_representation_follow_up_clock_binding_v1.py)
use native recorded contexts, freezes and measurement schedules with an explicitly
supplied verified-parent contract. They do not independently certify upstream
Meta admission. The existing synthetic capture/Meta/follow-up/cold-replay test
separately exercises those actual joins. The separate measurement/capture owner's
timing gates and other causal paths remain outside this change. Historical stored
records are not rewritten or retrospectively certified.
