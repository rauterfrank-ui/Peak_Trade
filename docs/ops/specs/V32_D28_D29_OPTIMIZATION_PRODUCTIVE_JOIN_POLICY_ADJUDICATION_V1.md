---
docs_token: DOCS_TOKEN_V32_D28_D29_OPTIMIZATION_PRODUCTIVE_JOIN_POLICY_ADJUDICATION_V1
status: active
scope: D28/D29 optimization productive join forensic adjudication (read-only)
capability: V32_D28_D29_OPTIMIZATION_PRODUCTIVE_JOIN_POLICY_ADJUDICATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# V32 D28/D29 — Optimization Productive Join Policy Adjudication V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_D28_D29_OPTIMIZATION_PRODUCTIVE_JOIN_POLICY_ADJUDICATION_AND_MAX_PRE_BLOCKER_BUILD_V1
BOUND_ORIGIN_MAIN_SHA=10f1a289b57cdf4b55efb71c76ac04c1eafaad3f
PREDECESSOR=V32_POST_D27_TEST_ENTRY_LIFECYCLE_GLOBAL_CLOSURE_ADJUDICATION_V1
EXTERNAL_EFFECT_AUTHORIZED=false
NEW_AUTHORITY_CREATED=false
TRADING_DECISION_AUTHORITY_CHANGED=false
IMPLEMENTATION_MODE=FORENSIC_ADJUDICATION_AND_COMPOSITION
```

Decision:
`config/governance/v32_d28_d29_optimization_productive_join_policy_adjudication_v1_decision_v1.json`

Owner:
`src/governance/v32_d28_d29_optimization_productive_join_policy_adjudication_v1.py`

## 1. Purpose

Forensic adjudication of optimization→productive join edges after global D27 closure.
Materializes an evidence-bound join matrix (F1/M9, F2, F5 subfamilies separated) and
records the first owner-policy boundary **without** flipping join booleans or authorizing
promotion, apply, numeric mutation, or external effect.

## 2. D28 / D29 classification

| Item | Status | Class |
| --- | --- | --- |
| D28 promotion intent (Concept v3.2) | OWNER_POLICY_REQUIRED | NAVIGATION_ONLY |
| D29 promotion intent (Concept v3.2) | OWNER_POLICY_REQUIRED | NAVIGATION_ONLY |
| F1/M9 M10 parameter lineage | PROVEN_CURRENT | CANONICAL_AUTHORITY (composed) |
| Global `optimization_universe_join_authorized` | OWNER_POLICY_REQUIRED | ADJUDICATED boundary |

Review admission ≠ productive authorization. Authorization ≠ apply. Apply ≠ self-deploy.

## 3. Join matrix (summary)

| row_id | status |
| --- | --- |
| F1-M9-M10-PARAMETER-LINEAGE | PROVEN_CURRENT |
| LEARNING-EVIDENCE-EXPORT-TO-OPTIMIZATION-INPUT | PROVEN_CURRENT |
| GLOBAL-OPTIMIZATION-UNIVERSE-PRODUCTIVE-JOIN | OWNER_POLICY_REQUIRED |
| F2-RESEARCH-COUNTERFACTUAL | FORBIDDEN |
| F5-FRESH-SHADOW-RESEARCH | FORBIDDEN |
| F5-SURV-PER-TOKEN-SHADOW | FORBIDDEN |
| F5-CAP-PER-TOKEN-SHADOW | FORBIDDEN |
| OPTIMIZATION-DIRECT-RUNTIME-SEAM-WRITE | FORBIDDEN |

Full rows: `build_optimization_productive_join_matrix_v1()`.

## 4. Next true blocker

`GLOBAL_OPTIMIZATION_UNIVERSE_JOIN_BOOLEAN_REQUIRES_SCOPED_OWNER_POLICY`

Minimal owner-policy question (decision JSON field `minimal_owner_policy_question`).

## 5. Non-goals

- Setting `optimization_universe_join_authorized=true`
- Productive promotion / apply / self-deploy
- F5-SURV/CAP/FRESH productive join
- D28/D29 runtime promotion gates
- Live / Testnet / order / external effect

## 6. Verification

- `tests/governance/test_v32_d28_d29_optimization_productive_join_policy_adjudication_v1.py`
