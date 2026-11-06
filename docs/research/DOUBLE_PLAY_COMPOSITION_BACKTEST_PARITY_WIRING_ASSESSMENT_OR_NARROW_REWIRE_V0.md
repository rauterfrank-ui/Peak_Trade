# Double Play Composition Backtest Parity Wiring Assessment or Narrow Rewire v0

Verdict: `PASS_DOUBLE_PLAY_COMPOSITION_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`

Assessment Status: `WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE`

## Scope

This slice assesses whether the canonical Double Play composition matrix in the backtest and integrated offline replay decision chain reuses the same Master-V2 owners and decision matrix as offline scenario replay. It is authority-neutral: no backtest execution, no economic evidence, no runtime mutation, and no canonical trading-semantic change.

## Surface Flags

| Flag | Value |
|---|---|
| `DOUBLE_PLAY_COMPOSITION_BACKTEST_PARITY_STATUS` | `ASSESSED` |
| `DOUBLE_PLAY_COMPOSITION_BACKTEST_PARITY_PASS` | `true` |
| `DOUBLE_PLAY_CANONICAL_OWNER_REUSED` | `true` |
| `SEPARATE_BACKTEST_COMPOSITION_LOGIC_FOUND` | `false` |
| `NARROW_REWIRE_REQUIRED` | `false` |
| `NARROW_REWIRE_IMPLEMENTED` | `false` |
| `BOTH_SIDES_CONFIRMED_CHOP_GUARD_BLOCK` | `true` |
| `SURVIVAL_SUITABILITY_PRE_COMPOSITION_GATES` | `true` |
| `EXISTING_POSITION_MANAGEMENT_CONTINUES` | `true` |
| `NO_IMPLICIT_SCORING_OVERRIDE` | `true` |
| `LONG_SHORT_SYMMETRY_PASS` | `true` |
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
- No risk, sizing, safety, runtime, or promotion change
- No runtime, shadow, paper, testnet, scheduler, adapter submission, orders, credentials, arming, canary, or live authority

## Canonical Owners

| Surface | Canonical Owner | Role |
|---|---|---|
| Bull/Bear directional assessment | `trading.master_v2.directional_assessment_v1` | Shared contract for both sides |
| Survival/Suitability pre-matrix gates | `trading.master_v2.survival_suitability_scenario_binding_adapter_v0` | Consumed before composition; not bypassed |
| Composition matrix (SSOT) | `trading.master_v2.double_play_composition_matrix_v1` | `evaluate_double_play_composition_matrix_v1()` |
| Scenario replay adapter | `trading.master_v2.double_play_composition_scenario_matrix_adapter_v0` | Routes scenario ticks through canonical matrix |
| Integrated offline replay | `trading.master_v2.integrated_offline_trading_logic_replay_v1` | Orchestrator STEP 29B–29H composition |
| MV2 backtest wiring | `backtest.mv2_research_wiring_v1` | Bar-loop → integrated replay |

## Call Paths

### Backtest bar-loop

`src/backtest/mv2_research_wiring_v1.py` → `run_integrated_offline_trading_logic_replay_v1()` → `evaluate_directional_assessment_v1()` (bull/bear) → `evaluate_survival_assessment_v1()` + `evaluate_suitability_binding_v1()` → `evaluate_double_play_composition_matrix_v1()`.

### Offline scenario replay

`src/trading/master_v2/offline_double_play_scenario_replay_v0.py` → `compose_double_play_scenario_via_canonical_matrix_v0()` → `apply_canonical_survival_suitability_pre_matrix_gates_v0()` → `evaluate_double_play_composition_matrix_v1()`.

## Composition Evidence

- Bull and Bear assessments consumed through the same `directional_assessment_v1` contract in integrated replay and scenario adapter inputs.
- Survival and suitability evaluated per side before matrix composition; scenario adapter applies canonical pre-matrix gates.
- `BOTH_SIDES_CONFIRMED` resolves deterministically to `CHOP_GUARD_BLOCK` with `no_new_entry` and `existing_position_management_continues`.
- Composition produces canonical trading decision evidence only; no orders, quantity, adapter compatibility, or authority effects.
- Decision precedence preserved: safety/reconciliation/exit stages remain before reversal and new entry in downstream entry-exit policy.
- No separate backtest scoring, tie-break, fallback, or strategy-selection logic; backtest has no composition SSOT beyond integrated replay.
- Long/short paths are structurally symmetric in parity contract tests.

## Gap Review

| Check | Reproducible |
|---|---|
| bypass path | false |
| duplicate decision path | false |
| missing owner call | false |
| separate backtest composition owner | false |
| integrated replay calls canonical composition matrix | true |
| scenario replay composition matrix adapter bound | true |
| survival/suitability pre-matrix gates bound | true |
| legacy `compose_double_play_decision` in backtest chain | false |
| legacy envelope at scenario adapter only | true |

Prior narrow reuse-first rewire evidence (PR #5016) binds offline scenario replay through canonical owners (`TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH`). Legacy envelope translation at the scenario adapter is compatibility-only and does not reproduce a bypass or parallel trading SSOT in the assessed backtest chain.

## Narrow Rewire Decision

`rewire_implemented=false` and `rewire_required=false` in this slice. Existing wiring is complete for the assessed surface; only manifest-verified PASS assertion evidence is added.

## Prior Surfaces

- `SURVIVAL_AND_SUITABILITY_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0` (PR #5064)
- `FLAT_BEFORE_OPPOSITE_SIDE_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0` (PR #5063)
- `BULL_BEAR_STATE_SWITCH_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`
- `ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`
