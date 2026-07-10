# Adverse Exit and Reversal Preparation Backtest Parity Wiring Assessment or Narrow Rewire v0

Verdict: `PASS_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`

Assessment Status: `ASSESSED_EXISTING_BACKTEST_PARITY_WIRING_CANDIDATE_FOUND_REVIEW_REQUIRED`

## Scope

This slice assesses whether Scope Adverse Exit and Reversal Preparation in the backtest decision path reuse the same canonical Master-V2 / Double-Play owners as offline scenario replay and runtime-near integrated replay. It is authority-neutral: no backtest execution, no economic evidence, no runtime mutation, and no canonical trading-semantic change.

## Surface Flags

| Flag | Value |
|---|---|
| `ADVERSE_SCOPE_EXIT_BACKTEST_PARITY_STATUS` | `ASSESSED` |
| `REVERSAL_PREPARATION_BACKTEST_PARITY_STATUS` | `ASSESSED` |
| `SCOPE_EXIT_REVERSAL_BACKTEST_PARITY_PASS` | `false` |
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

| Surface | Canonical Owner | Adapter / Policy |
|---|---|---|
| Adverse Exit evidence | `trading.master_v2.deterministic_scope_event_generator_v1` | `scope_event_generator_scenario_binding_adapter_v0` derives `scope_adverse_exit_signal` |
| Adverse Exit decision | `trading.master_v2.double_play_entry_exit_policy_v0` | `ExitClass.ADVERSE_SCOPE_EXIT`, precedence stage `MANDATORY_EXIT` |
| Reversal Preparation composition | `trading.master_v2.double_play_composition_matrix_v1` | `CompositionStatus.REVERSAL_PREPARATION` |
| Reversal Preparation decision | `trading.master_v2.double_play_entry_exit_policy_v0` | `reversal_preparation_scenario_binding_adapter_v0` → `ExitClass.REVERSAL_PREPARATION_EXIT` |

## Call Paths

### Backtest bar-loop

`src/backtest/mv2_research_wiring_v1.py` → `run_integrated_offline_trading_logic_replay_v1()` with `adverse_exit_distance=60.0` and default `scope_adverse_exit_signal=PolicySignalV0(triggered=False)`.

### Offline scenario replay

`src/trading/master_v2/offline_double_play_scenario_replay_v0.py` → `evaluate_scenario_scope_event_v0()` → `derive_scope_adverse_exit_signal_v0()` and `evaluate_scenario_reversal_preparation_entry_exit_v0()` → `evaluate_double_play_entry_exit_policy_v0()`.

## Decision Precedence Evidence

- Adverse scope exit resolves at precedence stage `MANDATORY_EXIT` before reversal preparation.
- Reversal preparation resolves at stage `REVERSAL` as reduce-only preparation, never as direct opposite-side entry.
- `reduce_only=True` and `position_flip_allowed=False` on all exit decisions.
- Opposite-side entry requires `FLAT_RECONCILED`; no direct long-to-short or short-to-long transition.

## Gap Review

| Check | Reproducible |
|---|---|
| bypass path | false |
| duplicate decision path | false |
| missing owner call | false |
| missing parity contract | false |
| integrated replay derives `scope_adverse_exit_signal` from scope evidence | false |
| scenario replay derives `scope_adverse_exit_signal` from scope evidence | true |
| backtest bar-loop defaults suppress adverse signal | true |

Prior narrow reuse-first rewire evidence already binds offline scenario replay through canonical owners (`TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH`). The remaining integrated-replay signal passthrough gap is documented but does not reproduce a bypass or parallel trading SSOT.

## Narrow Rewire Decision

`rewire_implemented=false` in this slice. Existing scenario-binding adapters and parity contracts already prove owner-bound offline parity. The admissible next slice for integrated signal-binding review is `SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_NARROW_REWIRE_V0`.

## Next Ranked Parity Surface

`SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_NARROW_REWIRE_V0`
