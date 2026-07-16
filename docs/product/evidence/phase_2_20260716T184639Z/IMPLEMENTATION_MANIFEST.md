# Phase 2 Implementation Manifest — Operator Overview + Chrome-primary Browser Policy

```text
SLICE=PHASE_2
PHASE_2_NAME=OPERATOR_OVERVIEW
GO_TOKEN=GO_VISUAL_OPERATOR_DASHBOARD_PHASE_2_CONTINUE_WITH_CHROME_PRIMARY_POLICY_V1
CANONICAL_PRODUCT_SPEC=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
RUNBOOK_SHA256=fd87909e3dc340bc5ae0f642cbb8114a5311b7d2300dae115667e27e67b64216
RUNBOOK_VERSION_CHANGED=false
SECOND_RUNBOOK_CREATED=false

PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_AUTOMATION=PLAYWRIGHT
PLAYWRIGHT_CHANNEL=chrome
BROWSER_ACTUAL=GOOGLE_CHROME
REAL_CHROME_VERIFIED=true
PLAYWRIGHT_CHROMIUM_FALLBACK_USED=false
CHROMIUM_REPORTED_AS_REAL_CHROME=false
SAFARI_ROLE=SECONDARY_COMPATIBILITY_CHECK
SAFARI_REQUIRED_FOR_NORMAL_SLICE_MERGE=false
REAL_SAFARI_VERIFIED=false
WEBKIT_AUTOMATION_VERIFIED=false
WEBKIT_REPORTED_AS_REAL_SAFARI=false

CHART_TOP_VISIBLE_1440x900=true
CHART_MATERIALLY_VISIBLE_1440x900=true
HORIZONTAL_OVERFLOW=false
CONSOLE_ERRORS=0
PAGE_ERRORS=0
FAILED_ASSETS=0
UNEXPECTED_NETWORK_REQUESTS=0
EXTERNAL_NETWORK_REQUESTS=0

HERO_LAYOUT_REFERENCE=8_COLUMNS_PRIMARY,4_COLUMNS_SYSTEM_STATE
DECISION_NARRATIVE_CONTRACT=true
BARE_ACTIVE_FORBIDDEN_IN_OVERVIEW=true
DASHBOARD_IS_CONSUMER_ONLY=true

DATA_PRODUCER_CHANGED=false
TRADING_SEMANTICS_EFFECT=NONE
RISK_SIZING_SEMANTICS_EFFECT=NONE
DECISION_SEMANTICS_EFFECT=NONE
ECONOMIC_SEMANTICS_EFFECT=NONE
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
STOP_BEFORE_MERGE=true
DESIGN_GATE_FINAL=OPERATOR_REVIEW_REQUIRED
PHASE_3_STARTED=false
```

## Owners / Files

- `docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md` — Browser Verification Policy
- `src/webui/market_visual_operator_surface_v1/operator_overview_display_v1.py` — presentation adapter
- `src/webui/market_surface.py` — wires overview VM into template context
- `templates/peak_trade_dashboard/partials/market_primary_operator_hero_v1.html` — Operator Overview hero
- `static/css/peak_trade_dashboard_layout_v1.css` — 8/4 hero grid owner
- `scripts/webui/market_dashboard_chrome_playwright_harness_v1.py` — Chrome Playwright harness
- `src/webui/app.py` — self-only `/favicon.ico` placeholder (console hygiene)
- `tests/webui/test_market_dashboard_phase_2_operator_overview_v1.py`
- `tests/webui/test_market_dashboard_browser_policy_chrome_primary_v1.py`

## Evidence file targets

- `MANIFEST.sha256`
- `MANIFEST_VERIFY.txt`
- `browser/browser_evidence_report.json`
- `browser/console_log.json`
- `geometry/phase_2_bounding_boxes_1440x900.json`
- `network/browser_network_summary.json`
- `screenshots/phase_2_1440x900_above_fold.png`
- `design_review/DESIGN_REVIEW_PACKAGE.md`
- `proofs/source_provenance_v1.json`
- `test_output/focused_tests.txt`

## Harness

```text
START_CMD=.venv/bin/python -m uvicorn src.webui.app:app --host 127.0.0.1 --port 8766 --no-access-log
PLAYWRIGHT=scripts/webui/market_dashboard_chrome_playwright_harness_v1.py --channel chrome
```
