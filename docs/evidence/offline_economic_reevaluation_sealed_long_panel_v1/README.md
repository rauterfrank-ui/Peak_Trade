# Offline economic reevaluation on sealed long panel v1

```text
SLICE=OFFLINE_ECONOMIC_REEVALUATION_SEALED_LONG_PANEL_V1
BASE_SHA=3cc71231dd8fc52ea9f2274e68c584555d31155b
BRANCH=audit/offline-economic-reevaluation-sealed-long-panel-v1
PRODUCTIVE_FILES_CHANGED=false
STATUS=FAIL
ECONOMIC_CLASS=FAIL_ECONOMIC
ECONOMIC_MEASUREMENT_VALID=true
COST_APPLICATION=APPLIED
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
RUNTIME_STARTED=false
ORDERS=false
LIVE_AUTHORIZED=false
```

## Verdict

Kanonische Messkette (post-#5348 Kosten + Shared-Book) auf dem versiegelten 65er
Long-Panel ist **messgültig**, aber wirtschaftlich **nicht tragfähig**
(`FAIL_ECONOMIC`): Net Return negativ, Profit Factor 0 (alle 303 Roundtrips via
`stop_loss`), alle 4 chronologischen OOS-Folds negativ, Kostenstress verschärft
den Verlust. Keine Promotion.

## Panel bind

| Field | Value |
|---|---|
| Dataset | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1` |
| Instruments | 65 |
| Common panel | `2023-08-16T05:55:00Z` .. `2024-09-01T00:00:00Z` |
| Sealed manifest SHA256 | `f4c616c556ff3f2500bb5deff2070c5ee9c4b6a5d5d6ca5da3dc7aca1e8a3e56` |
| Content hash | `7bcda794ae2a355c6f36b2ea04703f39078063458f52034add44bec5644206bb` |
| Registry digest | `ddcdec738ff5661f3e2f6bd3dcc97a1bcddbf0b9254faa344b318558f1dbe289` |
| Config | `bollinger_bands_v2_full_canonical_system_economic_binding_v1` |
| Seed / fee / slip / stop | 42 / 10 bps / 5 bps / 2.5% |

## Shared-book baseline

| Field | Value |
|---|---:|
| Trades (L/S) | 303 (15/288) |
| Gross / Fees / Slip / Net PnL | -228.949974 / 18.521888 / 9.260944 / -256.732807 |
| Net return | -0.025673 |
| Sharpe (hourly→8760) | -9.270642 |
| Max DD | -0.025673 |
| Profit factor (net) | 0.0 |
| Cost drag (abs / bps vs capital) | 27.782832 / 27.7828 |
| Exit reasons | all `stop_loss` |

## Robustness (read-only)

- Walk-forward: 4/4 OOS folds negative
- Monte Carlo (500, seed 42): median net return ≈ -0.025673; p05 ≈ -0.025715
- Loss concentration: worst-1 abs share ≈ 0.0454; worst-5 ≈ 0.1986
- Materialization note: public OHLCV only → `mark_price=close` proxy; funding not acquired (=0)

## Safety

Gate/Promotion closed. Evidence-only. No productive strategy/risk/execution mutation.
