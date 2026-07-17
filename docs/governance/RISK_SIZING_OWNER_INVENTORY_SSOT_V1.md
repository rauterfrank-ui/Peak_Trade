# Risk / Sizing Owner Inventory SSOT v1

**Status:** BINDING inventory / pointer (docs + static contract only)  
**Date:** 2026-07-17  
**Plan item:** `P2_GOVERNANCE &#47; RISK_SIZING_INVENTORY`  
**Machine inventory:** [`config/governance/risk_sizing_owner_inventory_ssot_v1.json`](../../config/governance/risk_sizing_owner_inventory_ssot_v1.json)

```
RISK_SIZING_OWNER_INVENTORY_SSOT_V1=true
INVENTORY_ONLY=true
CONSOLIDATION_STATUS=NOT_STARTED
RISK_SIZING_CLAIMED_CONSOLIDATED=false
CANONICAL_RISK_SIZING_OWNER=UNRESOLVED
CANONICAL_RISK_SIZING_OWNER_MV2_SCOPE=src.governance.capital_risk_sizing_v1
PRODUCTIVE_RISK_SIZING_DECISION_OWNER_COUNT=5
DUPLICATE_PRODUCTIVE_RISK_SIZING_DECISION_OWNERS=true
BYPASS_PATH_COUNT=5
RISK_LIMIT_AND_SIZING_SEPARATION=PARTIAL
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_V1=true
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_SEMANTICS=INVENTORY_ONLY_NOT_AUTHORITY_ASSIGNMENT
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_IS_NOT_AUTHORITY_ASSIGNMENT=true
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_DOES_NOT_PROMOTE_REPO_WIDE_OWNER=true
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_DOES_NOT_CONSOLIDATE=true
THIS_DOCUMENT_IS_INVENTORY_SSOT_NOT_RUNTIME_AUTHORITY=true
NO_RUNTIME_REWIRE_IN_THIS_SLICE=true
NO_TRADING_CORE_CHANGE=true
NO_RISK_SIZING_SEMANTICS_CHANGE=true
NO_LEGACY_ORDER_INTENT_CHANGE=true
NO_RUNTIME_BRIDGE_ACTIVATION=true
ELIGIBLE_FOR_LIVE_DEFAULT=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
RUNTIME_BRIDGE_ACTIVATED=false
ECONOMIC_GATE_REMAINS_FAIL_CLOSED=true
AUTHORITY_EFFECT=NONE
```

**INVENTORY ONLY — NOT CONSOLIDATED.** This slice does **not** claim Risk/Sizing is consolidated, does not rewire owners, and does not change sizing formulas, risk limits, leverage, notional, quantity, stop rules, trading-core semantics, runtime bridge, live/order flags, or the economic gate. The surface contract below is an **inventory / drift freeze only**.

## 1. Executive Summary

Repo-wide forensic inventory shows **five productive Risk/Sizing decision owners** that independently decide position size / quantity on different paths. For the **MV2 / governance / intent-bound chain only**, CRS (`src.governance.capital_risk_sizing_v1`) is uniquely pinned as owner via adapters that delegate without duplicating math.

**Repo-wide canonical owner: `UNRESOLVED`.**  
Reason: Classic Backtest, Offline-Eval sizing contract, Execution `execute_from_signals`, and Live/Shadow `position_fraction` still decide size **without** CRS. Obligation `OBL_B05_CAPITAL_RISK_SIZING_OWNER_SPLIT` remains open (`REQUIRES_RUNTIME_GO`). Do not assert consolidation.

| Metric | Value |
|---|---|
| Productive size decision owners | `5` |
| CRS bypass paths (productive size without CRS) | `5` |
| MV2/governance-chain owner | `src.governance.capital_risk_sizing_v1` |
| Repo-wide unique canonical | `UNRESOLVED` |
| Consolidation | `NOT_STARTED` |

## 2. Owner Matrix

