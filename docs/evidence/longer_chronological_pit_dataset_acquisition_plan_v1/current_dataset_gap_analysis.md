# Current dataset gap analysis

## Sealed current dataset

| Field | Value |
|---|---|
| Dataset ID | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` |
| Period | `2024-05-01T00:00:00Z..2024-09-01T00:00:00Z` (~4 months) |
| Instruments | 118 (binding = manifest) |
| Frequency | PT1H |
| Venue &#47; market | OKX linear USDT futures; BTC excluded; spot excluded |
| PIT claim | `pit_safe=true` on sealed evidence |
| Panel rows | 348454 (sealed evidence) |
| Longer period available locally | **false** |

## Binding blocker (verbatim from sealed evidence)

```text
NO_LONGER_CHRONOLOGICAL_PIT_OKX_LINEAR_USDT_NON_BTC_DATASET_THAN_2024-05-01..2024-09-01;
max local coverage equals prior sample period;
cross-sectional expansion to full 118-member panel used instead
```

## What the short window breaks

| Need | Status on current panel |
|---|---|
| Multi-year chronologic Walk-Forward | FAIL — only ~3 coarse folds inside 4 months; sign unstable (#5350) |
| Regime slices (bull &#47; bear &#47; chop over years) | FAIL — insufficient calendar depth |
| Leave-one-instrument-out stability over regimes | PARTIAL — LOO exists but regime-conditioned LOO impossible |
| Stress vs structural edge | INCONCLUSIVE — cost stress flips sign; period too short to separate noise |
| Survivorship-safe expansion across listings | UNKNOWN beyond sealed window — need lifecycle history |

## What is already good enough to keep

- Measurement contract after #5349 (`COST_APPLICATION=APPLIED`, shared portfolio equity)
- Universe policy: non-BTC linear USDT, survivorship forbidden
- Panel validation codes (gap &#47; duplicate &#47; OHLC &#47; no forward fill)
- Public fetch helpers for candles &#47; funding (rate-limited)

## Gap categories

1. **Chronological depth** — primary blocker for promotion-grade robustness claims.
2. **Lifecycle metadata depth** — listing &#47; delisting history across years must be acquired &#47; validated, not inferred from today's instrument list.
3. **Fee schedule history** — current research uses bound constants; multi-year economics need versioned fee provenance or explicit PROXY tagging.
4. **Spread &#47; orderbook history** — generally absent on public path; slippage remains model PROXY unless commercial L2 is approved later.
5. **Public API history depth** — UNCERTAIN until a bounded probe (no bulk download) measures max reachable candle &#47; funding history per instrument.

## Conservative conclusion

Cross-sectional width (118) was expanded; chronological length was not. The next admissible research step is a **new versioned chrono dataset**, not parameter tuning on the 4-month panel.
