---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_23_META_DUAL_ROUTING_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 23 Meta-Learning dual routing
capability: UNIFIED_BLUEPRINT_PHASE_23_META_DUAL_ROUTING_V1
last_updated: 2026-09-26
---

# Unified Blueprint Phase 23 — Meta Dual Routing Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_23_META_DUAL_ROUTING_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
LOOP_C_PROVEN=false
```

Prerequisite: Phase 22 `PROVEN_COMPLETE` on `origin/main`.

Owners (offline; AUTHORITY=NONE):

- Typed routing envelope: `src/learning/deterministic_decision_outcome_v0/meta_evidence_v1.py`
- Dual router: `src/experiments/canonical_meta_evidence_dual_router_v1.py`
- Optimization consumer (reuse M7): `src/experiments/canonical_meta_to_optimization_feedback_v1.py`
- Learning research adaptation input: `src/experiments/canonical_meta_to_learning_research_adaptation_input_v1.py`

Closure: `config/governance/unified_blueprint_phase_23_meta_dual_routing_v1.json`

## Verification

- `tests/experiments/test_canonical_meta_evidence_dual_router_v1.py`
- `tests/learning/test_meta_evidence_v1.py`
- `tests/governance/test_unified_blueprint_phase_23_meta_dual_routing_v1.py`
- `prove_unified_blueprint_phase_23_meta_dual_routing_v1`
