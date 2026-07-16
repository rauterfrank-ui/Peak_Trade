# Phase 3 Browser Verification Report

```text
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_AUTOMATION=PLAYWRIGHT
PRIMARY_PLAYWRIGHT_CHANNEL=chrome
BROWSER_ACTUAL=GOOGLE_CHROME
REAL_CHROME_VERIFIED=true
CHROMIUM_FALLBACK_USED=false
WEBKIT_VERIFIED=NOT_RUN
REAL_SAFARI_VERIFIED=NOT_RUN
CONSOLE_ERRORS=0
PAGE_ERRORS=0
FAILED_ASSETS=0
UNEXPECTED_NETWORK_REQUESTS=0
EXTERNAL_NETWORK_REQUESTS=0
NETWORK_ASSERTIONS=SELF_ONLY_PASS
HORIZONTAL_OVERFLOW=false
CHART_TOP_VISIBLE_1440x900=true
CHART_MATERIALLY_VISIBLE_1440x900=true
HARNESS=scripts/webui/market_dashboard_chrome_playwright_harness_v1.py
HARNESS_PHASE=3
BASE_URL=http://127.0.0.1:8766
DEFAULT_PATH=/market?timeframe=1d&limit=120
MACHINE_REPORT=docs/product/evidence/phase_3_20260716T191523Z/browser/browser_evidence_report.json
```

## Screenshot inventory (full repo paths)

1. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_default_1440x900.png`
2. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_full_desktop.png`
3. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_narrow_desktop.png`
4. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_selected_instrument.png`
5. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_tooltip_or_equivalent_detail_state.png`
6. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_stale_state.png`
7. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_missing_or_incomplete_state.png`
8. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_with_volume.png`
9. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/above_fold_with_chart.png`
10. `docs/product/evidence/phase_3_20260716T191523Z/screenshots/chart_wide_1728x1117.png`

```text
SCREENSHOT_COUNT=10
chart_gap_state=NOT_CAPTURED_NO_REAL_GAP_IN_FIXTURE
```

Stale capture used a dedicated read-only fixture server on `127.0.0.1:8767` with `stale=true` OHLCV JSON (no invented candles). Overlay count verified = 1.
