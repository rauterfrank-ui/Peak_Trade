# Visual Foundation Rework v1 — Implementation Manifest

```text
SLICE=VISUAL_FOUNDATION_REWORK_V1
GO_TOKEN=GO_VISUAL_OPERATOR_DASHBOARD_REWORK_FOUNDATION_V1
BASE=origin/main@880bc9a1dde0d9d3be1c80c5f53bd060afecef31
PR_5247=MERGED
PR_5248=CLOSED_NOT_MERGED
BRANCH=feat/market-dashboard-visual-foundation-rework-v1
RUNBOOK_PATH=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
RUNBOOK_SHA256=cb07ca30310056a3f7f3639763a8c2774c2fe5de527666446f7b269c6b0d82c0
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_PLAYWRIGHT_CHANNEL=chrome
HARNESS=scripts/webui/market_dashboard_chrome_playwright_harness_v1.py
```

## Scope delivered

- Compact global header (Operator Console + Snapshot/Source/Freshness + Read only)
- Quiet safety rail (3 signals, no 8-col badge wall)
- Hero 8/4: instrument primacy + system decision / primary blocker / Economic·Risk·Safety
- Dominant primary chart (min height 390px, compact meta row)
- Design tokens + layout composition contract
- Focused tests + Chrome Playwright harness composition fields
- Canonical runbook v1.3 updated in place (DesignGate / Chrome / Playwright / VisualContract)

## Non-scope (confirmed)

- No ranking/decision/risk/economic producer changes
- No core/strategy/authority/live/orders semantics
- No blind merge of PR #5248 technical chart polish (branch retained for inventory)

## Tests

See `test_output/focused_tests.txt`.

## Chrome Playwright composition (1440×900)

```text
BROWSER_ACTUAL=GOOGLE_CHROME
REAL_CHROME_VERIFIED=true
HEADER_HEIGHT_PX=45.6875
SAFETY_RAIL_HEIGHT_PX=17.0
HERO_HEIGHT_PX=210.0
CHART_HEIGHT_PX=390.0
PRIMARY_CHART_VISUAL_SHARE_PCT=57.67
PRIMARY_CHART_VISUAL_SHARE_MIN_MET=true
CHART_TOP_VISIBLE_1440x900=true
CHART_MATERIALLY_VISIBLE_1440x900=true
COMPOSITION_CONTRACT_PASS=true
HORIZONTAL_OVERFLOW=false
CONSOLE_ERRORS=0
```

Evidence report: `browser/browser_evidence_report.json`
