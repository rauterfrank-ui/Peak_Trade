# Longer Chronological PIT Dataset Acquisition Plan v1

```text
SLICE=LONGER_CHRONOLOGICAL_PIT_DATASET_ACQUISITION_PLAN_V1
BASE_SHA=b242db1b3b16582ff5b63153f647e980f1469e4a
BRANCH=audit/longer-chronological-pit-dataset-acquisition-plan-v1
STATUS=PASS
PRODUCTIVE_FILES_CHANGED=false
ECONOMIC_CLASS=INCONCLUSIVE_UNSTABLE
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
LIVE_AUTHORIZED=false
ORDERS=false
SHADOW=false
PAPER=false
TESTNET=false
DOWNLOADS_STARTED=false
```

## Purpose

Define a fail-closed, reproducible **acquisition and validation plan** for a longer
chronological Point-in-Time (PIT) OKX linear-USDT futures panel so the canonical
Master-V2 &#47; Double-Play economic chain can be re-evaluated with adequate
walk-forward and regime depth.

This workstream is **plan &#47; contract &#47; inventory &#47; evidence only**.
No bulk download, no paid product booking, no private keys, no strategy or
runtime mutation.

## Why now

Post-#5349 measurement is valid. Post-#5350 attribution shows
`INCONCLUSIVE_UNSTABLE` economics dominated by exit inefficiency, SHORT drag,
and cost sensitivity, with binding data limitation:

`NO_LONGER_CHRONOLOGICAL_PIT_OKX_LINEAR_USDT_NON_BTC_DATASET_THAN_2024-05-01..2024-09-01`

## Proposed target

| Field | Value |
|---|---|
| Current dataset | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` |
| Proposed dataset | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1` |
| Venue | OKX |
| Market | linear USDT perpetuals &#47; futures (repo contract) |
| BTC | excluded |
| Spot | excluded |
| Frequency | PT1H |
| Target period (default) | `2021-09-01T00:00:00Z..2024-09-01T00:00:00Z` |
| Public-first path | preferred default |
| Commercial source | operator decision later |

## Safety

Economic Gate stays closed. Promotion stays ineligible. Master V2 remains sole
direction &#47; switch authority. `entry_side=NONE` &#47; OPTION_D unchanged.

## Next recommended action after this PR

`EXECUTE_BOUNDED_PUBLIC_OKX_HISTORY_DEPTH_PROBE_NO_BULK_DOWNLOAD`
