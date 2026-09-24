---
docs_token: DOCS_TOKEN_V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1
status: active
scope: Concept v3.2 D26 platform-unified native vs candidate baseline evidence (read-only)
capability: V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1
last_updated: 2026-09-23
---

# V3.2 D26 — Platform-Unified Native vs Candidate Baseline Evidence Closure v1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1
PREDECESSOR_WP=V32_CURRENT_MV2_DP_CONCEPT_ALIGNMENT_V1
BOUND_ORIGIN_MAIN_SHA=8a16133d3bfacf1dad615e1b9bece598b559d48c
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_DECISION_AUTHORITY_CHANGED=false
P5_AUTHORITY_CUTOVER_AUTHORIZED=false
OPTIMIZATION_PRODUCTIVE_AUTHORITY=NONE
LEARNING_PRODUCTIVE_AUTHORITY=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
```

Machine-readable decision:
`config/governance/v32_d26_platform_unified_native_vs_candidate_baseline_evidence_closure_v1_decision_v1.json`

Code owner:
`src/governance/platform_unified_native_vs_candidate_baseline_evidence_v1.py`

## 1. Purpose

Close **D26** by composing existing CURRENT evidence contracts into one read-only
platform classification layer that makes silent candidate→native baseline substitution
**impossible**. No trading-core mutation, no promotion, no productive optimization join.

## 2. Implementation mode

```text
D26_IMPLEMENTATION_MODE=COMPOSE_EXISTING
NEW_CONTRACT_REQUIRED=false
```

| Layer | Owner |
| --- | --- |
| Native baseline classification | `classify_canonical_trading_decision_evidence_v1` |
| F1 research candidate classification | `classify_f1_parameter_research_candidate_result_v1` |
| DDO counterfactual classification | `classify_ddo_counterfactual_record_v1` |
| Optimization experiment candidate | `classify_optimization_experiment_evidence_v1` |
| Comparison join | `derive_comparison_context_identity_v1` |

Producer adapters (read-only, non-hot-path):

- `integrated_replay_native_baseline_evidence_adapter_v1` (governance package)
- `baseline_evidence_classification_adapter_v1` (F1 research execution package)

## 3. Influence classification invariants

| Class | Meaning |
| --- | --- |
| `NATIVE_BASELINE` | Positively no optimization/research/candidate parameter influence |
| `CANDIDATE_OR_COUNTERFACTUAL` | Influence explicit; baseline reference required |
| `UNKNOWN` | Missing or incomplete baseline/influence join — fail-closed |
| `INVALID` | Conflicting or forbidden influence markers on native path |

`UNKNOWN` and `INVALID` must never normalize to `NATIVE_BASELINE`.

F1 `BASELINE_CANDIDATE_ID` remains a **research counterfactual slot** — never `NATIVE_BASELINE`.

## 4. D26 / D27 adjudication (post-closure)

| ID | Status |
| --- | --- |
| D26 | `PROVEN_CURRENT` |
| D27 | `PROVEN_CURRENT` (global closure via post-D27 composition WP; F5 enforced on shadow campaign) |

`D27_BLOCKED_BY_D26=false`

## 5. Non-goals

- Productive activation of research candidates
- Learning→Optimization productive join
- P5 cutover
- D27 lifecycle gate implementation (separate WP)
