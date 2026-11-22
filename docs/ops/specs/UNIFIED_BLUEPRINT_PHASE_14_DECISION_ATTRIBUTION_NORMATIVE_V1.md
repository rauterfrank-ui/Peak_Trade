---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_14_DECISION_ATTRIBUTION_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 14 decision attribution evidence boundary
capability: UNIFIED_BLUEPRINT_PHASE_14_DECISION_ATTRIBUTION_V1
last_updated: 2026-11-22
---

# Unified Blueprint Phase 14 — Decision Attribution Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_14_DECISION_ATTRIBUTION_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP=true
```

Machine-readable closure:
`config/governance/unified_blueprint_phase_14_decision_attribution_v1.json`

Canonical boundary owner:
`src/governance/unified_blueprint_decision_attribution_evidence_v1.py`

## Purpose

Condition realized N_BARS outcomes on **existing** MV2/Double-Play decision references as
evidence only. Compose references; do not duplicate trading-decision or Cap 2.3 selection
ownership.

## Chain

```text
EXISTING DECISION REFERENCES (DecisionEvent / Double-Play bundle refs)
  + REALIZED N_BARS OUTCOME (DDO evaluation engine)
  + OPTIONAL MI forecast/evaluation references
  → TYPED DECISION ATTRIBUTION EVIDENCE (EVIDENCE_ONLY)
  → EXISTING learning_outcome_evidence_ingest_v1 (optional, proven consumer)
  → STOP
```

## Reuse (no parallel authority)

- `evaluation_engine_v0` — offline outcome/attribution/counterfactual bundle
- `real_outcome_horizon_contracts_v1` — N_BARS lookahead guards
- `learning_outcome_evidence_ingest_v1` — learning state ingest
- `decision_attribution_query_v1` — MI evidence reference query

## Non-goals

- Trading-decision mutation or MV2/Double-Play authority duplication
- Cap 2.3 selection/rerank
- Promotion, runtime apply, productive configuration, execution/external effects

## Verification

- `tests/governance/test_unified_blueprint_decision_attribution_evidence_v1.py`
- `tests/governance/test_unified_blueprint_phase_14_decision_attribution_v1.py`

## Original attribution at the learning handoff — 22 November 2026

The existing composer, optional learning adapter, original DDO ingest, durable
ledger and replay remain the owners. At baseline
`f59044aeeaee250d9f37aaee9a20dc9691d78665`, the adapter checked ATTRIBUTED
status but did not bind the supplied evaluation bundle to its attribution body.
The underlying ingest already validates native records, provenance, original
ledger content, configuration pools, ordering and idempotency. Those checks do
not establish that this particular attribution names the consumed bundle.

Two valid native ETH measurement bundles can retain the same decision and
evaluation record IDs while differing in original outcome, return or source
provenance. A foreign bundle already stored in the ledger was therefore
accepted under the other attribution. Missing or contradictory attribution
bodies and a different stored DecisionEvent with the same ID also passed.
The corrected baseline reproduced thirteen invalid learning admissions and
six false-positive replays; eight controls already passed. An earlier fixture
preflight used the wrong ledger-path property and is not semantic evidence.

Before calling the existing learning consumer, the adapter now checks the body
and result digests, existing evidence-only boundary, native bundle validation,
all three record/decision references, original outcome and horizon, existing
Phase-14 fingerprint and derived evidence ID. It binds the decision content
hash, selected-instrument reference and configuration reference to the original
DecisionEvent read from the ledger. Recomputed digests alone do not establish
these joins. The original ingest still checks that all three evaluation records
are actually stored and still owns the append, provenance admission and reducer.
The existing external-effect invariant is checked before invoking that consumer.
The existing repr-based digest includes the inner horizon dictionary's insertion
order. Admission reconstructs that original builder order after sorted JSON
serialization, without dropping fields, changing values or changing the digest
algorithm. A three-case JSON rejection in the first hardening version was
reproduced and corrected; it is retained as an intermediate regression diagnosis.

Replay now compares the complete recomposed result using the existing canonical
JSON value representation, including evaluation records, MI reference query,
body, digests and reason codes. Equivalent JSON arrays and native tuples remain
equivalent. Comparing cached IDs/digests alone is insufficient. This replay has
no ledger input and does not independently certify archived sources.

The regression contract is
`tests/governance/test_decision_attribution_learning_binding_v1.py`: 27 cases
cover the thirteen admissions, six replays, six matching native/JSON packets
with actual learning append, cold read and idempotency, and two existing
non-attributed guards. Six complete original result/ingest/readback packets and
six full synthetic ledger files remain byte-identical. All 103 selected offline
attribution, Phase-25, evaluation and learning-ingest cases pass without skips.
Network access is denied; no business or research session is started.

The policy inventory admits only the exact original/current source-hash pair
through its existing development-delta mechanism, with six additional admission
and preservation probes. Rehashing another implementation, missing bindings,
wrong parents and altered authority remain rejected; frozen inventories stay
unchanged. The existing reviewed-policy-set test omitted the already admitted
D01/D02 checker. This stale expectation was reproduced using original baseline
owner/binding bytes and now includes that existing delta and the new exact pair.
The original POLICY_SOURCE_DRIFT diagnosis before registration remains evidence
of the intact guard, not an unresolved final failure.

The September contract date is historical intent. Available local Git history
for this owner begins with the frozen November import; earlier construction
history is not independently reconstructed here. Current call-site inspection
finds this learning adapter in offline tests, not a productive host or scheduler.
LearningState preserves original opaque economic/decision/safety labels and
LOG_RETURN provenance; this is not account profit, model fitting, improved
decision quality or a causal-effect estimate. Phase-14 and LearningState retain
their different fingerprint algorithms. No digest, ID, numerical formula,
stored original, productive reducer, BTC source, freeze tag or authorization
changes. Optional MI query construction and independently observed source/time
authenticity are separate questions; no overall chain or operating acceptance
is inferred from this bounded handoff proof.

## Optional MI query joins — 22 November 2026

The [MI query contract](MARKET_INTELLIGENCE_FORECAST_CALIBRATION_OFFLINE_STACK_NORMATIVE_V1.md#optional-decision-attribution-query-binding--2026-11-22)
now checks explicitly supplied decision, selected-instrument, forecast and
calibration references. Phase 14 forwards the actual outcome reference already
produced by the original evaluation owner; it does not create a second outcome
or numerical truth. A calibration naming another original measurement rejects
before this composer publishes its result. A native receipt without an outcome
keeps that absence and is not filled from a later evaluation. The query remains
optional and evidence-only. Native validation failures or contradictory joins
raise their existing ValueError-style errors; they are not converted into a
successful or invented disposition. Prior learning-adapter and replay hardening
remain in place. The exact source admission is advanced only to this reviewed
composition delta; frozen policy objects and authority constants remain intact.
The link consistency is distinct from observed historical forecast use,
independent source/time authenticity, numerical learning and productive apply.
