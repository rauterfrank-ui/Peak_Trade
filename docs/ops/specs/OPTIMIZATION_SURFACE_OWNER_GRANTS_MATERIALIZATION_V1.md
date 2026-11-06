---
docs_token: DOCS_TOKEN_OPTIMIZATION_SURFACE_OWNER_GRANTS_MATERIALIZATION_V1
status: active
scope: Materialize Owner decisions D1-D4 for optimization surface family closure
capability: OPTIMIZATION_SURFACE_OWNER_GRANTS_MATERIALIZATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# Optimization Surface Owner Grants Materialization V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
WORKPACKAGE_ID=OPTIMIZATION_SURFACE_OWNER_GRANTS_MATERIALIZATION_V1
BOUND_ORIGIN_MAIN_SHA=3abeffae801f2973408e8e613b1c03f903b08d0a
PREDECESSOR_WP=OPTIMIZATION_SURFACE_FAMILIES_PRE_TEST_PREPARATION_V1
ADJUDICATION_BASIS=F3_F5_OPTIMIZABLE_SURFACE_OWNER_ADJUDICATION_V1
PRODUCTIVE_EFFECT=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
TRADING_LOGIC_CHANGED=false
CORE_BOUNDARY_CHANGED=false
MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY=true
```

Machine-readable decision:
`config/governance/optimization_surface_owner_grants_materialization_v1_decision_v1.json`

## Owner decisions (exact scope)

| ID | Decision | Materialized effect |
|----|----------|---------------------|
| D1 | F5-FRESH GO | Separate optimizable envelope `F5_FRESH_FUTURES_INPUT_FRESHNESS_MAX_AGE_SHADOW_RESEARCH_V1` |
| D2 | F5-SURV SHADOW_CALIBRATION_ONLY | Per-token test-entry registry; no optimizer envelope |
| D3 | F5-CAP SHADOW_CALIBRATION_ONLY | Per-token test-entry registry; no optimizer envelope |
| D4 | F3 GLOBAL_SURFACE_NO_GO | Exclusion record; no strategy.* envelope |

## Non-goals

- Calibration/search/OOS/robustness execution
- Productive threshold or admission mutation
- F3 legacy path activation
- Promotion, Live/POST, M10
