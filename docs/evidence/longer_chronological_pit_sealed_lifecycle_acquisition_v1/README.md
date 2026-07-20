# Longer chronological PIT — sealed production lifecycle + bounded acquisition v1

```text
SLICE=LONGER_CHRONOLOGICAL_PIT_SEALED_LIFECYCLE_ACQUISITION_V1
BASE_SHA=d884a000d03d7859c9d262a932cf77cba01e5eb7
BRANCH=feat/sealed-production-lifecycle-pit-acquisition-v1
NETWORK_EXECUTED=true
MASS_UNBOUNDED_DOWNLOAD=false
CREDENTIALS_USED=false
ORDERS=false
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
LIVE_AUTHORIZED=false
```

## Purpose

Bind the existing production PIT futures lifecycle registry SSOT (not the
scaffold sample), seal a long-panel inclusion set under a versioned policy
(>=365 usable days), and run a bounded public OKX PT1H acquisition for the
common panel window. No economic reevaluation in this slice.

## Production binding

- Source: `okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1`
- Registry: external `registry_snapshot_v1.json` (digest recorded in seal)
- Universe truth: `production_lifecycle_registry_binding_v1`
- Sample universe cannot be emitted as production (fail-closed)

## CLI

```text
python -m src.research.longer_chronological_pit_acquisition_v1 seal-lifecycle \
  --production-registry-json "$REGISTRY_SNAPSHOT" \
  --allow-network-probe --allow-write-seal --seal-request-budget 2500 \
  --archive-root "$PEAK_TRADE_DATA_ARCHIVE_ROOT"

python -m src.research.longer_chronological_pit_acquisition_v1 acquire-long-panel \
  --sealed-manifest-json "$SEALED_MANIFEST" \
  --allow-network-probe --allow-write-acquisition \
  --acquisition-request-budget 8000 \
  --archive-root "$PEAK_TRADE_DATA_ARCHIVE_ROOT"
```

## Safety

- Public endpoints only (`/api/v5/public/instruments`, `/api/v5/market/history-candles`)
- BTC / Spot excluded
- Economic Gate closed
- Raw archives external only (hashes in git evidence)


## Result snapshot

- Long panel included: 65
- Common panel: 2023-08-16T05:55:00Z .. 2024-09-01T00:00:00Z (381.75d)
- Acquired bars/pages: 595530/5980
- Gaps/dups/ordering: 0/0/0
- ECONOMIC_REEVALUATION_READY=True
- LUNA_DECISION=INCLUDE_LONG_PANEL