| Owner / Symbol | Path | Role | Status | Authoritative size? | Fail-closed |
|---|---|---|---|---|---|
| CRS `evaluate_capital_risk_sizing_v1` / quantity chain | `src/governance/capital_risk_sizing_v1.py` | canonical decision owner (**MV2 scope**) | ACTIVE | Yes (governance path) | Yes |
| `PositionSizer` / `calc_position_size` | `src/risk/position_sizer.py` | legacy decision owner (classic BT) | LEGACY (still ACTIVE) | Yes (classic) | Partial |
| `BasePositionSizer` family | `src/core/position_sizing.py` | independent decision owner | ACTIVE | Yes if wired | Path-dependent |
| `offline_evaluation_sizing_contract_v1` | `src/backtest/offline_evaluation_sizing_contract_v1.py` | policy owner + calculator wrapper | ACTIVE | Yes (eval path) | Yes |
| `ExecutionPipeline.execute_from_signals` | `src/execution/pipeline.py` | simplified decision owner | ACTIVE | Yes (exec path) | Weak |
| Offline replay / backtest state-file adapters | `src&#47;trading&#47;master_v2&#47;capital_risk_sizing_*_adapter_v0.py` | adapter | ADAPTER_ONLY | No (delegates) | Yes |
| Intent pipeline bridge | `src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py` | adapter/consumer | ADAPTER_ONLY | Consumes CRS | Yes; submission blocked |
| `RiskLimits` / `BaseRiskManager` / dynamic leverage | `src/risk/limits.py`, `src/core/risk.py`, `src/risk/dynamic_leverage.py` | limit / helper | ACTIVE | No | Limit/veto |
| `BacktestEngine` | `src/backtest/engine.py` | consumer (selects owner) | ACTIVE | Indirect | Path-dependent |
| Shadow / testnet `position_fraction` | `src/live/shadow_session.py`, `src/live/testnet_profiles.py` | consumer / config size | ACTIVE | Yes (runtime-ish) | Profile validation |
| `SIZING_OWNER_REF` | `src/meta/learning_loop/runtime_eligibility_v1.py` | reporter / token gate | ACTIVE | Token only | Ref mismatch fails |
| `position_sizer_old_backup` | `src/risk/_archive/position_sizer_old_backup.py` | archive | ARCHIVED | No | n/a |

### Known plan candidates (classification)

| Candidate | Classification |
|---|---|
| **CRS** | `canonical_decision_owner` for MV2/governance/intent-bound paths only; `ACTIVE`; authority/runtime effect `NONE` |
| **PositionSizer** | `legacy_decision_owner` still productively used by Classic Backtest; CRS marks `DEPRECATE_LEGACY_PATH` |
| **core.position_sizing** | Independent `decision_owner` when `core_position_sizer` is wired; **not** a CRS adapter/calculator |

## 3. Call-Graph / Consumer Matrix

```
CRS (capital_risk_sizing_v1)
  ├─ capital_risk_sizing_offline_replay_binding_adapter_v0
  │    ├─ integrated offline / scenario replay harnesses
  │    └─ capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0
  ├─ canonical_order_intent_v1 (consumes decision; no live authority)
  └─ canonical_core_runtime_integration_intent_pipeline_bridge_v0
       └─ OrderIntent / plan (submission_blocked; bridge not activated)

PositionSizer / calc_position_size
  ├─ BacktestEngine (default branch)
  └─ offline_evaluation_sizing_contract_v1
       └─ BacktestEngine (when offline_sizing_bound)

core.position_sizing
  ├─ BacktestEngine (if core_position_sizer set)
  ├─ sweeps / diagnostics helpers
  └─ position-feedback adapters (research/backtest)

Execution execute_from_signals
  └─ signal * max_position_notional_pct  (no CRS)

Live/Shadow
  └─ position_fraction  (no CRS)
```

## 4. Duplicate / Bypass Assessment

### Duplicate owners vs representations

- **Duplicate productive decision owners:** `true` (five independent size authorities across paths).
- **Multiple representations of CRS:** Decision object + evidence refs + backtest state-file binding = adapters, **not** a second math owner.
- Offline-eval contract = policy wrapper around legacy sizer with **own** `sizing_owner`.

### Bypass paths (CRS)

1. `BYPASS_CLASSIC_BACKTEST_DEFAULT` — Classic Backtest default (`calc_position_size` / `PositionSizer`)
2. `BYPASS_CORE_POSITION_SIZER` — `core_position_sizer` branch
3. `BYPASS_OFFLINE_EVAL_SIZING_CONTRACT` — Offline-eval sizing contract
4. `BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS` — Execution `execute_from_signals`
5. `BYPASS_LIVE_SHADOW_POSITION_FRACTION` — Live/Shadow `position_fraction`

CRS `export_bypass_scan_v1` documents legacy sizer presence and `DEPRECATE_LEGACY_PATH` for the governance owner boundary; it does **not** remove classic/execution bypasses.

### Risk/Sizing owner and bypass surface contract v1

```
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_V1=true
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_SEMANTICS=INVENTORY_ONLY_NOT_AUTHORITY_ASSIGNMENT
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_IS_NOT_AUTHORITY_ASSIGNMENT=true
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_DOES_NOT_PROMOTE_REPO_WIDE_OWNER=true
RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_DOES_NOT_CONSOLIDATE=true
EXPECTED_OWNER_COUNT=5
EXPECTED_BYPASS_COUNT=5
DRIFT_POLICY=owner/bypass addition/removal/rename/duplicate/unresolved_symbol/role_or_reachability_drift/authority_escalation → FAIL
```

