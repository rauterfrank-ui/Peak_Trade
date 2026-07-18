# Authority Analysis

## Checks (both components)

| Capability | Ehlers | Bouchaud | Evidence |
|---|---|---|---|
| Set Bull/Bear directly | No | No | No MV2 references |
| Set LONG/SHORT as system authority | Produces long/flat **signals** only if selected; not system authority | Same | Strategy `generate_signals`; agreement side stays NEUTRAL |
| Change Dynamic Scope | No | No | Not bound |
| Trigger transition_state / Dynamic Switch | No | No | Not bound |
| Override Agreement | No | No | Encoding helper only |
| Bypass Composition | No | No | Not default composite children |
| Force CRS / Order Intent | No | No | Live gates false |
| Bypass Risk gates | No | No | — |
| Force position size / quantity | No | No | Offline sizing policy ≠ runtime force |
| Set execution eligibility | No (`IS_LIVE_READY=False`) | No | Registry + class constants |
| Direct Trade Intent (live) | No | No | — |
| Activate legacy compatibility paths | No | No | — |

## Path classifications

| Path | Classification |
|---|---|
| Ehlers Super Smoother → offline/backtest signal if strategy selected | **SAFE_STRATEGY_INTENT** (research-gated) |
| Ehlers Hilbert/Bandpass stubs | **INACTIVE_OR_UNBOUND** |
| Ehlers STEP29M offline binding | **INACTIVE_OR_UNBOUND** w.r.t. MV2; research authority_effect NONE |
| Bouchaud OHLCV/proxy `generate_signals` | **SAFE_STRATEGY_INTENT** (research-gated; proxy) |
| Bouchaud feature matrix / linear diagnostics | **SAFE_INFORMATION_SOURCE** / research-only |
| Bouchaud propagator/trade-sign config knobs | **INACTIVE_OR_UNBOUND** |
| Agreement encoding inclusion (`POSITIONAL_LONG01`) | **SAFE_NON_AUTHORITY_PROJECTION** (maps to NEUTRAL) |
| Generic `estimated_market_impact` observability | **SAFE_NON_AUTHORITY_PROJECTION** (false-positive for Bouchaud) |

## Competing authority

- **CONFIRMED_COMPETING_AUTHORITY:** none (`COMPETING_AUTHORITY_COUNT=0`)
- **POTENTIAL** only if an operator later selects these as executed strategies inside an Agreement/CRS path without governance — current repo state does not activate that.

## Legacy productive

`LEGACY_PRODUCTIVE_COUNT=0` for Ehlers/Bouchaud (no legacy functional alias analogous to ECM for these names).
