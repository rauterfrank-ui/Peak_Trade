---
docs_token: DOCS_TOKEN_V32_D28_D29_SCOPED_OPTIMIZATION_PRODUCTIVE_JOIN_F1_M9_MAX_BUILD_V1
status: active
scope: D28/D29 scoped F1/M9 optimization productive join policy (fail-closed)
capability: V32_D28_D29_SCOPED_OPTIMIZATION_PRODUCTIVE_JOIN_F1_M9_MAX_BUILD_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# V32 D28/D29 — Scoped Optimization Productive Join F1/M9 Max Build V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_D28_D29_SCOPED_OPTIMIZATION_PRODUCTIVE_JOIN_F1_M9_MAX_BUILD_V1
BOUND_ORIGIN_MAIN_SHA=9aa0d05eb1d286b6b705f27b78dd730df02d13d5
PREDECESSOR=V32_D28_D29_OPTIMIZATION_PRODUCTIVE_JOIN_POLICY_ADJUDICATION_AND_MAX_PRE_BLOCKER_BUILD_V1
AUTHORITY_EFFECT=SCOPED_POLICY_ONLY
EXTERNAL_EFFECT_AUTHORIZED=false
TRADING_DECISION_AUTHORITY_CHANGED=false
```

Decision:
`config/governance/v32_d28_d29_scoped_optimization_productive_join_f1_m9_owner_policy_v1_decision_v1.json`

Registry:
`config/governance/v32_d28_d29_scoped_optimization_productive_join_registry_v1.json`

Owners:
`src/governance/v32_d28_d29_scoped_optimization_productive_join_policy_v1.py`
`src/governance/v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1.py`

## 1. Owner policy (ratified)

Productive optimization join authority is **scoped** per `(surface_id, productive_target_id)`.
The learning field `optimization_universe_join_authorized` remains **legacy compatibility only**
and must not be interpreted as universe-wide productive authority.

First authorized pair (PROVEN_CURRENT M9→M10 lineage on baseline):

| surface_id | productive_target_id |
| --- | --- |
| `VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1` | `peak_trade.governance.productive_target.m9_volatility_numeric_max_age_seconds&#47;v1` |

## 2. Global boolean adjudication

```text
GLOBAL_JOIN_BOOLEAN_STATUS=LEGACY_COMPATIBILITY_ONLY_UNCHANGED
optimization_universe_join_authorized=false (unchanged)
scoped_registry_is_pair_authority_ssot=true
```

## 3. F1/M9 lineage (CURRENT)

| Stage | Owner |
| --- | --- |
| Candidate | `research.canonical_volatility_numeric_max_age_parameter_research_execution_v1` |
| Governance ingress | `optimization_proposal_governance_ingress_v1` |
| Explicit authorization | `explicit_productive_authorization_v1` |
| Governed configuration | `governed_productive_configuration_v1` |
| Authorized seam | `authorized_productive_parameter_seam_v1` |
| Runtime transport | `governed_productive_runtime_parameter_seam_join_v1` |
| Consumer | `double_play_runtime_typed_volatility_presence_gate_v1` |

Scoped join policy **does not** replace per-ingress explicit authorization or authorize apply.

## 4. Next true blocker

`M9_SCOPED_JOIN_REQUIRES_PER_INGRESS_EXPLICIT_PRODUCTIVE_AUTHORIZATION_AND_PRODUCTIVE_APPLY_OWNER_GO`

## 5. Non-goals

- Global `optimization_universe_join_authorized=true`
- F2/F5 productive join
- Productive apply / promotion / self-deploy
- Optimization direct runtime write
- Numeric mutation / external effect

## 6. Verification

- `tests/governance/test_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1.py`
