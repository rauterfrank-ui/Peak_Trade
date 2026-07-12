# Cross-Sectional Futures Lead-Lag Information Diffusion v0 Versioned Hypothesis Binding

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_VERSIONED_HYPOTHESIS_BINDING_V0
STATUS: VERSIONED_HYPOTHESIS_BINDING_RATIFIED
scope: governance, research-binding-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifies the versioned offline research binding for `cross_sectional_futures_lead_lag_information_diffusion&#47;v0`. No economic evaluation, no runtime authority, no promotion.

## Binding Summary

| Field | Value |
|---|---|
| `RESEARCH_SCOPE` | `cross_sectional_futures_lead_lag_information_diffusion&#47;v0` |
| `HYPOTHESIS_ID` | `CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_NON_BITCOIN_PERPETUALS_V0` |
| `SCORE_FAMILY_POLICY` | `panel_median_benchmark_lagged_return_diffusion_v0` |
| `DEFAULT_LAG_WINDOW_L` | `8` |
| `ADMISSIBLE_LAG_SURFACE` | `{4,8,12,24}` |
| `DATASET_ID` | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` |
| `MATERIAL_DIFFERENCE_PROVEN` | `true` |
| `SAME_SEMANTIC_BINDING` | `false` |

## Authoritative Owners

- Config: `config/research/cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0.json`
- Materializer: `scripts/research/materialize_cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0.py`
- Validator: `src/research/cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0.py`
- Score: `src/research/cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0.py`

## Next Admissible Scope

Offline economic evaluation execution only with separate Operator-GO:
`GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0`
