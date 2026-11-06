---
docs_token: DOCS_TOKEN_F2_DETERMINISTIC_COST_GRID_IDENTITY_REPLAY_AND_STEP29M_BOUNDED_SENSITIVITY_OOS_RESEARCH_EXECUTION_V1
status: active
scope: F2 E2E research execution — identity replay + Step29M bounded sensitivity/OOS + evidence
capability: F2_DETERMINISTIC_COST_GRID_IDENTITY_REPLAY_AND_STEP29M_BOUNDED_SENSITIVITY_OOS_RESEARCH_EXECUTION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# F2 — Deterministic Cost Grid Identity Replay + Step29M Bounded Sensitivity/OOS V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
WORKPACKAGE_ID=F2_DETERMINISTIC_COST_GRID_IDENTITY_REPLAY_AND_STEP29M_BOUNDED_SENSITIVITY_OOS_RESEARCH_EXECUTION_V1
BOUND_ORIGIN_MAIN_SHA=903acb8afe5422a1e20edf077748524c95685e2e
PREDECESSOR=F2_RESEARCH_BACKTEST_COST_GRID_END_TO_END_V1
RESEARCH_OPTIMIZATION_ONLY=true
PROPOSAL_ONLY=true
PRODUCTIVE_TRADING_EFFECT=NONE
TRADING_AUTHORITY=NONE
SELECTION_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
```

Decision:
`config/governance/f2_deterministic_cost_grid_identity_replay_step29m_bounded_sensitivity_oos_research_execution_v1_decision_v1.json`

## Purpose

Materialize the authorized F2 optimizable envelope as a **research-only** execution surface:

1. D27 F2 `TEST_ENTRY_GATE` admission
2. Deterministic canonical experiment identity replay (config- and git-bound provenance)
3. Existing Step29M `run_parameter_sensitivity_v1` bounded grid + train/validation/OOS evaluation
4. Required F2 evidence classes from `research_backtest_cost_grid_evidence_requirements_v1.json`

## Authoritative Step29M config (fail-closed)

Single path only — converging refs:

- `src/backtest/okx_eth_perp_research_cost_grid_v1_constants.py` → `SOURCE_STEP29M_CONFIG`
- `config/governance/step29m_current_single_selected_future_dynamic_binding_v1.json`
- `config/governance/optimizable_envelope/research_backtest_cost_grid_allowed_policy_domain_v1.json`

Owner module: `src/experiments/f2_step29m_config_authority_v1.py`

## Non-goals

- M4 experiment plane surface switch
- Productive apply, promotion, threshold selection, live/testnet
- New fee/slippage domain values or parallel sensitivity engines
