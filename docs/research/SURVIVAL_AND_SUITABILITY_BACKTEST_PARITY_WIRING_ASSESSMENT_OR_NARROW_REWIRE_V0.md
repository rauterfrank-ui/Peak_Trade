# Survival and Suitability Backtest Parity Wiring Assessment or Narrow Rewire v0

Verdict: `PASS_SURVIVAL_AND_SUITABILITY_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`

Assessment Status: `WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE`

## Scope

This slice assesses whether the canonical backtest and offline replay decision chain fully represents survival aggregation (six subchecks) and suitability/regime binding (deterministic strategy selection, unknown-regime fail-closed). It is authority-neutral: no backtest execution, no economic evidence, no runtime mutation, and no canonical trading-semantic change.

## Surface Flags

| Flag | Value |
|---|---|
| `SURVIVAL_BACKTEST_PARITY_STATUS` | `WIRED` |
| `SURVIVAL_BACKTEST_PARITY_PASS` | `true` |
| `SUITABILITY_BACKTEST_PARITY_STATUS` | `WIRED` |
| `SUITABILITY_BACKTEST_PARITY_PASS` | `true` |
| `SURVIVAL_REQUIRED_UNKNOWN_BLOCKS` | `true` |
| `SURVIVAL_ANY_HARD_FAIL_FAILS` | `true` |
| `SURVIVAL_ALL_REQUIRED_PASS_REQUIRED` | `true` |
| `UNKNOWN_REGIME_BLOCKS_NEW_ENTRY` | `true` |
| `NO_IMPLICIT_STRATEGY_SELECTION_BY_LIST_ORDER` | `true` |
| `NO_FALLBACK_STRATEGY` | `true` |
| `STABLE_TIE_BREAK_POLICY_BOUND` | `true` |
| `CANONICAL_OWNER_IDENTIFIED` | `true` |
| `REWIRE_REQUIRED` | `false` |
| `BACKTEST_RUNTIME_DECISION_PARITY_PASS` | `false` |
| `FULL_CANONICAL_CHAIN_WIRED` | `false` |
| `SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `authority_effect` | `NONE` |
| `runtime_effect` | `NONE` |

## Boundaries

- FUTURES_ONLY=true
- BITCOIN_DIRECTION_ALLOWED=false
- No Master-V2 trading-semantic change
- No Double-Play semantic change
- No risk, sizing, or promotion change
- No runtime, shadow, paper, testnet, scheduler, adapter submission, orders, credentials, arming, canary, or live authority

## Canonical Owners

| Surface | Canonical Owner | Role |
|---|---|---|
| Survival aggregation + six subchecks | `trading.master_v2.survival_assessment_v1` | `aggregate_survival_status()` fail-closed aggregation |
| Suitability / regime binding | `trading.master_v2.suitability_binding_v1` | Regime gating, eligibility filter, `select_strategy_deterministic()` |
| Deterministic strategy selection | `trading.master_v2.suitability_binding_v1` | `priority_rank` asc, then `strategy_id` lexicographic asc |
| Integrated offline replay | `trading.master_v2.integrated_offline_trading_logic_replay_v1` | Orchestrator STEP 29B–29H |
| Scenario replay adapter | `trading.master_v2.survival_suitability_scenario_binding_adapter_v0` | Scenario ticks → canonical survival + suitability |
| MV2 backtest wiring | `backtest.mv2_research_wiring_v1` | Bar-loop → integrated replay |

## Call Paths

### Backtest bar-loop

`src/backtest/mv2_research_wiring_v1.py` → `run_integrated_offline_trading_logic_replay_v1()` → `evaluate_survival_assessment_v1()` + `evaluate_suitability_binding_v1()`.

### Offline scenario replay

`src/trading/master_v2/offline_double_play_scenario_replay_v0.py` → `compose_double_play_scenario_via_canonical_matrix_v0()` → `apply_canonical_survival_suitability_pre_matrix_gates_v0()` → canonical survival + suitability.

## Survival Aggregation Evidence

- Six required subchecks wired: `DATA_COMPLETENESS_CHECK`, `COST_SURVIVAL_CHECK`, `VOLATILITY_SURVIVAL_CHECK`, `SEQUENCE_SURVIVAL_CHECK`, `DRAWDOWN_SURVIVAL_CHECK`, `LIQUIDATION_BUFFER_CHECK`.
- `ANY_HARD_FAIL` → `FAIL`; `ANY_REQUIRED_UNKNOWN` → `BLOCKED`; `ALL_REQUIRED_PASS` → `PASS` via `aggregate_survival_status()`.
- No separate backtest survival owner; backtest consumes integrated replay only.

## Suitability / Regime Evidence

- `UNKNOWN` regime blocks new entry fail-closed (`unknown_regime_blocked`).
- No implicit strategy selection by registry list order; `select_strategy_deterministic()` uses versioned ranking policy.
- No fallback strategy when survival blocked or no eligible strategies.
- Registry adapter (`suitability_registry_adapter_v1`) provides deterministic snapshot binding only.

## Gap Review

| Check | Reproducible |
|---|---|
| bypass path | false |
| duplicate decision path | false |
| missing owner call | false |
| separate backtest survival owner | false |
| separate backtest suitability owner | false |
| integrated replay calls canonical survival + suitability | true |
| scenario replay survival/suitability adapter bound | true |
| legacy envelope at scenario loop init | true |
| integrated replay stub survival metrics | true |
| backtest regime status hardcoded KNOWN | true |

Prior narrow reuse-first rewire evidence (PR #5017) binds offline scenario replay through canonical owners (`TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH`). Legacy envelope initialization and stub metric inputs are compatibility/documentation gaps only; they do not reproduce a bypass or parallel trading SSOT in the assessed backtest chain.

## Narrow Rewire Decision

`rewire_implemented=false` and `rewire_required=false` in this slice. Existing wiring is complete for the assessed surface; only manifest-verified PASS assertion evidence is added.

## Prior Surfaces

- `FLAT_BEFORE_OPPOSITE_SIDE_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0` (PR #5063)
- `BULL_BEAR_STATE_SWITCH_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`
- `ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`
