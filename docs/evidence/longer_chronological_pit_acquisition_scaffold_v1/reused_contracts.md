# Reused contracts (PR #5351 alignment)

| Concern | Reused owner |
|---|---|
| Proposed dataset ID | PR #5351 plan verdict `..._chrono_3y_v1` |
| PT1H &#47; UTC &#47; no forward fill | `src&#47;research&#47;pit_okx_pt1h_panel_ohlcv_dataset_v1.py` semantics |
| PIT universe &#47; listing &#47; delisting fields | `src&#47;research&#47;pit_futures_universe_manifest_v1.py` |
| Public candle &#47; funding locators | Patterns from `cross_sectional_bounded_panel_fetch_v0` + CDN funding archive owners |
| Canonical JSON hashing | `src&#47;execution&#47;replay_pack&#47;canonical.py` (`dumps_canonical`) |
| BTC &#47; spot exclusion | Explicit planner gates (aligned with lifecycle exclusion codes) |
| External archive env pattern | Same fail-closed spirit as other `PEAK_TRADE_*_ROOT` contracts |

No parallel economic truth. No Master-V2 &#47; Double-Play mutation.