**Purpose:** inventory / drift freeze of the already-inventoried productive Risk/Sizing decision surface. Machine contract: `risk_sizing_owner_and_bypass_surface_contract` in [`config/governance/risk_sizing_owner_inventory_ssot_v1.json`](../../config/governance/risk_sizing_owner_inventory_ssot_v1.json).

This frozen set does **not**:
- select a repo-wide canonical Risk/Sizing owner (`CANONICAL_RISK_SIZING_OWNER=UNRESOLVED`)
- assign capital authority or execution authority
- consolidate, decommission, rewire, or delegate owners/bypasses
- change Risk/Sizing algorithms, risk limits, capital allocation, position-sizing formulas, notional/quantity derivation, leverage, or exposure caps
- activate runtime bridge, live, testnet, shadow, paper, or orders
- change order intent, order submission, or Legacy Order Intent surface contracts
- assert economic quality of any size path

`role=canonical_decision_owner` for CRS is **MV2-scope classification only**. Repo-wide `CANONICAL_RISK_SIZING_OWNER` remains `UNRESOLVED`.

Per-owner freeze pins (inventory-backed IDs / paths / symbols only):

| stable_id | source_path | symbol_or_callable | role | decision_type | reachability | canonical | authorized | capital_authority |
|---|---|---|---|---|---|---|---|---|
| `backtest.offline_evaluation_sizing_contract_v1` | `src/backtest/offline_evaluation_sizing_contract_v1.py` | `size_offline_evaluation_entry_v1` | policy_owner | offline_evaluation_sizing_policy | REACHABLE_PRODUCTIVE | false | false | false |
| `src.core.position_sizing` | `src/core/position_sizing.py` | `BasePositionSizer` | decision_owner | position_sizing | REACHABLE_PRODUCTIVE | false | false | false |
| `src.execution.pipeline.execute_from_signals` | `src/execution/pipeline.py` | `ExecutionPipeline.execute_from_signals` | decision_owner | quantity_notional_derivation | REACHABLE_PRODUCTIVE | false | false | false |
| `src.governance.capital_risk_sizing_v1` | `src/governance/capital_risk_sizing_v1.py` | `evaluate_capital_risk_sizing_v1` | canonical_decision_owner | capital_risk_sizing_quantity_chain | REACHABLE_PRODUCTIVE | false | false | false |
| `src.risk.position_sizer` | `src/risk/position_sizer.py` | `calc_position_size` | legacy_decision_owner | position_sizing | REACHABLE_PRODUCTIVE | false | false | false |

Per-bypass freeze pins (inventory-backed IDs / paths / symbols only):

| stable_id | source_path | caller_symbol | target | bypasses | canonical | authorized |
|---|---|---|---|---|---|---|
| `BYPASS_CLASSIC_BACKTEST_DEFAULT` | `src/backtest/engine.py` | `BacktestEngine.run_realistic` | `calc_position_size` | CRS | false | false |
| `BYPASS_CORE_POSITION_SIZER` | `src/backtest/engine.py` | `BacktestEngine.run_realistic` | `BasePositionSizer.get_target_position` | CRS | false | false |
| `BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS` | `src/execution/pipeline.py` | `ExecutionPipeline.execute_from_signals` | same (simplified notional pct) | CRS | false | false |
| `BYPASS_LIVE_SHADOW_POSITION_FRACTION` | `src/live/shadow_session.py` | `ShadowPaperSession.step_once` | `SHADOW_CFG_POSITION_FRACTION_ASSIGNMENT` | CRS | false | false |
| `BYPASS_OFFLINE_EVAL_SIZING_CONTRACT` | `src/backtest/engine.py` | `BacktestEngine.run_realistic` | `size_offline_evaluation_entry_v1` | CRS | false | false |

**Separate, unchanged contracts:** Legacy Order Intent `direct_submission_surface_contract_v1` and `decision_owner_surface_contract_v1` remain separate and are **not** mutated by this slice.

### Defaults / caps conflicts (inventory observation only)

| Surface | Example defaults |
|---|---|
| `PositionSizerConfig` | `risk_pct=1.0` (%), `max_position_pct=10.0` (%) |
| `calc_position_size` | `max_position_pct=0.25` (decimal), `min_position_value=50` |
| `config/default.toml` `[risk]` | mixed decimal / percent keys |
| CRS offline adapters | absolute USD risk / equity envelopes |
| `FixedFractionSizer` | `fraction=0.1` |

