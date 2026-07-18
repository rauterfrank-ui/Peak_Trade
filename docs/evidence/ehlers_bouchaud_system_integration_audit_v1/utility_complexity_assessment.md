# Utility & Complexity Assessment

## Ehlers

| Question | Assessment |
|---|---|
| Problem to solve | Reduce lag/noise vs EMA; cycle timing for entries |
| Already solved canonically? | Trend/filter roles partially covered by MA/trend_following/vol filters; **cycle authority** is Armstrong/ECM calendar family, not Ehlers |
| Incremental information? | Super Smoother may differ from EMA; **unproven** for Peak_Trade futures (offline baseline terminal inconclusive) |
| Redundancy | High overlap with generic MA crossover semantics (close vs smooth) |
| Decision quality vs complexity | Docs/config advertise Hilbert/Bandpass while stubs unused → **complexity without delivered method** |
| Auditable/reproducible? | Yes for Super Smoother path (deterministic recursion) |
| Evidence | Profile shows poor BTC sample metrics; STEP29M terminal inconclusive |
| Overfitting risk | Medium if presets expand unused params without method completion |
| Data quality risk | Low for OHLCV close |
| Sensible later use | Keep as research filter feature; **not** MV2 authority |

**Recommendation: KEEP_RESEARCH_ONLY**

## Bouchaud

| Question | Assessment |
|---|---|
| Problem to solve | Microstructure pressure / impact-aware timing or cost |
| Already solved canonically? | Observability has generic participation impact proxy; risk kernel has impact BPS guards — **not** Bouchaud laws |
| Incremental information? | Unclear; OHLCV proxies are weak substitutes for order flow |
| Redundancy | Close-vs-SMA and bar-pressure overlap momentum/mean-reversion features |
| Decision quality vs complexity | Large research/governance surface around a thin proxy → **high complexity / low microstructure fidelity** |
| Auditable/reproducible? | Strategy path deterministic; features labeled proxy |
| Evidence | Offline baseline inconclusive; retry blocks; tick/L2 scope reserved separately |
| Overfitting risk | High if proxy features promoted without tick data |
| Proxy data risk | **HIGH** |
| Sensible later use | Only after tick/L2 data + true method + non-claim repair; candidate for cost/execution research later, **not now** |

**Recommendation: KEEP_RESEARCH_ONLY**

## Placement vs Master V2 / Double Play

Current placement (registry R&D + offline research bindings, **outside** MV2 chain) is **correct**. Pulling either into Dynamic Scope, Agreement authority, or CRS would overload the canonical Double Play logic without proportional evidence.
