# Entry Position Exit Policy Backtest Parity Wiring Assessment or Narrow Rewire v0

Verdict: `PASS_ENTRY_POSITION_EXIT_POLICY_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`

Assessment Status: `WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE`

## Scope

This slice assesses whether the canonical Entry / Existing-Position-Management / Exit policy in the backtest and integrated offline replay decision chain reuses the same Master-V2 owners and decision semantics as offline scenario replay. It is authority-neutral: no backtest execution, no economic evidence, no runtime mutation, and no canonical trading-semantic change.

## Surface Flags

| Flag | Value |
|---|---|
| `ENTRY_POLICY_BACKTEST_PARITY_STATUS` | `ASSESSED` |
| `ENTRY_POLICY_BACKTEST_PARITY_PASS` | `true` |
| `POSITION_MANAGEMENT_BACKTEST_PARITY_STATUS` | `ASSESSED` |
| `POSITION_MANAGEMENT_BACKTEST_PARITY_PASS` | `true` |
| `EXIT_POLICY_BACKTEST_PARITY_STATUS` | `ASSESSED` |
| `EXIT_POLICY_BACKTEST_PARITY_PASS` | `true` |
| `PARTIAL_FILL_SEMANTICS_STATUS` | `ASSESSED` |
| `REDUCE_ONLY_INVARIANT_STATUS` | `ASSESSED` |
| `POSITION_FLIP_FORBIDDEN_STATUS` | `ASSESSED` |
| `NARROW_REWIRE_REQUIRED` | `false` |
| `NARROW_REWIRE_PERFORMED` | `false` |
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
- No reconciliation, safety, killswitch, sizing, or promotion change
- No runtime, shadow, paper, testnet, scheduler, adapter submission, orders, credentials, arming, canary, or live authority

## Canonical Owners

| Surface | Canonical Owner | Role |
|---|---|---|
| Entry Preconditions | `trading.master_v2.double_play_entry_exit_policy_v0` | `_entry_preconditions_met()` gate |
| Existing Position Management | `trading.master_v2.double_play_entry_exit_policy_v0` | `DecisionPrecedenceStage.EXISTING_POSITION` |
| Exit Classes | `trading.master_v2.double_play_entry_exit_policy_v0` | `ExitClass` enum and `_MANDATORY_EXIT_PRIORITY` |
| Profit Protection Exit | `trading.master_v2.double_play_entry_exit_policy_v0` | `ExitClass.PROFIT_PROTECTION_EXIT` |
| Time Exit | `trading.master_v2.double_play_entry_exit_policy_v0` | `ExitClass.TIME_EXIT` |
| Strategy Invalidation Exit | `trading.master_v2.double_play_entry_exit_policy_v0` | `ExitClass.STRATEGY_INVALIDATION_EXIT` |
| Adverse Scope Exit | `trading.master_v2.double_play_entry_exit_policy_v0` | `ExitClass.ADVERSE_SCOPE_EXIT` |
| Reversal Preparation Exit | `trading.master_v2.double_play_entry_exit_policy_v0` | `ExitClass.REVERSAL_PREPARATION_EXIT` |
| Flat-before-opposite-side adapter | `trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0` | Blocks opposite entry until reconciled flat |
| Scenario replay adapter | `trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0` | Routes scenario ticks through canonical policy |
| Integrated offline replay | `trading.master_v2.integrated_offline_trading_logic_replay_v1` | Orchestrator entry-exit decision stage |
| MV2 backtest wiring | `backtest.mv2_research_wiring_v1` | Bar-loop → integrated replay |

## Call Paths

### Backtest bar-loop

`src/backtest/mv2_research_wiring_v1.py` → `run_integrated_offline_trading_logic_replay_v1()` → `evaluate_double_play_entry_exit_policy_v0()`.

### Offline scenario replay

`src/trading/master_v2/offline_double_play_scenario_replay_v0.py` → `evaluate_scenario_flat_before_opposite_side_entry_exit_v0()` → `evaluate_scenario_entry_exit_policy_v0()` → `evaluate_double_play_entry_exit_policy_v0()`.

## Decision Precedence Evidence

- Entry preconditions enforced: direction armed, composition directional, flat reconciled, reconciliation reconciled, trading gate, safety mode, data integrity, clock trust, cooldown.
- Existing position management resolves at `EXISTING_POSITION` stage before new entry.
- Mandatory exits resolve in stable priority order: adverse scope → profit protection → time → strategy invalidation.
- Reversal preparation resolves at `REVERSAL` stage as reduce-only preparation, never as direct opposite-side entry.
- `reduce_only=True` and `position_flip_allowed=False` on all exit decisions.
- `quantity_status=NOT_BOUND` — no order, adapter, or credential authority.
- Partial-fill and unknown position states block entry and reversal (`partial_fill_or_unknown_blocks_entry`).
- Opposite-side entry requires `FLAT_RECONCILED`; no direct long-to-short or short-to-long transition.

## Gap Review

| Check | Reproducible |
|---|---|
| bypass path | false |
| duplicate decision path | false |
| missing owner call | false |
| separate backtest entry owner | false |
| separate backtest exit owner | false |
| direct reversal-to-opposite-entry | false |
| integrated replay calls canonical entry-exit policy | true |
| scenario replay entry-exit adapter bound | true |
| scenario replay flat-before adapter bound | true |
| backtest bar-loop position state static flat default | true |

Prior narrow reuse-first rewire evidence already binds offline scenario replay through canonical owners (`TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH`). The integrated-replay position-state merge gap is documented but does not reproduce a bypass or parallel trading SSOT.

## Narrow Rewire Decision

`rewire_implemented=false` in this slice. Existing scenario-binding adapters and parity contracts already prove owner-bound offline parity. No functional rewire required.

## Source Evidence

`SOURCE_EVIDENCE_REFERENCED=false` — no durable archive bundle referenced. Prior in-repo contract refs reviewed only.
