# Next Slice Plan — Decision Surface Vertical Compression

## Problem Statement

Above the fold, the Primary Market Chart already dominates (≥51% viewport share) and Engineering is secondary. On the **full page**, `DECISION_SURFACE` consumes ~53% of page height at 1440×900 (1803 px), burying `OBSERVABILITY_SURFACE` near Y≈2812. Landmark order is correct, but Blickführung after Primary collapses into a Decision wall. The next bounded slice must restore full-page composition rhythm by vertically compressing Decision presentation only.

## Evidence

- Evidence root: this directory
- `composition_geometry.json` aggregate + per-viewport landmark heights
- Full-page screenshots: `screenshots&#47;full_page_1440x900.png`, `1280x800`, `1728x1117`
- `REAL_CHROME_VERIFIED=true`, `CHROMIUM_FALLBACK_USED=false`
- Decision page-share: 53.4% (1440), 53.6% (1280), 50.0% (1728)

## Root Cause

Presentation density inside `DECISION_SURFACE`: Governed Top20 matrix + decision funnel + four-column secondary grid (watchlist / F5 / Double Play / safety) are all fully expanded in normal document flow. No data-contract failure; layout/template density causes the composition defect.

## Chosen single slice

**Title:** `COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1`

**Scope:** Presentation/Layout/Template/CSS only — compress Decision landmark vertical weight while preserving landmark order, consumer-only semantics, and existing ViewModels.

**Target measurable deltas (1440×900, Chrome full-page):**

| Metric | Before (this rebaseline) | After target |
|---|---:|---:|
| DECISION_SURFACE height | 1803 px | ≤ 1350 px |
| DECISION_SURFACE page share | 53.4% | ≤ 40% |
| OBSERVABILITY_SURFACE start Y | 2812 | ≤ 2200 |
| PRIMARY chart viewport share | 55.4% | ≥ 40% (no regression) |
| Engineering initial viewport share | 0% | < 15% (no regression) |
| Horizontal overflow px | 0 | 0 |
| Landmark order | PASS | PASS |

## Explicitly excluded work

- Chart polish / candle redesign (Phase 3 visual chrome)
- Ranking data-contract changes (Phase 4A)
- New producers, ViewModels, or snapshot owners
- Trading / risk / decision / sizing / execution / authority logic
- Runtime, scheduler, live, testnet, paper, shadow activation
- Observability content redesign (unless spacing only as side-effect of Decision compression)
- Engineering Drawer feature work
- Master Runbook PART I mutation
- WebKit/Safari verification as merge gate

## Affected existing owner files

- `templates/peak_trade_dashboard/market_v0.html` (Decision landmark shell / secondary grid composition)
- `templates/peak_trade_dashboard/partials/market_governed_top20_primary_v1.html`
- `templates/peak_trade_dashboard/partials/market_decision_funnel_visual_v1.html`
- `templates/peak_trade_dashboard/partials/market_watchlist_compact_v1.html`
- `templates/peak_trade_dashboard/partials/futures_market_compact_v1.html`
- `templates/peak_trade_dashboard/partials/double_play_market_compact_v1.html`
- `templates/peak_trade_dashboard/partials/market_safety_compact_v1.html`
- `static/css/peak_trade_dashboard_layout_v1.css`
- `static/css/peak_trade_dashboard_design_tokens_v1.css` (Decision density tokens only, if needed)

Reuse existing context builders in `src/webui/market_surface.py` and `market_visual_operator_surface_v1&#47;*` — **no new Python owners**.

## Unchanged Core / SSOT boundaries

```text
BUSINESS_SSOT=MASTER_V2_AND_DOUBLE_PLAY
DASHBOARD_ROLE=READ_ONLY_CONSUMER_DISPLAY_LAYER
DASHBOARD_CREATES_SECOND_TRUTH=false
NO_TRADING_SEMANTICS_EFFECT=true
NO_RUNTIME_AUTHORITY_EFFECT=true
NO_DATA_CONTRACT_CHANGE=true
```

## Acceptance criteria

1. Landmark order remains GLOBAL_HEADER → PRIMARY → DECISION → OBSERVABILITY → ENGINEERING.
2. Decision height/page-share targets met at 1440×900; same direction of improvement at 1280 and 1728.
3. Primary chart remains dominant above the fold (≥40% viewport share).
4. Engineering remains secondary/closed by default.
5. No horizontal overflow.
6. Read-only / live-locked / non-authorizing markers unchanged.
7. No productive Python owner/semantic change; presentation-only diff.
8. Chrome full-page evidence pack attached to implementation PR.

## Tests

- Extend/reuse: `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`
- Extend/reuse: `tests/webui/test_market_dashboard_phase1a_composition_foundation_v1.py`
- Extend/reuse: `tests/webui/test_market_dashboard_responsive_polish_v1.py`
- Extend/reuse: `tests/webui/test_market_dashboard_topn_navigation_visual_density_v1.py`
- Browser policy remains green: `tests/webui/test_market_dashboard_browser_policy_chrome_primary_v1.py`
- Focused CI selector path only unless selector demands broader scope

## Chrome Full-Page Evidence Plan

1. Start via `scripts/ops/start_market_dashboard_visual_operator_readonly_v1.sh` (offline bundles).
2. Capture with `scripts/webui/market_dashboard_chrome_playwright_harness_v1.py` (`channel=chrome`).
3. Required viewports: 1440×900, 1280×800, 1728×1117.
4. Artifacts: full-page + viewport screenshots; geometry JSON with Decision height/share and Observability start Y.
5. `REAL_CHROME_VERIFIED=true` required; Chromium fallback fails closed for acceptance.

## Rollback Plan

Revert the single presentation PR (templates/CSS only). No data/runtime rollback needed. Rebaseline screenshots from this evidence pack remain the before-reference.

## Expected risks

- Over-compaction hiding required Decision status (mitigate: keep blocker/safety summary visible; densify tables/spacing, do not remove authority-false markers).
- Accidental semantic/text changes in ranking/safety copy (mitigate: template class/spacing-only edits; structure contracts).
- Responsive regressions at 1280 (mitigate: three-viewport Chrome evidence mandatory).

## PR boundary

One PR, presentation-only, titled approximately:

`feat(webui): compress decision surface vertical weight for full-page composition`

Must not include Master Runbook rewrite, producer changes, or runtime activation.
