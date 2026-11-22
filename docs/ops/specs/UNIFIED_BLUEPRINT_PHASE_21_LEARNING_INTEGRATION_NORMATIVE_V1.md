---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_21_LEARNING_INTEGRATION_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 21 Loop A conditioned Learning evidence integration
capability: UNIFIED_BLUEPRINT_PHASE_21_LEARNING_INTEGRATION_V1
last_updated: 2026-11-21
---

# Unified Blueprint Phase 21 — Learning Integration Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_21_LEARNING_INTEGRATION_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Prerequisite: Phase 20 `REALIZED_BEHAVIOR_V1` behavior join on `origin&#47;main`.

Loop A owner (offline MI/Learning; AUTHORITY=NONE):
`src/learning/market_intelligence_forecast_calibration_offline_stack_v1/loop_a_conditioned_learning_evidence_v1.py`

Established Learning writer/reader (unchanged ownership):
`mi_learning_evidence_ingest_v1` / `mi_learning_evidence_learning_export_v1`

Integration closure:
`config/governance/unified_blueprint_phase_21_learning_integration_v1.json`

## Verification

- `tests/learning/test_loop_a_conditioned_learning_evidence_v1.py`
- `tests/governance/test_unified_blueprint_phase_21_learning_integration_v1.py`
- `prove_unified_blueprint_phase_21_learning_integration_v1`

## Conditioned admission before the MI bridge — 2026-11-21

The existing context-at-or-before-forecast condition is now enforced before the
original MI bridge/calibration and store append, including the branch without an
outcome or realized behavior. Missing outcome is still explicit NOT_EVALUABLE;
it does not permit a future conditioning context. The optional behavior's context
reference and the existing context/evaluation bound are checked at the same
admission point. All time comparisons retain the original UTC-Z source precision.

This is a conditioned evidence reference, not proof that the original forecast
consumed these context features. No new equality requirement between the forecast
and context information-set IDs is introduced. Realized behavior is later outcome
evidence, not a decision-time signal or a new productive LearningState. Original
record identities, missing/insufficient semantics, writer/store/export ownership
and authority NONE remain unchanged. Existing MI learning records are not
rewritten or recalibrated on cold read; their historical chronology is not
retrospectively certified.

[Offline verification](../../../tests/learning/test_conditioned_learning_exact_clock_v1.py)
checks composer and real ingest boundaries, then persistence, idempotency, cold
read and export for valid original packets. No operational/research run is needed.

## Behavior binding to supplied original sources — 2026-11-22

At baseline `53d4ddd137a4a0358185c2245774c46bc6333e26`, the conditioned
composer, ingest, store, export and P5 consumer are connected. Context chronology,
native behavior identity and MI record-state admission are already checked.
The original behavior producer stores context identity and the complete declared
N_BARS horizon/window; these fields also exist in the frozen November import.
The conditioned consumer previously compared context ID and two non-null outcome
references, without binding the stored behavior horizon/window to its supplied
observation. A native later evaluation could therefore alias an earlier one
under the same context ID and actual outcome reference.

The existing composer now compares behavior instrument, information set and
observation time with its supplied context. When the original observation is
present, it also compares actual outcome reference (including missingness),
horizon kind, n_bars, bar specification, start/evaluation times, ordered bar
identities, close times and observation status/reason. Existing exact JSON value
and nanosecond clock owners are reused. Equivalent zero-fraction UTC instants
remain equal without changing either original string. Forecast and context
information-set IDs remain distinct; no new equality is inferred between them.

The gate runs after the existing MI bridge and its original errors, before a
successful conditioned receipt or store append. It does not recalculate behavior,
calibration or the original measurement. The existing non-null conflicting-outcome
error remains. Original-source counterexamples have 28 previously unblocked
composer/ingest admissions and nine passing controls, including equivalent time
representations. Three native probes reach ingest, cold get/list, export and P5
ADMIT: one fully native later-evaluation substitution and two resealed inconsistent
declarations. Self-consistent digests do not establish this cross-object join.

Verification: `tests/learning/test_conditioned_behavior_source_binding_v1.py`.
Eight full original input/receipt/ingest/replay/export packets and eight stored
files remain byte-identical. Missing outcomes, insufficient support, optional
measurements, zero fractions and later evaluations paired with their own original
observations remain supported. Classical MFE/MAE and transition remain explicitly
SEMANTICALLY_UNRESOLVED; direction-neutral close-path excursion is not relabelled.

Observation remains optional. A supplied behavior reference cannot manufacture
an absent original observation: that receipt stays INCOMPLETE/NOT_EVALUABLE with
no actual_outcome_ref, and no observation join is certified. Full original-source
comparison is limited to the objects supplied at this consumer. It establishes
declared consistency, not independent authenticity, correct interior O4 prices,
numeric behavior truth, historical forecast feature consumption or predictive
quality. The native behavior validator, Phase-25 attribution seam and behavior
snapshot meaning keep their separate boundaries. No new numerical learner,
authority, route, model update or productive apply is introduced. IDs/digests,
scoring methods (including the documented V1 linear 1-p meaning), units and
existing writer/reader ownership remain unchanged. No historical record is
rewritten, repaired or retroactively source-certified.