### Risk limits vs position sizing

**PARTIAL separation:** Limit/veto surfaces (`RiskLimits`, `BaseRiskManager`) are distinct from quantity owners, but CRS bundles Capital+Risk+Sizing stages; Classic Engine sequences size then limits; config mixes sizing and limit keys under `[risk]`.

### Authority leak toward runtime / orders

- **No active live authority leak via CRS/bridge:** CRS `AUTHORITY_EFFECT=NONE`, `RUNTIME_EFFECT=NONE`, `adapter_compatible=false`; intent bridge submission blocked; runtime bridge remains not activated.
- **Semantic parallel-authority leak:** Execution/Live can assign size without CRS (`position_fraction`, `max_position_notional_pct`).

## 5. Canonical Status

```
CANONICAL_STATUS=UNRESOLVED
REASON=Multiple productive size decision owners coexist;
       CRS is unique only for MV2/governance/intent-bound paths;
       OBL_B05 requires Operator-GO architecture decision;
       Classic BT / Offline Eval / Execution / Live-Shadow bypass CRS.
PRODUCTIVE_DECISION_OWNER_COUNT=5
BYPASS_PATH_COUNT=5
INVENTORY_ONLY=true
CONSOLIDATION_STATUS=NOT_STARTED
```

Do **not** treat this inventory as consolidation. Do **not** delete legacy/domain surfaces without a separate call-graph + contract closeout PR under explicit Operator-GO.

## 6. Core Questions (answered)

1. **Productive decision owners:** `5`
2. **Canonical today (repo-wide):** `UNRESOLVED` (MV2-scope only → CRS)
3. **CRS / PositionSizer / core.position_sizing:** CRS = MV2 canonical owner; PositionSizer + core.position_sizing = independent decision owners (not mere adapters)
4. **Parallel size paths:** Yes — Classic BT, MV2/Replay (CRS), Offline Eval, Execution, Live/Shadow; Portfolio risk surfaces are primarily limit/veto
5. **Bypass canonical CRS:** Yes — five productive paths listed above
6. **Contradictory defaults:** Yes — percent vs decimal, absolute vs fraction (see matrix)
7. **Duplicates:** Duplicate owners across paths; CRS adapters are representations, not second owners
8. **Limits vs sizing separation:** `PARTIAL`
9. **Authority leak:** No CRS→orders leak; parallel size authority outside CRS exists
10. **Later reuse-first consolidation (not implemented):** Pin CRS for system evidence; gate classic size behind CRS provenance; demote legacy sizers to calculator/deprecate for core paths; label or align offline-eval contract; bind/deauthorize execution/live simplified size; fix `SIZING_OWNER_REF`; unify defaults

## 7. Open Governance Decisions

1. Is CRS the sole size owner for *all* system/economic evidence — including Classic BT?
2. Remain offline-eval contract non-canonical or rebind to CRS policy inputs?
3. Deauthorize execution/live simplified size until CRS-intent?
4. Are `core.position_sizing` overlays research-only forever?
5. Default harmonization (% vs decimal, absolute vs fraction)
6. Align `SIZING_OWNER_REF` with real CRS module path
7. `OBL_B05` Operator-GO architecture packet

## 8. Safety invariants (unchanged by this slice)

- Economic gate remains fail-closed
- `eligible_for_live` default remains `false`
- Runtime bridge remains bound-not-activated / not activated
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- No trading-core, risk/sizing semantics, legacy order-intent, market-dashboard, or GitHub settings mutation in this slice

## 9. Next plan item after this slice

Risk/Sizing inventory and the owner/bypass surface-contract freeze are **DONE**. Consolidation of Risk/Sizing remains **NOT_STARTED** and requires a separate Operator-GO architecture packet (`OBL_B05_CAPITAL_RISK_SIZING_OWNER_SPLIT`).  

**Related (separate, non-mutating):** [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) / [`config/governance/risk_sizing_units_dimensions_contract_v0.json`](../../config/governance/risk_sizing_units_dimensions_contract_v0.json) declares units/dimensions for the same five owners without changing math, defaults, authority, or the 5/5 owner/bypass freeze.

**Related (separate, non-mutating):** [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md) / [`config/governance/risk_sizing_caller_owner_topology_contract_v0.json`](../../config/governance/risk_sizing_caller_owner_topology_contract_v0.json) freezes caller→owner topology edges without assigning authority or changing sizing semantics.

Legacy Order Intent inventory / decision-owner / direct-submission surface contracts remain separate and unchanged (`INVENTORY ONLY — DECOMMISSION NOT STARTED`).
