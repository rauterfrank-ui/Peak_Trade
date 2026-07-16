# Landmark Discovery Delta v1

GO_TOKEN: `GO_VISUAL_OPERATOR_DASHBOARD_LANDMARK_DISCOVERY_DELTA_PR_OPEN_STOP_BEFORE_MERGE_V1`

HEAD: `2b936808c7c99687def5e9c4597e3fe55de0e58f`
ORIGIN_MAIN: `2b936808c7c99687def5e9c4597e3fe55de0e58f`
CANONICAL_RUNBOOK: `docs&#47;product&#47;Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md`

## Purpose

Read-only binding of Runbook v1.3 Landmark&#47;Composition contracts to the current repository render chain after merge of PR #5252 (review server harness).

## Render Chain

- Route: `GET &#47;market`
- Route owner: `src&#47;webui&#47;market_surface.py`
- Resolver: `resolve_market_page_data`
- Context: `build_market_v0_page_template_context`
- Template: `templates&#47;peak_trade_dashboard&#47;market_v0.html` extends `base.html`
- Review server: `scripts&#47;webui&#47;review_server.sh`
- Browser harness: `scripts&#47;webui&#47;market_dashboard_chrome_playwright_harness_v1.py`

## Landmark Owners

See `landmark_owner_matrix.json`. Observed DOM order:

`GLOBAL_HEADER -> PRIMARY_MARKET_SURFACE -> DECISION_SURFACE -> OBSERVABILITY_SURFACE -> ENGINEERING_DRAWER`

## Composition Baseline (1440x900)

- HEADER_HEIGHT_PX=45.69
- PRIMARY_CHART_TOP_Y=381.47
- PRIMARY_CHART_VISIBLE_HEIGHT_PX=518.53
- HORIZONTAL_OVERFLOW_PX=0.00
- ENGINEERING_DRAWER_DEFAULT_HIDDEN=True
- REAL_CHROME_VERIFIED=True
- UNEXPECTED_EXTERNAL_NETWORK_REQUESTS=0
- CONSOLE_ERRORS=0

## Key Defects

- LDD-01 EYE_PATH_BROKEN (decision narrative above chart)
- LDD-02 missing explicit landmark markers
- LDD-03 Decision&#47;Observability mixed secondary grid
- LDD-04 multiple engineering details vs single drawer
- LDD-05 ranking density
- LDD-06 residual card-like chrome

## Next Slice

`PHASE_1A_COMPOSITION_FOUNDATION` — presentation-only composition&#47;landmark foundation.
Expected GO_TOKEN: `GO_VISUAL_OPERATOR_DASHBOARD_PHASE_1A_COMPOSITION_FOUNDATION_V1`

## Safety

- PRODUCTIVE_DASHBOARD_UI_MUTATION=false
- DASHBOARD_IS_CONSUMER_ONLY=true
- LIVE_AUTHORIZED=false
- ORDERS_ALLOWED=false
- STOP_BEFORE_MERGE=true
