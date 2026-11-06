# Proposed Implementation Slice (Post-Ratification Only)

**This file is a plan only. No implementation in the current slice.**

## Gate

```text
BLOCKED_UNTIL=STRATEGY_SEMANTIC_RATIFICATION_REQUIRED
```

Do not start OPTION_A or OPTION_C code until an explicit Operator-GO resolves:

- CP02 (`1 (long)` vs `1=entry`)
- Whether Bollinger ENTRY is LONG-only intent, event-only, or intent+DP-match
- SHORT: absent forever vs future geometry

## If ratification chooses LONG-only (then OPTION_A-style activation)

### Allowed productive files (minimal)

- `src/strategies/bollinger.py` — doc/contract alignment only (no formula change unless GO says so)
- `src/backtest/strategy_signal_suitability_agreement_adapter_v1.py` — add producer-scoped ratification for `bollinger_bands` ENTRY→LONG
- Governance SSOT JSON + narrative under `config/governance/` + `docs/governance/`

### Forbidden owners

- `double_play_state.py::transition_state` / `RuntimeScopeState` / dynamic scope
- Composition matrix as side inventor
- Risk/sizing/execution side rewrite
- `compose_double_play_decision` (legacy residual)
- Runtime bridge activation / LIVE / ORDERS
- Projecting `entry_side` from selected Bull/Bear (OPTION_B)

### Required contracts / tests

| Type | Cases |
|------|-------|
| Positive LONG | Bollinger ENTRY `+1` → `entry_side=LONG`; directional cycle `+1` |
| Positive SHORT | **Expect fail** or skip until SHORT geometry ratified — do not fake SHORT |
| Negative NONE | EXIT `-1` → NONE; flat `0` → NONE; other producers unchanged |
| Negative inference | `cycle_signal_value=+1` alone must not authorize LONG without ratification path |
| Conflict | If OPTION_C later: intent≠selected_side → fail-closed |
| Serialization / backward compat | Material with missing `entry_side` → NONE |
| Parity / Surface-P | Existing Surface-P + CRS/OI non-authority suites remain green |
| Quarantine | Sole-authority quarantine still PASS |

### Non-goals

- No SHORT invent from EXIT
- No runtime/testnet/orders/live
- No generic assert weakening
- No competing authority paths

### Abort criteria

- Any attempt to infer side from sign without producer ratification
- Any OPTION_B projection
- Surface-P / quarantine regression
- CP02 left contradictory while emitting LONG

### Expected next blocker after successful LONG activation

```text
Likely: COMPOSITION_OBSERVE / AGREEMENT mismatch or suitability — not CRS/qty first
(TF impact diagnostic precedent: DA clears → later stages dominate)
```

## If ratification chooses event-only

- Keep adapter NONE forever for Bollinger
- Document `EVENT_ONLY_NO_SIDE_AUTHORITY`
- Zero-trade on Bollinger ENTRY remains intentional
- Next economic work: different strategy binding (e.g. already-ratified TF) — not Bollinger side

## If ratification chooses OPTION_C architecture

- Additional allowed file: agreement match gate near `resolve_agreement_bound_directional_cycle_v1` / suitability binding (reuse-before-new)
- Tests: match / mismatch / unbound selected_side
- Still requires explicit producer intent semantics first
