# Adverse Exit and Reversal Preparation Backtest Parity Narrow Rewire v0

Verdict: `PASS_SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_NARROW_REWIRE_V0`

## Scope

This slice closes the integrated-replay backtest parity gap documented in PR #5060 assessment by binding the backtest consumer path through existing scope-event and reversal-preparation adapter owners. No runtime authority, no economic evidence, and no trading-semantic change.

## Surface Flags

| Flag | Value |
|---|---|
| `ADVERSE_SCOPE_EXIT_BACKTEST_PARITY_STATUS` | `WIRED` |
| `REVERSAL_PREPARATION_BACKTEST_PARITY_STATUS` | `WIRED` |
| `SCOPE_EXIT_REVERSAL_BACKTEST_PARITY_PASS` | `true` |
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
- No runtime, scheduler, order, credential, shadow, paper, testnet, canary, or live authority

## Canonical Owners (Reuse)

| Surface | Owner | Narrow Binding |
|---|---|---|
| Adverse exit evidence | `deterministic_scope_event_generator_v1` | `derive_scope_adverse_exit_signal_v0(scope_event)` |
| Reversal preparation projection | `reversal_preparation_scenario_binding_adapter_v0` | `project_composition_for_reversal_preparation_entry_exit_v0` |
| Backtest consumer | `mv2_research_wiring_v1.py` | `run_integrated_offline_trading_logic_replay_v1()` |
| Integrated replay orchestrator | `integrated_offline_trading_logic_replay_v1.py` | consumer-bound resolver functions only |

## Narrow Rewire

`rewire_implemented=true` at the integrated replay consumer boundary only:

1. `resolve_integrated_scope_adverse_exit_signal_v0` derives adverse scope exit from canonical scope evidence instead of suppressing via backtest-default passthrough.
2. `resolve_integrated_reversal_preparation_entry_exit_binding_v0` reuses reversal-preparation adapter projection before entry-exit policy evaluation.

No parallel SSOT created.

## Required Contract Tests

- `ADVERSE_SCOPE_EXIT_WIRED_TO_BACKTEST`
- `REVERSAL_PREPARATION_WIRED_TO_BACKTEST`
- `REVERSAL_PREPARATION_PRODUCES_EXIT_BEFORE_OPPOSITE_ENTRY`
- `OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT`
- `POSITION_FLIP_NOT_ALLOWED`
- `REDUCE_ONLY_EXIT_PRESERVED`
