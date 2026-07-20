# Longer chronological PIT — OKX history-depth probe v1

```text
SLICE=LONGER_CHRONOLOGICAL_PIT_OKX_HISTORY_DEPTH_PROBE_V1
PR_NUMBER=5352
BRANCH=feat/longer-chronological-pit-acquisition-scaffold-v1
NETWORK_PROBE_EXECUTED=true
MASS_DOWNLOAD_STARTED=false
CREDENTIALS_USED=false
ORDERS=false
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
LIVE_AUTHORIZED=false
```

## Purpose

Bounded public OKX `history-candles` depth probe for the planned
`..._chrono_3y_v1` dataset. Confirms Phase-1 scaffold behavior through the
network boundary only. No mass download. No economic evaluation.

## CLI

```text
python -m src.research.longer_chronological_pit_acquisition_v1 history-depth-probe
  # defaults: no network, no write

python -m src.research.longer_chronological_pit_acquisition_v1 history-depth-probe \
  --allow-network-probe --allow-write-probe --request-budget 25 \
  --max-instruments 5 --archive-root "$PEAK_TRADE_DATA_ARCHIVE_ROOT"
```

## Probe sample (deterministic)

Policy-compatible scaffold lifecycle sample (not a second production universe
manifest). Roles: oldest / middle / youngest / edge_near_period_start / fill.

| Instrument | Role | Earliest public PT1H | Latest public | 3y depth |
|---|---|---|---|---|
| ETH-USDT-SWAP | oldest | 2021-08-23T16:00:00Z | 2026-07-20T17:00:00Z | YES |
| LINK-USDT-SWAP | fill | 2020-06-06T17:00:00Z | 2026-07-20T17:00:00Z | YES |
| SOL-USDT-SWAP | edge_near_period_start | 2021-05-23T17:00:00Z | 2026-07-20T17:00:00Z | YES |
| LUNA-USDT-SWAP | middle (delist edge) | 2026-07-12T10:00:00Z | 2026-07-20T17:00:00Z | NO |
| TIA-USDT-SWAP | youngest | 2023-10-31T18:00:00Z | 2026-07-20T17:00:00Z | YES |

- Request budget: 25; used: 20 (4 per instrument)
- Endpoint: `https://www.okx.com/api/v5/market/history-candles` only
- BTC excluded; Spot excluded; Futures-only Linear USDT Swap
- External archive root (git-foreign):
  `${TMPDIR}&#47;peak_trade_data_archive&#47;okx_history_depth_probe_v1`

## Lifecycle clipping

Overall `lifecycle_clipping_valid=false` because sample `listing_time` values for
LINK/SOL/TIA are slightly after observed public earliest candles. Planner
`planned_start` still clips to the sample listing. LUNA shows recent-only public
history after a 2022 sample delisting (likely relisted contract continuity).

## Safety attestation

- no credentials
- no orders
- no mass download
- no economic reevaluation
- Economic Gate closed
- Promotion not eligible
- no archive payloads committed to git (hashes only)

## Files

| File | Role |
|---|---|
| `probe_summary.json` | Machine-readable probe result |
| `request_budget_endpoint_instrument_overview.json` | Budget / endpoint / timestamps |
| `external_artifact_hashes.json` | SHA256 of external probe artifacts |
| `manifest_resume_attestation.json` | Manifest digest + resume state proof |
| `limitations_and_blockers.md` | Limitations / blockers |
| `safety_attestation.md` | Explicit safety statements |
| `tests.txt` | Focused test evidence |
