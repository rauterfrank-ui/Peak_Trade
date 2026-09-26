---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_14_DECISION_ATTRIBUTION_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 14 decision attribution evidence boundary
capability: UNIFIED_BLUEPRINT_PHASE_14_DECISION_ATTRIBUTION_V1
last_updated: 2026-09-26
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
