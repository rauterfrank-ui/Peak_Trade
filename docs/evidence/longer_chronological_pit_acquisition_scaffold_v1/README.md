# Longer chronological PIT acquisition scaffold v1

```text
SLICE=LONGER_CHRONOLOGICAL_PIT_ACQUISITION_SCAFFOLD_V1
BASE_SHA=b242db1b3b16582ff5b63153f647e980f1469e4a
BRANCH=feat/longer-chronological-pit-acquisition-scaffold-v1
REFERENCE_PLAN_PR=5351
STATUS=PASS
PRODUCTIVE_TRADING_FILES_CHANGED=false
DATA_ARCHIVES_ADDED_TO_GIT=false
NETWORK_USED=false
MASS_DOWNLOAD_STARTED=false
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
LIVE_AUTHORIZED=false
ORDERS=false
```

## Purpose

Phase-1 scaffold implementing the acquisition architecture from PR #5351:

- external archive root contract (`PEAK_TRADE_DATA_ARCHIVE_ROOT`)
- public-first OKX source discovery (no network in defaults)
- monthly lifecycle-aware partition planner
- deterministic acquisition manifest
- resume state machine
- dry-run qualification CLI
- probe-gated adapter (network off by default)

## Dataset

`pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1`

Target period: `2021-09-01T00:00:00Z..2024-09-01T00:00:00Z` (PT1H, UTC).

## Defaults

| Flag | Default |
|---|---|
| Dry-run | true |
| Network | disabled |
| Write | disabled |
| Credentials | none |

## Safety

No mass download, no trading-core changes, Economic Gate closed.
