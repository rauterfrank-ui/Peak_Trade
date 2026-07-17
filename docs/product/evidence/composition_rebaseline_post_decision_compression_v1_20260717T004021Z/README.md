# Composition Rebaseline — Post Decision Compression v1

Timestamp (UTC dir): `composition_rebaseline_post_decision_compression_v1_20260717T004021Z`
Repository HEAD: `8fa865061e671d065e93ad5619ce263b91c46fee`
Branch: `main` (= `origin/main`)
Mode: **READ-ONLY** capture + composition analysis (no code changes, no commit, no PR)

## Purpose

1. Rebaseline full-page composition after merge of `COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1` (PR #5259).
2. Analyze landmark hierarchy, rhythm, whitespace, scan path, and Decision/Observability balance.
3. Produce a prioritized next-slice backlog with effort / risk / visual gain — **no implementation**.

## Browser

- Primary: Google Chrome via Playwright (`channel=chrome`)
- Harness: `scripts/webui/market_dashboard_chrome_playwright_harness_v1.py`
- `REAL_CHROME_VERIFIED=true`
- `CHROMIUM_FALLBACK_USED=false`
- `EVIDENCE_ACCEPTED=true`

## Dashboard start (this run)

- Host: `127.0.0.1:8765` · path `/market?timeframe=1h`
- Offline visual-operator bundles · depth disabled · authority none
- Process stopped after capture

## Key results @1440×900

| Metric | Pre-compression | Now |
|---|---:|---:|
| Page height | 3377 | **2572** |
| DECISION height / share | 1803 / 53.4% | **1006 / 39.1%** |
| PRIMARY share | 26.1% | **34.2%** |
| OBSERVABILITY start Y | 2812 | **2007** |
| Chart viewport share | 55.4% | **55.4%** (held) |

Gates: landmark order / overflow / chart dominance / engineering secondary — all PASS.

Largest remaining composition gap: **Decision still slightly heavier than Primary on full-page share** (39.1% vs 34.2%); Observability still ~2.2 viewport scrolls down.

## Artifact index

- `README.md`
- `composition_audit.md`
- `next_composition_slices.md`
- `browser_report.json`
- `composition_geometry.json`
- `landmark_order.json`
- `console_and_network_report.json`
- `repository_snapshot.json`
- `ssot_consumer_audit.json`
- `screenshots&#47;full_page_*.png`
- `screenshots&#47;viewport_*.png`
- `MANIFEST.sha256`

## Governance

- Business SSOT: Master V2 + Double Play only
- Dashboard: read-only consumer / display layer
- No productive mutations in this phase
