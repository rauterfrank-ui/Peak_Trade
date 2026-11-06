# Bypass and Competing Authority Findings

## Competing Authority Count

```text
COMPETING_AUTHORITY_COUNT=0
```

No productive path invents Bollinger `entry_side` ∈ {LONG, SHORT} beside Master V2 &#47; Double Play. OBL_B07 + adapter branch + material guard keep Bollinger at `NONE`.

## Confirmed Bypass Count

```text
CONFIRMED_BYPASS_COUNT=1
```

| # | Path | Behavior | Canonical? |
|---|------|----------|------------|
| 1 | `BacktestEngine.run_realistic` | `signal==1` → LONG ENTRY; `signal==-1` → EXIT long | **No** — Legacy&#47;Compatibility. OBL_B07: `CLASSIC_LONG_IS_CANONICAL=false`, `CLASSIC_LONG_PROPAGATES_TO_INTEGRATED=false` |

## Residual asymmetry (not counted as competing entry-side authority)

| Path | Behavior | Risk |
|------|----------|------|
| `suitability_binding_v1.derive_effective_strategy_side_agreement_v1` | ENTRY_EXIT ENTRY impulse AGREE only vs LONG DA; does not consult `entry_side` | MEDIUM suitability demotion bias; does **not** emit carrier LONG for Bollinger |

## Strategy → Order shortcuts

- Integrated&#47;MV2: Bollinger ENTRY with `entry_side=NONE` → `resolve_agreement_bound_directional_cycle_v1` returns `None` → not executable.
- Runtime bridge: `BOUND_NOT_ACTIVATED`, `authority_effect=NONE`.
- Live&#47;Orders: false.

## Legacy compose

`compose_double_play_decision` does not set Bollinger `entry_side`; residual eligibility&#47;dashboard surface, not SideState SSOT.
