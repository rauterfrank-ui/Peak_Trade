# Flat Before Opposite Side Backtest Parity Wiring Assessment or Narrow Rewire v0

Verdict: `PASS_FLAT_BEFORE_OPPOSITE_SIDE_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0`

Assessment Status: `WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE`

## Scope

This slice assesses whether the canonical backtest and offline replay decision chain fully represents the flat-before-opposite-side invariant. It is authority-neutral: no backtest execution, no economic evidence, no runtime mutation, and no canonical trading-semantic change.

## Surface Flags

| Flag | Value |
|---|---|
| `FLAT_BEFORE_OPPOSITE_SIDE_BACKTEST_PARITY_STATUS` | `WIRED` |
| `FLAT_BEFORE_OPPOSITE_SIDE_BACKTEST_PARITY_PASS` | `true` |
| `OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT` | `true` |
| `VENUE_FLAT_ALONE_SUFFICIENT` | `false` |
| `EXIT_BEFORE_OPPOSITE_SIDE` | `true` |
| `POSITION_FLIP_ALLOWED` | `false` |
| `REDUCE_ONLY_EXIT_PRESERVED` | `true` |
| `LONG_TO_SHORT_SYMMETRY_PASS` | `true` |
| `SHORT_TO_LONG_SYMMETRY_PASS` | `true` |
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
| Entry-exit decision (SSOT) | `trading.master_v2.double_play_entry_exit_policy_v0` | `_effective_flat`, `_entry_preconditions_met`, `position_flip_allowed=False` |
| Integrated replay orchestrator | `trading.master_v2.integrated_offline_trading_logic_replay_v1` | Calls canonical policy fail-closed |
| Offline scenario binding | `trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0` | Merges side-state position evidence before policy evaluation |
| Backtest consumer | `src/backtest/mv2_research_wiring_v1.py` | Bar-loop → integrated replay |

## Call Paths

### Backtest bar-loop

`src/backtest/mv2_research_wiring_v1.py` → `run_integrated_offline_trading_logic_replay_v1()` → `evaluate_double_play_entry_exit_policy_v0()`.

### Offline scenario replay

`src/trading/master_v2/offline_double_play_scenario_replay_v0.py` → `evaluate_scenario_flat_before_opposite_side_entry_exit_v0()` → canonical entry-exit policy via reversal-preparation adapter chain.

## Decision Precedence Evidence

- Opposite-side entry requires `PositionState.FLAT_RECONCILED`; venue-flat alone is insufficient (`_effective_flat`).
- Reconciliation must be `RECONCILED`; unresolved submission, partial fill, and exit-pending states block entry.
- Reversal preparation produces reduce-only exit before opposite-side entry; direct long→short or short→long flip is blocked (`position_flip_allowed=False`).
- Long→short and short→long negative paths verified symmetrically in parity contract tests.

## Gap Review

| Check | Reproducible |
|---|---|
| bypass path | false |
| duplicate decision path | false |
| missing owner call | false |
| missing parity contract | false |
| integrated replay calls canonical entry-exit policy | true |
| scenario replay flat-before adapter bound | true |
| integrated side-state position merge bound | false |
| backtest bar-loop static flat default position state | true |

Prior narrow reuse-first rewire evidence binds offline scenario replay through canonical owners (`TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH`). Integrated replay consumes the canonical policy directly; side-state merge is scenario-replay wiring only and does not reproduce a bypass or parallel trading SSOT.

## Narrow Rewire Decision

`rewire_implemented=false` and `rewire_required=false` in this slice. Existing wiring is complete for the assessed surface; only manifest-verified PASS assertion evidence is added.

## Prior Surface

`SCOPE_ADVERSE_EXIT_REVERSAL_BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_SURFACE_ONLY_V0` (PR #5062)
