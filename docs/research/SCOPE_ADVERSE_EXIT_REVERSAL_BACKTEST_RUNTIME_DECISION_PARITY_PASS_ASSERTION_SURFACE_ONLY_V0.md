# Scope Adverse Exit and Reversal Preparation Backtest Runtime Decision Parity Pass Assertion — Surface Only v0

Verdict: `PASS_SCOPE_ADVERSE_EXIT_REVERSAL_BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_SURFACE_ONLY_V0`

## Scope

This slice materializes a machine-readable, surface-only assertion that Scope Adverse Exit and Reversal Preparation use canonical owners in the backtest decision path. It is documentation and contract evidence only; it does not mutate trading logic, runtime, or backtest execution.

## Surface Flags

| Flag | Value |
|---|---|
| `ADVERSE_SCOPE_EXIT_BACKTEST_PARITY_STATUS` | `WIRED` |
| `REVERSAL_PREPARATION_BACKTEST_PARITY_STATUS` | `WIRED` |
| `SCOPE_EXIT_REVERSAL_BACKTEST_PARITY_PASS` | `true` |
| `SCOPE_EXIT_REVERSAL_BACKTEST_RUNTIME_DECISION_PARITY_PASS` | `true` |
| `BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_SCOPE` | `SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_SURFACE_ONLY` |
| `BACKTEST_RUNTIME_DECISION_PARITY_PASS` | `false` |
| `FULL_CANONICAL_CHAIN_WIRED` | `false` |
| `SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `authority_effect` | `NONE` |
| `runtime_effect` | `NONE` |

## Decision Precedence

| Flag | Value |
|---|---|
| `EXIT_BEFORE_OPPOSITE_SIDE` | `true` |
| `OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT` | `true` |
| `POSITION_FLIP_ALLOWED` | `false` |
| `REDUCE_ONLY_EXIT_PRESERVED` | `true` |

## Boundaries

- FUTURES_ONLY=true
- BITCOIN_DIRECTION_ALLOWED=false
- No Master-V2 trading-semantic change
- No Double-Play semantic change
- No Scope, Exit, Reversal, Survival, Suitability, Risk or Sizing change
- No Runtime, Shadow, Paper, Testnet, Scheduler, Adapter Submission, Orders, Credentials, Arming, Canary or Live authority

## Source Review

- Assessment contract (PR #5060): `docs/research/adverse_exit_and_reversal_preparation_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json`
- Narrow rewire review contract (PR #5061): `docs/research/adverse_exit_and_reversal_preparation_backtest_parity_narrow_rewire_v0.json`
- Source evidence MANIFEST.sha256 verified with RC=0 for both PR #5060 and PR #5061 durable bundles

## Canonical Wiring Evidence

| Evidence | Path |
|---|---|
| Integrated replay orchestrator | `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` |
| Scope adapter | `src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py` |
| Reversal preparation adapter | `src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py` |
| Adverse exit canonical owner | `src/trading/master_v2/deterministic_scope_event_generator_v1.py` |
| Backtest consumer | `src/backtest/mv2_research_wiring_v1.py` |
| Scope parity contract | `tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py` |
| Reversal parity contract | `tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py` |

Integrated replay invokes `resolve_integrated_scope_adverse_exit_signal_v0` and `resolve_integrated_reversal_preparation_entry_exit_binding_v0`, routing through canonical adapters. PR #5061 classified `NARROW_INTEGRATED_CONSUMER_BINDING`; no bypass or duplicate owner path is reproducible from origin/main.

## Mirrored Behavior and Bypass Exclusion

- Mirrored long/short adverse exit and reversal-preparation parity verified via deterministic fixture paths
- Legacy duplicate scope-signal logic absent from integrated replay consumer
- Bypass authority excluded; adapter calls canonical owner only

## Limitations and Non-Claims

- Surface-only assertion; does not imply whole-system `BACKTEST_RUNTIME_DECISION_PARITY_PASS`
- Does not claim `FULL_CANONICAL_CHAIN_WIRED`
- Does not claim `SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE`
- Does not authorize `RUNTIME_REWIRE_ADMISSIBLE`
- Does not assert parity from direct reference count alone
- Assertion is invalidated if canonical owner or backtest consumer paths change materially since PR #5061

## Next Parity Surface

`FLAT_BEFORE_OPPOSITE_SIDE_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`
