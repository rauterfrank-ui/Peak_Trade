# Promotion Owner and Gate Inventory SSOT v1

**Status:** BINDING inventory / pointer (docs + static contract only)  
**Date:** 2026-07-17  
**Plan item:** `P2_GOVERNANCE / PROMOTION_OWNER`  
**Machine inventory:** [`config/governance/promotion_owner_and_gate_inventory_ssot_v1.json`](../../config/governance/promotion_owner_and_gate_inventory_ssot_v1.json)

```
PROMOTION_OWNER_AND_GATE_INVENTORY_SSOT_V1=true
CANONICAL_PROMOTION_GATE_OWNER=governance.promotion_loop.promotion_economic_gate_v1
CANONICAL_PROMOTION_GATE_MODULE=src/governance/promotion_loop/promotion_economic_gate_v1.py
CANONICAL_PROMOTION_GATE_CALLABLE=evaluate_promotion_economic_gate_v1
PRODUCTIVE_PROMOTION_DECISION_OWNER_COUNT=1
DUPLICATE_PRODUCTIVE_PROMOTION_DECISION_OWNERS=false
SECOND_PRODUCTIVE_PROMOTION_DECISION_OWNER_FORBIDDEN=true
THIS_DOCUMENT_IS_INVENTORY_SSOT_NOT_RUNTIME_AUTHORITY=true
NO_RUNTIME_REWIRE_IN_THIS_SLICE=true
NO_TRADING_CORE_CHANGE=true
NO_RISK_SIZING_CHANGE=true
NO_LEGACY_ORDER_INTENT_CHANGE=true
NO_RUNTIME_BRIDGE_ACTIVATION=true
ELIGIBLE_FOR_LIVE_DEFAULT=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
ECONOMIC_GATE_REMAINS_FAIL_CLOSED=true
AUTHORITY_EFFECT=NONE
```

## 1. Purpose

Repo-wide inventory that pins the **single productive promotion gate / candidate-eligibility decision owner** and classifies every other promotion-related surface so operators and agents do not treat adapters, research registries, learning-loop evidence, or docs as a second decision owner.

This document does **not** authorize live, orders, runtime bridge activation, deployment, or capital changes.

## 2. Canonical gate owner (decision owner)

| Field | Value |
|---|---|
| Classification | `CANONICAL_DECISION_OWNER` |
| Module path | `src/governance/promotion_loop/promotion_economic_gate_v1.py` |
| Owner id | `governance.promotion_loop.promotion_economic_gate_v1` |
| Policy version | `promotion_economic_gate_v1` |
| Primary callable | `evaluate_promotion_economic_gate_v1` |
| Current-repo probe | `evaluate_current_repo_promotion_gate_v1` |
| Effect | Non-authorizing promotion **candidate** eligibility only; fail-closed |
| Deployment / runtime / activation / execution | Never granted by a PASS |

Call-graph (productive `src/` importers of the gate owner, 2026-07-17):

- `src/research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.py` — adapter/precheck → calls real gate
- `src/research/linear_evidence/offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py` — consumer binding → calls real gate
- `src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py` — boundary adapter → calls real gate
- `src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py` — adapter (imports gate policy constants; boundary via Surface M)
- Reconciliation / parity harness modules that **reference** the owner without replacing it

`PROMOTION_ECONOMIC_GATE_POLICY_OWNER` is defined only in the gate module. Other modules may alias `CANONICAL_PROMOTION_GATE_OWNER = PROMOTION_ECONOMIC_GATE_POLICY_OWNER` but must not redefine the owner string.

## 3. Classification of other promotion surfaces

### ADAPTER / CONSUMER

Thin bindings that invoke or mirror the canonical gate without owning gate policy:

- `src/research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.py`
- `src/research/linear_evidence/offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py`
- `src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py`
- `src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py`
- `src/governance/canonical_offline_linear_diagnostics_promotion_binding_completion_reconciliation_v0.py` (`PROMOTION_GATE_CONSUMER_OWNER`)
- `src/governance/bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_and_promotion_binding_completion_reconciliation_v0.py` (`PROMOTION_GATE_CONSUMER_OWNER`)

