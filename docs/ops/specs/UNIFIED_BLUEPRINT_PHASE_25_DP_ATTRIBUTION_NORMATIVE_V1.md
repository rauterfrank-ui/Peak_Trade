---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_25_DP_ATTRIBUTION_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 25 DP Attribution evidence
capability: UNIFIED_BLUEPRINT_PHASE_25_DP_ATTRIBUTION_V1
last_updated: 2026-11-22
---

# Unified Blueprint Phase 25 — DP Attribution Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_25_DP_ATTRIBUTION_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
ATTRIBUTION_EVIDENCE_ONLY=true
COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP=true
```

Prerequisites:

- Phase 24 `PROVEN_COMPLETE` on authorized baseline
- Phase 14 decision attribution compose boundary `PROVEN_COMPLETE`

Canonical compose owner (offline; AUTHORITY=NONE):

`src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_25_dp_attribution_evidence_v1.py`

Typed evidence schema: `attribution_evidence_v1`

## Normative reference bundle

```text
ATTRIBUTION_EVIDENCE_V1 = {
  market_context_ref(t),
  selected_future_ref,
  mv2_dp_decision_ref(t),
  side_state_ref,
  configuration_ref,
  realized_behavior_ref(t+N),
  quality_refs
}
```

Phase 25 **references** existing owners only:

- `market_context_v1` — MARKET_CONTEXT at decision PIT
- Phase 14 `build_decision_attribution_evidence_v1` — MV2/DP decision + realized N_BARS outcome
- `realized_behavior_v1` — REALIZED_BEHAVIOR(t+N) join backbone

## Non-goals

- MV2/Double-Play trading-decision mutation or authority duplication
- Cap 2.3 reranking/reselection
- Trading gates, risk/sizing, execution/post/wire changes
- Optimization/meta-learning promotion
- Phase 26 Final DoD (forbidden from Phase 25 scope)

Closure: `config/governance/unified_blueprint_phase_25_dp_attribution_v1.json`

## Verification

- `tests/learning/test_phase_25_dp_attribution_evidence_v1.py`
- `tests/governance/test_unified_blueprint_phase_25_dp_attribution_v1.py`
- `prove_unified_blueprint_phase_25_dp_attribution_v1`

## Original measurement and exact declared PIT binding — 22 November 2026

The normative reference-only construction already exists in the frozen source.
The available local path history begins with its frozen-system import in
`9397d04a37d527a8316b3e44ef4f80b4ef44db7a`; the earlier development history is not
reconstructed here. On the current baseline, Phase 25 calls the original Phase-14
decision-attribution owner and consumes validated MARKET_CONTEXT and
REALIZED_BEHAVIOR records. Compose, inspection and replay are implemented.
The inspected callers are offline tests and governance/reference checks; no
productive invocation or automatic learning return is established by this review.
Historical `PROVEN_COMPLETE` labels remain bounded closure declarations.

The compose boundary now requires the supplied behavior's `actual_outcome_ref`
to equal the evaluation observation's original measurement reference before
Phase 14 is invoked. Matching context, instrument and horizon do not make two
different original measurements interchangeable. This remains true for opposite
returns, proportional endpoint prices with the same return, or identical prices
with different source provenance. A matching observation/behavior pair remains
admissible; the adapter does not choose one source, overwrite measurements or
recompute their prices.

The existing inequalities context time ≤ decision time and, with a supplied
behavior, context time ≤ horizon start now compare the complete original UTC
precision through nine fractional digits. Original `Z` syntax, zero-fraction
equivalence and inclusive equality remain unchanged. Newly rebound serialized
declarations whose context is later than their horizon are counterevidence;
valid hashes do not authenticate their chronology or a new source observation.
Contradictions reject without reaching the Phase-14 evaluation consumer. Missing
behavior for an otherwise valid complete horizon remains explicitly insufficient.

These joins preserve original Decision/selection/SideState/configuration
references, schemas, IDs/digest formulas, quality-reference reporting and replay.
The existing selection reference is transported without inventing an instrument
mapping. LOG_RETURN, close-path excursion and realized volatility retain their
original units and estimators. Classical MFE/MAE and regime transition remain
explicitly unresolved where their original owners mark them so. A later price
return does not establish account profit, decision-rule quality or causal effect.

[Original-evidence and clock counterexamples](../../../tests/learning/test_dp_attribution_original_evidence_binding_v1.py)
use synthetic typed DecisionEvent fixtures, original O4/context/measurement
builders, the actual Phase-14 evaluation owner and original inspection/replay.
They do not execute the trading Core or authenticate venue observations.
The inspector remains a digest/reference reader without the original request;
it does not independently re-establish PIT or source truth. Old evidence is not
rewritten or retroactively certified. `pit_join_proven` records the bounded
declared compose checks, not observed operation, independent source timing or
complete system semantics. Trading, productive learning, apply and operating
authority remain unchanged and absent from this adapter.

101 targeted offline cases pass, including 31 new counterexamples/controls and
70 existing attribution, behavior, exact-time and governance cases. The original
adapter failed 13 of the new expectations: nine inputs were incorrectly
ATTRIBUTED and four contradictory future-context inputs were INSUFFICIENT
instead of REJECTED. Eighteen controls already passed. Fourteen complete original
request/result/inspection/replay packets remain byte-identical, including a valid
missing-behavior result. Network access is forbidden in the test process and the
compatibility comparison. No operating or research run was started.
