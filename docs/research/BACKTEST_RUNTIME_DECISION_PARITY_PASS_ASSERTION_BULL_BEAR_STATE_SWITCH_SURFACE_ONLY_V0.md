# Backtest Runtime Decision Parity Pass Assertion — Bull/Bear State Switch Surface Only v0

Verdict: `PASS_BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_BULL_BEAR_STATE_SWITCH_SURFACE_ONLY_V0`

## Scope

This slice materializes a machine-readable, surface-only assertion that Bull/Bear State Switch uses the canonical owner in the backtest decision path. It is documentation and contract evidence only; it does not mutate trading logic, runtime, or backtest execution.

## Surface Flags

| Flag | Value |
|---|---|
| `BULL_BEAR_STATE_SWITCH_BACKTEST_PARITY_PASS` | `true` |
| `BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_SCOPE` | `BULL_BEAR_STATE_SWITCH_SURFACE_ONLY` |
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
- No Double-Play change
- No Scope, Exit, Reversal, Survival, Suitability, Risk or Sizing change
- No Runtime, Shadow, Paper, Testnet, Scheduler, Adapter Submission, Orders, Credentials, Arming, Canary or Live authority

## Source Review

- Assessment contract (PR #5057): `docs/research/bull_bear_state_switch_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json`
- No-rewire review contract (PR #5058): `docs/research/bull_bear_state_switch_backtest_parity_narrow_rewire_v0.json`
- Owner binding contract: `docs/research/bull_bear_state_switch_owner_binding_implementation_v0.json`
- Owner binding implementation: `src/research/owner_bindings/bull_bear_state_switch_owner_binding_v0.py`
- Source evidence MANIFEST.sha256 verified with RC=0 for both PR #5057 and PR #5058 durable bundles

## Canonical Wiring Evidence

| Evidence | Path |
|---|---|
| Canonical owner | `src/trading/master_v2` (`trading.master_v2.double_play_state.transition_state`) |
| Scenario binding adapter | `src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py` |
| Backtest consumer | `src/trading/master_v2/offline_double_play_scenario_replay_v0.py` |
| Parity harness | `src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py` |
| Parity contract | `tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py` |

Offline scenario replay invokes `evaluate_scenario_state_switch_v0` and routes through the canonical adapter to `transition_state`. PR #5058 classified `REVIEW_NO_REWIRE_REQUIRED`; no bypass or duplicate owner path is reproducible from origin/main.

## Mirrored Behavior and Bypass Exclusion

- Mirrored bull/bear side-state parity verified via deterministic fixture and harness paths
- Legacy duplicate `transition_state` logic absent from backtest consumer
- Bypass authority excluded; adapter calls canonical owner only

## Limitations and Non-Claims

- Surface-only assertion; does not imply whole-system `BACKTEST_RUNTIME_DECISION_PARITY_PASS`
- Does not claim `FULL_CANONICAL_CHAIN_WIRED`
- Does not claim `SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE`
- Does not authorize `RUNTIME_REWIRE_ADMISSIBLE`
- Does not assert parity from direct reference count alone
- Assertion is invalidated if canonical owner or backtest consumer paths change materially since PR #5058

## Next Parity Surface

`SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`