### REPORTING / OBSERVABILITY

Status / parity / evidence surfaces that report promotion-boundary state:

- `src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py`
- `src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py`
- `src/trading/master_v2/surface_p_final_flags_fail_closed_contract_v0.py` (flag matrix row `promotion_gate_boundary`)
- `src/meta/learning_loop/runtime_eligibility_v1.py` (consumes promotion decision digests; rejects when not authorized by canonical owner)
- `src/meta/learning_loop/deploy_inactive_v1.py` (inactive deploy evidence; not a live promotion gate)

### POLICY / DOCS

- `docs/PROMOTION_LOOP_V0.md`
- `docs/ops/specs/MASTER_V2_PROMOTION_STATE_MACHINE_V1.md`
- `docs/LEARNING_PROMOTION_LOOP_*`, `docs/learning_promotion/**`
- Runbook / progress registry mentions of promotion (non-authorizing)

### TEST / FIXTURE

- `tests/governance/test_promotion_economic_gate_v1.py`
- `tests/ops/test_step29n_promotion_economic_gate_binding_fail_closed_contract_v0.py`
- `tests/research/test_*promotion_economic_gate*`
- `tests/trading/master_v2/test_promotion_gate_boundary_*`
- Related scripts under `scripts/ops/*promotion*`, `scripts/run_promotion_proposal_cycle.py`

### LEGACY / DOMAIN-SCOPED (not a second productive live-promotion gate)

These remain in-tree. They are **not** deleted in this slice. They are **not** the canonical live/candidate promotion economic gate:

| Path | Role | Why not canonical gate |
|---|---|---|
| `src/governance/promotion_loop/engine.py` + `safety.py` + `models.py` | Promotion Loop v0 candidate filter (`eligible_for_live` default `false`) | Loop/safety filter; does not own economic gate policy; default blocks live |
| `src/research/okx_full_panel_dataset_promotion_decision_and_binding_v0.py` | Research dataset promotion / panel binding | Domain research registry decision, not economic gate |
| `src/research/step31f_promotion_metric_materialization_path_execution_owner_v0.py` | Metric materialization path owner | Research path execution owner, not promotion gate |
| `src/meta/learning_loop/comparison_promotion_policy_decision_v1.py` | Offline LEVEL_3 descriptive policy decision evidence | Explicitly `promotion_decision_is_descriptive_only` / non-authorizing |
| `src/experiments/topn_promotion.py` | Sweep Top-N export helper | Experiment tooling, not governance gate |

### FALSE_POSITIVE

- Mentions of `eligible_for_live` only as denylist / field lists in learning-loop contracts
- Egg-info / generated path lists
- Docs examples that illustrate forbidden live-eligibility true states

## 4. Competing decision-owner verdict

**Productive promotion economic gate decision owners:** `1`  
**Duplicate productive decision owners:** `false`

Apparent “multiple promotion owners” in prior audits are inventory noise: adapters, research dataset decisions, descriptive learning evidence, and the v0 loop filter. After classification, only `promotion_economic_gate_v1` owns productive promotion **candidate eligibility** gating for the economic gate.

Do **not** delete legacy/domain surfaces without a separate call-graph + contract closeout PR.

## 5. Safety invariants (unchanged by this slice)

- Economic gate remains fail-closed (`promotion_eligible=false` under current-repo probe)
- `eligible_for_live` default remains `false`
- Runtime bridge remains bound-not-activated / not activated
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- No trading-core, risk/sizing, legacy order-intent, market-dashboard, or GitHub settings mutation in this slice

## 6. Next plan item after this slice

`P2 Risk/Sizing Inventory` (CRS / PositionSizer / `core.position_sizing`) — inventory only; **not** claimed consolidated by this PR.
