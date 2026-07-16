# Phase 3 Execution Plan — Market Chart (Preparation Only)

```text
GO_TOKEN=GO_VISUAL_OPERATOR_DASHBOARD_DESIGN_GATE_AND_PHASE3_PREP_V1
PHASE=PHASE_3
PHASE_NAME=MARKET_CHART
IMPLEMENTATION_STARTED=false
DESIGN_GATE_DEPENDENCY=PASS
STOP_BEFORE_IMPLEMENTATION=true
PRIMARY_BROWSER=GOOGLE_CHROME
PLAYWRIGHT_CHANNEL=chrome
```

Canonical product SSOT:

- `docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md` (§3.3 Market Chart, PHASE 3)

## Goal (from runbook)

- Real candlesticks, volume, tooltip, source, freshness, selected-instrument binding.
- Exit: `CANDLE_CHART_REAL_DATA=true`, `CHART_SELECTED_INSTRUMENT_SYNC=true`, `NO_EMPTY_CHART_WHEN_DATA_EXISTS=true`.
- Contracts: default visible bars 120; windows 50/120/250/ALL; explicit gaps; stale overlay; timezone visible; no visual interpolation of missing bars.

## Affected files (expected reuse-first)

### Templates / partials

- `templates/peak_trade_dashboard/partials/market_primary_close_chart_v1.html` — primary chart surface
- `templates/peak_trade_dashboard/market_v0.html` — only if chart density/CSS hooks require binding
- Existing Chart.js vendor wiring under `static/vendor/chartjs/` (Phase 1B) — reuse, no CDN

### Python / display adapters

- `src/webui/market_surface.py` — template context wire only; no producer ownership
- Existing futures OHLCV display/runtime owners already used by `/market` (reuse; do not fork)
- Narrow presentation helpers only if tooltip/window labels need formatting (consumer-only)

### CSS / tokens

- `static/css/peak_trade_dashboard_layout_v1.css` — chart density / above-fold constraints
- `static/css/peak_trade_dashboard_design_tokens_v1.css` — token reuse only; no second token owner

### Tests (expected)

- Extend focused webui chart contracts (new or existing under `tests/webui/`)
- Preserve Phase 1A/1B/2 geometry: chart top + material visibility @ 1440×900
- Chrome Playwright harness: `scripts/webui/market_dashboard_chrome_playwright_harness_v1.py`

### Screenshot matrix (Phase 3 evidence)

1. Chart detail 1440×900 (candles + volume)
2. Tooltip / hover state (Chrome)
3. Fresh vs stale overlay
4. Missing/gap rendering state
5. Window switch 50/120/250 if implemented
6. Narrow 1280×800 + wide 1728×1117 regression
7. Hero+chart above-fold regression (Phase 2 must not regress)

## Owners

| Concern | Owner |
|---|---|
| OHLCV data truth | Existing futures OHLCV read-model / runtime (canonical; not dashboard) |
| Chart presentation | `market_primary_close_chart_v1.html` + market_surface context |
| Layout / fold geometry | `peak_trade_dashboard_layout_v1.css` + Phase 1A markers |
| Browser evidence | Chrome Playwright harness (`channel=chrome`) |
| Design tokens | `peak_trade_dashboard_design_tokens_v1.css` |

## Adapter policy

- Dashboard remains consumer-only.
- No second chart truth.
- No synthetic candles.
- No request-time venue network.
- Tooltip/window UI may format existing fields only.

## Reuse plan

1. Keep Chart.js local vendor path from Phase 1B.
2. Keep SSR candle path if it already renders real OHLCV; enhance presentation contracts before introducing new libraries.
3. Reuse Phase 2 above-fold markers and harness assertions as regression gates.
4. Do not rebuild Operator Overview in Phase 3.

## Risks

| Risk | Mitigation |
|---|---|
| Chart enhancements push chart below fold | Hard gate: CHART_MATERIALLY_VISIBLE_1440x900 |
| Tooltip/window JS causes console/network failures | Chrome harness console=0, self-only network |
| Temptation to invent missing bars | Explicit gap policy; no interpolation |
| Scope creep into ranking/decision | Strict Phase 3 file allowlist; STOP_BEFORE_MERGE |

## Browser evidence plan

```text
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_AUTOMATION=PLAYWRIGHT
PRIMARY_PLAYWRIGHT_CHANNEL=chrome
SAFARI_REQUIRED_FOR_NORMAL_SLICE_MERGE=false
```

## Non-goals for Phase 3 prep

- No implementation in this document's commit.
- No Phase 4 ranking work.
- No merge of PR #5247 from this prep step alone beyond evidence commit.

```text
PHASE3_READY=true
IMPLEMENTATION_STARTED=false
```
