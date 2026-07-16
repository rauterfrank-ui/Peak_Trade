# Peak_Trade Visual Operator Dashboard Runbook v1.3
## Canonical Composition + Technical Discovery Edition

> Dieses Dokument kombiniert:
> - die normativen Architektur-, Governance- und UX-Regeln des Composition/Landmark-Runbooks
> - die vollständige technische Discovery als Referenz für Implementierung und Audits.

---

# PART I — Product Runbook (Canonical)

# Peak_Trade Visual Operator Dashboard Runbook v1.3 (Neuaufbau)

## Ziel
Dieses Runbook definiert ausschließlich die Umsetzung des Dashboards als **eine zusammenhängende Full-Page-Komposition**.

## Architekturgrundsätze

- Es existiert genau **eine** visuelle Komposition.
- Landmarks definieren die Informationsarchitektur.
- Kompositionsbereiche sind reine Layout-Helfer.
- Das Dashboard ist ausschließlich Consumer der kanonischen Core-Systeme.
- Es entsteht niemals eine zweite fachliche Wahrheit.

## Verbindliche Reihenfolge der Landmarks

1. Global Header
2. Primary Market Surface
3. Decision Surface
4. Observability Surface
5. Engineering Drawer (standardmäßig geschlossen)

## Composition-first

Vor jeder Änderung:

1. Vollseiten-Screenshot mit Playwright in Google Chrome.
2. Analyse der gesamten Seite.
3. Composition Plan erstellen.
4. Erst danach Implementierung.

Lokale Verbesserungen ohne Verbesserung der Gesamtkomposition sind unzulässig.

## Dashboard-Governance

- Dashboard ist Read-only.
- Keine Trading-, Risk-, Decision- oder Authority-Logik.
- Nur kanonische Core-Outputs darstellen.
- Adapter sind reine Präsentationsschicht.

## Browser

Primär:
- Google Chrome über Playwright

Sekundär:
- Chromium (explizit als Fallback kennzeichnen)
- WebKit/Safari nur als Kompatibilitätsprüfung

## Merge-Blocker

- Unterbrochene Landmark-Reihenfolge
- Konkurrenz mehrerer Primärfokusse
- Große unbegründete Leerflächen
- Horizontales Overflow
- Unklare Blickführung
- Neue fachliche Logik im Dashboard
- Fehlende Full-Page-Evidence

## Definition of Done

Ein Slice ist nur bestanden, wenn:

- die gesamte Seite sichtbar verbessert wurde,
- die Landmark-Reihenfolge erhalten bleibt,
- der Marktchart die dominante Bühne bildet,
- Engineering sekundär bleibt,
- alle Änderungen durch Screenshots belegt sind,
- technische Tests grün sind,
- das Dashboard ausschließlich Consumer bleibt.

## Cursor-Arbeitsvertrag

1. Immer Full-Page denken.
2. Immer Landmark-Reihenfolge erhalten.
3. Immer zuerst analysieren, dann ändern.
4. Reuse-first.
5. Keine zweite Wahrheit.
6. Keine lokalen Optimierungen ohne globalen Gewinn.
7. Vor jedem Merge Full-Page-Review.


---

# PART II — Technical Discovery (Repository Snapshot)

# Runbook V2 Discovery

Discovery-Zeitpunkt: 2026-07-17  
Modus: READ-ONLY  
Scope: Visual Operator / Market Dashboard im aktuellen Repository

---

# 1 Repository

| Feld | Wert |
|---|---|
| Workspace | `/Users/frnkhrz/Peak_Trade` |
| Branch | `main` |
| HEAD | `30de36030892d4a7680c68b812021f6bb38b5831` |
| origin/main | `30de36030892d4a7680c68b812021f6bb38b5831` |
| HEAD vs origin/main | identisch (`0	0` ahead/behind) |
| HEAD-Message | `Merge pull request #5254 from rauterfrank-ui&#47;feat&#47;market-dashboard-phase1a-composition-foundation-v1` |
| Tracking | `main...origin&#47;main` |

## Worktree-Status

- Tracked working tree: clean (keine staged/unstaged tracked changes)
- Untracked: `.runtime&#47;`
  - `.runtime&#47;market-dashboard-composition-first.log`
  - `.runtime&#47;market-dashboard-phase-minus-1-rebaseline.log`
  - `.runtime&#47;market-dashboard-phase-minus-1-rebaseline.pid`
  - `.runtime&#47;market-dashboard-pr5248.log`
  - `.runtime&#47;market-dashboard-pr5249-merged.log`
  - `.runtime&#47;market-dashboard-pr5250-review.log`

---

# 2 Dashboard Render Chain

Framework: FastAPI  
Kanonische Route: `GET &#47;market`  
App-Einstieg: `src.webui.app:app` (`create_app()` → module-level `app`)  
Template-Root: `templates/peak_trade_dashboard` (`Jinja2Templates`)  
Static mount: `/static` → `static/`  
Middleware: keine anwendungsweite FastAPI-Middleware für `/market`  
Inventory-Anker: `docs/product/evidence/phase_minus_1_rebaseline_v1_20260716T210645Z/dashboard_component_inventory.json`

## Request → Response

```
Client GET /market[?symbol&timeframe&limit&source&top_n&matrix_*]
  → uvicorn src.webui.app:app
  → app.include_router(create_market_router(templates, get_project_status))
       Owner: src/webui/app.py
  → create_market_router → handler market_v0_page
       Owner: src/webui/market_surface.py
  → resolve_market_page_data(...)
       → (symbol, source, payload, data_unavailable)
  → build_market_v0_page_template_context(...)
       → aggregierte Surface-ViewModels
  → Jinja2Templates.TemplateResponse(request, "market_v0.html", context)
  → HTMLResponse (SSR; Primary-Chart = SSR-SVG)
```

## Legacy Redirects (nicht kanonischer Render)

| Route | Handler-Datei | Ziel |
|---|---|---|
| `GET &#47;market&#47;double-play` | `src/webui/app.py` | `302` → `/market?...#double-play` |
| `GET &#47;market&#47;futures` | `src/webui/app.py` | `302` → `/market...#futures` |

## Neben-Endpunkte (nicht SSR-Hauptpfad)

| Route | Owner-Datei | Funktion |
|---|---|---|
| `GET &#47;api&#47;market&#47;ohlcv` | `src/webui/market_surface.py` | `api_market_ohlcv` (Legacy JSON; `source=futures` → HTTP 422) |
| `GET &#47;api&#47;market&#47;depth` | `src/webui/market_depth_api_v0.py` | Depth JSON |
| `GET &#47;api&#47;master-v2&#47;double-play&#47;dashboard-display.json` | `src/webui/double_play_dashboard_display_json_route_v0.py` | Double-Play Display JSON |

## Kanonische Owner-Konstanten (`src/webui/market_surface.py`)

| Konstante | Wert |
|---|---|
| `CANONICAL_MARKET_ROUTE` | `/market` |
| `CANONICAL_MARKET_ROUTE_OWNER` | `src/webui/market_surface.py` |
| `CANONICAL_MARKET_VIEWMODEL_OWNER` | `src/webui/market_surface.py` |
| `CANONICAL_MARKET_TEMPLATE_OWNER` | `templates/peak_trade_dashboard/market_v0.html` |
| `CANONICAL_CHART_OWNER` | `templates/peak_trade_dashboard/partials/market_primary_close_chart_v1.html` |
| `CANONICAL_RANKING_FUNNEL_OWNER` | `src/webui/market_ranking_funnel_runtime_v0.py` |
| `CANONICAL_FUTURES_OHLCV_OWNER` | `src/webui/market_futures_ohlcv_runtime_v0.py` |
| `CANONICAL_F5_METADATA_OWNER` | `src/webui/futures_read_only_market_dashboard_runtime_v0.py` |
| `CANONICAL_DP_DATA_OWNER` | `src/webui/double_play_dashboard_display_json_route_v0.py` |
| `CANONICAL_SAFETY_DATA_OWNER` | `src/webui/futures_read_only_market_dashboard_runtime_v0.py` |
| `CANONICAL_CURRENT_STATE_SNAPSHOT_OWNER` | `src/webui/market_dashboard_current_state_snapshot_v0.py` |
| `CANONICAL_CURRENT_STATE_RUNTIME_OWNER` | `src/webui/market_dashboard_current_state_runtime_v0.py` |
| `CANONICAL_ELIGIBILITY_OWNER` | `src/webui/market_instrument_eligibility_v0.py` |

## Python-Funktionen der SSR-Kette

### Router / Resolve / Page Context

| Funktion | Datei |
|---|---|
| `create_app` | `src/webui/app.py` |
| `create_market_router` | `src/webui/market_surface.py` |
| `market_v0_page` | `src/webui/market_surface.py` |
| `resolve_market_page_data` | `src/webui/market_surface.py` |
| `build_market_v0_page_template_context` | `src/webui/market_surface.py` |
| `build_market_view_query_extras` | `src/webui/market_surface.py` |
| `normalize_top_n` (via Top-N Helpers) | `src/webui/market_surface.py` |

### Context Builder in `build_market_v0_page_template_context`

| Funktion | Datei |
|---|---|
| `build_market_primary_values_display_context` | `src/webui/market_surface.py` |
| `build_market_depth_display_context` | `src/webui/market_surface.py` |
| `build_market_run_projection_display_context` | `src/webui/market_surface.py` |
| `build_market_tape_display_context` | `src/webui/market_surface.py` |
| `build_market_ranking_funnel_display_context` | `src/webui/market_surface.py` → Ranking Runtime |
| `build_market_operator_overview_display_context` | `src/webui/market_surface.py` |
| `build_market_ranking_watchlist_display_context` | `src/webui/market_surface.py` |
| `build_market_instrument_header_display_context` | `src/webui/market_surface.py` |
| `build_market_futures_metrics_strip_display_context` | `src/webui/market_surface.py` |
| `build_market_active_paper_run_display_context` | `src/webui/market_surface.py` → Active Paper Runtime |
| `build_market_single_page_consolidation_display_context` | `src/webui/market_surface.py` |
| `build_workflow_dashboard_display_context` | `src/webui/workflow_dashboard_runtime_v1.py` (gate) |
| `build_last_paper_run_panel_display_context` | `src/webui/last_paper_run_panel_runtime_v0.py` (gate) |
| `build_static_dashboard_display_dict` | `src/webui/double_play_dashboard_display_json_route_v0.py` |
| `build_futures_read_only_market_dashboard_display_context` | `src/webui/futures_read_only_market_dashboard_runtime_v0.py` |
| `build_market_futures_ohlcv_display_context` | `src/webui/market_futures_ohlcv_runtime_v0.py` |
| `build_market_governed_top20_display_context` | `src/webui/market_surface.py` |
| `build_market_selected_instrument_workspace_display_context` | `src/webui/market_surface.py` |
| `build_market_double_play_matrix_display_context` | `src/webui/market_surface.py` |
| `build_market_safety_matrix_display_context` | `src/webui/market_surface.py` |
| `build_market_dashboard_current_state_display_context` | `src/webui/market_dashboard_current_state_runtime_v0.py` |
| `build_market_visual_operator_surface_context` | `src/webui/market_visual_operator_surface_v1/runtime_v1.py` |
| `build_operator_overview_display_v1` | `src/webui/market_visual_operator_surface_v1/operator_overview_display_v1.py` |

### Visual-Operator Display Module

| Funktion / Modul | Datei |
|---|---|
| `build_operator_header_display_v1` | `src/webui/market_visual_operator_surface_v1/operator_header_display_v1.py` |
| `build_decision_funnel_display_v1` | `src/webui/market_visual_operator_surface_v1/decision_funnel_display_v1.py` |
| `build_economic_observability_display_v1` | `src/webui/market_visual_operator_surface_v1/economic_observability_display_v1.py` |
| `build_ai_linear_diagnostics_display_v1` | `src/webui/market_visual_operator_surface_v1/ai_linear_diagnostics_display_v1.py` |
| Contracts / Env | `src/webui/market_visual_operator_surface_v1/contracts.py` |

### Templates der SSR-Antwort

| Rolle | Pfad |
|---|---|
| Base | `templates/peak_trade_dashboard/base.html` |
| Page | `templates/peak_trade_dashboard/market_v0.html` |
| Partials | siehe Kapitel 4 |

### Readonly-Start

| Script | Pfad |
|---|---|
| Visual Operator Readonly Start | `scripts/ops/start_market_dashboard_visual_operator_readonly_v1.sh` |

---

# 3 Owner Matrix

CSS-Trio für alle Surfaces:  
`static/css/peak_trade_dashboard_design_tokens_v1.css` +  
`static/css/peak_trade_dashboard_layout_v1.css` +  
`static/css/peak_trade_dashboard_utilities_v1.css`  
(eingebunden in `base.html`)

| Surface / Component | Landmark / ID | Owner (Python) | Context Builder | Template | CSS | JS | Datenquelle |
|---|---|---|---|---|---|---|---|
| GLOBAL_HEADER | `GLOBAL_HEADER` / C-HEADER | `market_surface` + `market_visual_operator_surface_v1` | `build_market_visual_operator_surface_context` → `build_operator_header_display_v1`; Page-Shell in `market_v0.html` | `market_v0.html` Header + `partials&#47;market_visual_operator_header_v1.html` | CSS-Trio | — | Futures-OHLCV Freshness + Economic/AI Activity States |
| PRIMARY Hero / Workspace | `PRIMARY_MARKET_SURFACE` / C-HERO | `src/webui/market_surface.py` (`CANONICAL_WORKSPACE_TEMPLATE_OWNER`) | `build_market_selected_instrument_workspace_display_context`, `build_market_primary_values_display_context`, `build_operator_overview_display_v1` | `partials&#47;market_primary_operator_hero_v1.html` | CSS-Trio | — | `resolve_market_page_data` → Futures-OHLCV Bundle oder Legacy Loader |
| PRIMARY Chart | C-CHART | Chart-Template Owner | payload / primary_values / workspace | `partials&#47;market_primary_close_chart_v1.html` | CSS-Trio (`--pt-primary-chart-min-height`) | SSR SVG (kein Chart.js im Primary) | `payload.bars` / Futures OHLCV |
| DECISION Ranking / Top20 | `DECISION_SURFACE` / C-RANKING | `src/webui/market_ranking_funnel_runtime_v0.py` + `market_surface` | `build_market_ranking_funnel_display_context` → `build_market_governed_top20_display_context` | `partials&#47;market_governed_top20_primary_v1.html` | CSS-Trio | Query-Hrefs (SSR Links) | `PEAK_TRADE_MARKET_RANKING_FUNNEL_*` + `ranking_funnel.json` |
| DECISION Funnel | C-FUNNEL | `market_visual_operator_surface_v1` | `build_decision_funnel_display_v1` | `partials&#47;market_decision_funnel_visual_v1.html` | CSS-Trio | — | `PEAK_TRADE_MARKET_VISUAL_OPERATOR_EVIDENCE_ROOT` |
| DECISION F5 Compact | DECISION secondary | `src/webui/futures_read_only_market_dashboard_runtime_v0.py` | `build_futures_read_only_market_dashboard_display_context` | `partials&#47;futures_market_compact_v1.html` (+ Detail `futures_read_only_market_panel_v0.html`) | CSS-Trio | — | `PEAK_TRADE_F5_MARKET_DASHBOARD_*` → `dashboard.json` |
| DECISION Double Play | DECISION secondary | `src/webui/double_play_dashboard_display_json_route_v0.py` + `market_surface` | `build_static_dashboard_display_dict` → `build_market_double_play_matrix_display_context` | `partials&#47;double_play_market_compact_v1.html` (+ `double_play_market_panel_v0.html`) | CSS-Trio | optional JSON-URL im Context | In-process static Double-Play Snapshot |
| DECISION Safety / Risk | C-SAFETY | `market_surface` + F5 Runtime | `build_market_safety_matrix_display_context` | `partials&#47;market_safety_compact_v1.html` | CSS-Trio | — | DP Display + F5 Sections; Authority-Flags false |
| DECISION Watchlist | Include in `DECISION_SURFACE` (Inventory: C-WATCH / OBSERVABILITY) | `market_surface` | `build_market_ranking_watchlist_display_context` | `partials&#47;market_watchlist_compact_v1.html` | CSS-Trio | — | Ranking-Funnel Rows |
| OBSERVABILITY Economic | C-ECON | `market_visual_operator_surface_v1` | `build_economic_observability_display_v1` | `partials&#47;market_economic_observability_visual_v1.html` | CSS-Trio | — | Evidence Root |
| OBSERVABILITY AI Linear | C-AI | `market_visual_operator_surface_v1` | `build_ai_linear_diagnostics_display_v1` | `partials&#47;market_ai_linear_diagnostics_visual_v1.html` | CSS-Trio | — | `PEAK_TRADE_MARKET_LINEAR_DIAGNOSTICS_BUNDLE_ROOT` |
| ENGINEERING Current State | ENGINEERING_DRAWER | Snapshot + Runtime | `market_dashboard_current_state_snapshot_v0` → `build_market_dashboard_current_state_display_context` | `partials&#47;market_current_state_compact_v1.html` | CSS-Trio | — | In-code Snapshot SSOT (always-on) |
| ENGINEERING Diagnostics | C-ENG | Runtime + Legacy Panels | depth/tape/run/active-paper/current_state Contexts | `partials&#47;market_diagnostics_drawer_v1.html` → `market_legacy_operator_panels_v0.html` | CSS-Trio | Chart.js vendor (Legacy) | Env-gated Depth/Tape/Paper/Run Projection Bundles |
| Operator Overview Phase 2 | Hero/Header Composition | `operator_overview_display_v1.py` | `build_operator_overview_display_v1` | konsumiert in Hero/Header (kein eigenes Top-Level-Include) | Layout Hero Grid | — | Composed aus Primary/Workspace/Funnel/Safety/AI |
| Secondary Grid | MIXED / C-SECONDARY-GRID | `market_v0.html` Layout | F5 + DP + Safety + Watchlist Contexts | Secondary Grid in `market_v0.html` | Layout CSS | — | F5 + DP + Safety + Watchlist |

---

# 4 Template-Struktur

## Seiten-Templates (Market-relevant)

| Datei | Rolle |
|---|---|
| `templates/peak_trade_dashboard/base.html` | Base; CSS-Links; Default App-Chrome |
| `templates/peak_trade_dashboard/market_v0.html` | Kanonische Market Page (`{% extends "base.html" %}`) |
| `templates/peak_trade_dashboard/double_play_market_dashboard_v0.html` | Legacy Standalone Double-Play |
| `templates/peak_trade_dashboard/futures_read_only_market_dashboard_v0.html` | Legacy Standalone F5 |

## Market Partials (vollständig)

| Datei |
|---|
| `templates/peak_trade_dashboard/partials/market_visual_operator_header_v1.html` |
| `templates/peak_trade_dashboard/partials/market_primary_operator_hero_v1.html` |
| `templates/peak_trade_dashboard/partials/market_primary_close_chart_v1.html` |
| `templates/peak_trade_dashboard/partials/market_governed_top20_primary_v1.html` |
| `templates/peak_trade_dashboard/partials/market_decision_funnel_visual_v1.html` |
| `templates/peak_trade_dashboard/partials/futures_market_compact_v1.html` |
| `templates/peak_trade_dashboard/partials/double_play_market_compact_v1.html` |
| `templates/peak_trade_dashboard/partials/market_safety_compact_v1.html` |
| `templates/peak_trade_dashboard/partials/market_watchlist_compact_v1.html` |
| `templates/peak_trade_dashboard/partials/market_economic_observability_visual_v1.html` |
| `templates/peak_trade_dashboard/partials/market_ai_linear_diagnostics_visual_v1.html` |
| `templates/peak_trade_dashboard/partials/double_play_market_panel_v0.html` |
| `templates/peak_trade_dashboard/partials/futures_read_only_market_panel_v0.html` |
| `templates/peak_trade_dashboard/partials/market_current_state_compact_v1.html` |
| `templates/peak_trade_dashboard/partials/market_diagnostics_drawer_v1.html` |
| `templates/peak_trade_dashboard/partials/market_legacy_operator_panels_v0.html` |
| `templates/peak_trade_dashboard/partials/workflow_dashboard_v1_panels.html` |
| `templates/peak_trade_dashboard/partials/last_paper_run_panel_v0.html` |

## Include-Hierarchie (kanonischer SSR-Pfad)

```
base.html
└── market_v0.html
    ├── [data-landmark=GLOBAL_HEADER]
    │   ├── inline header (market_v0.html)
    │   └── partials/market_visual_operator_header_v1.html
    ├── [data-landmark=PRIMARY_MARKET_SURFACE]
    │   └── partials/market_primary_operator_hero_v1.html
    │       └── partials/market_primary_close_chart_v1.html
    ├── [data-landmark=DECISION_SURFACE]
    │   ├── partials/market_governed_top20_primary_v1.html   (if futures_first)
    │   ├── partials/market_decision_funnel_visual_v1.html
    │   ├── partials/futures_market_compact_v1.html
    │   ├── partials/double_play_market_compact_v1.html
    │   ├── partials/market_safety_compact_v1.html
    │   └── partials/market_watchlist_compact_v1.html
    ├── [data-landmark=OBSERVABILITY_SURFACE]
    │   ├── partials/market_economic_observability_visual_v1.html
    │   └── partials/market_ai_linear_diagnostics_visual_v1.html
    └── [data-landmark=ENGINEERING_DRAWER]
        ├── partials/double_play_market_panel_v0.html
        ├── partials/futures_read_only_market_panel_v0.html
        ├── partials/market_current_state_compact_v1.html   (if current_state.section_visible)
        └── partials/market_diagnostics_drawer_v1.html
            └── partials/market_legacy_operator_panels_v0.html
                ├── partials/workflow_dashboard_v1_panels.html
                ├── partials/last_paper_run_panel_v0.html
                └── Chart.js: /static/vendor/chartjs/4.4.1/chart.umd.min.js
```

## Weitere Dashboard-Templates im selben Tree (nicht Market-SSR-Hauptpfad)

`index.html`, `alerts.html`, `error.html`, `execution_watch.html`, `execution_timeline.html`, `observability_hub.html`, `ops_stage1.html`, `ops_workflows.html`, `ops_ci_health.html`, `session_detail.html`, `telemetry_console.html`, `trigger_training_psychology.html`, `psychology_heatmap_macro.html`, `r_and_d_*.html`

---

# 5 CSS / Styling

## Zentrale CSS-Dateien

| Datei | Rolle | Owner-Marker |
|---|---|---|
| `static/css/peak_trade_dashboard_design_tokens_v1.css` | Design Tokens (`:root`) | Header: `CANONICAL_OWNER: static&#47;css&#47;peak_trade_dashboard_design_tokens_v1.css` |
| `static/css/peak_trade_dashboard_layout_v1.css` | Layout / Grid / Composition | konsumiert nur Tokens |
| `static/css/peak_trade_dashboard_utilities_v1.css` | Purged Utilities (self-hosted; kein Tailwind CDN) | Template-Marker `data-market-utilities-css-v1` |

## Einbindung (`base.html` `<head>`)

1. `/static/css/peak_trade_dashboard_design_tokens_v1.css` (`data-market-design-token-owner-v1`, `data-canonical-design-token-owner`)
2. `/static/css/peak_trade_dashboard_layout_v1.css`
3. `/static/css/peak_trade_dashboard_utilities_v1.css`

Meta: `peak-trade-browser-network-allowlist` = `self-only`  
Inline: nur `.pulse-dot` Animation

## Design Tokens (`:root`)

| Gruppe | Tokens |
|---|---|
| Layout | `--pt-content-max-width: 1600px`, `--pt-page-padding: 16px`, `--pt-grid-gap: 12px`, `--pt-card-padding: 12px`, `--pt-card-radius: 10px`, `--pt-card-border`, `--pt-header-height: 64px`, `--pt-safety-rail-max-height: 32px`, `--pt-hero-min-height: 210px`, `--pt-hero-max-height: 290px`, `--pt-primary-chart-min-height: 390px`, `--pt-primary-chart-visual-share-min: 0.4`, `--pt-table-row-height: 44px` |
| Spacing Scale | `--pt-space-1`…`--pt-space-7` (4px…48px) |
| Icons | `--pt-icon-sm&#47;md&#47;lg` |
| Breakpoints | `--pt-bp-narrow: 1280px`, `--pt-bp-reference: 1440px`, `--pt-bp-wide: 1728px` |
| Typography | `--pt-font-family`, `--pt-mono-font`, `--pt-font-size-xs`…`xl`, `--pt-line-height: 1.4` |
| Colors | `--pt-color-background`, `surface-1&#47;2`, `border`, `text-primary&#47;secondary`, `positive`, `negative`, `warning`, `info`, `model`, `muted` |

## Layout-System / Grid / Spacing

Datei: `static/css/peak_trade_dashboard_layout_v1.css`

| Selektor / Klasse | Funktion |
|---|---|
| `.pt-dashboard-shell` | max-width + page padding |
| `.pt-dashboard-app-header` | Header-Höhe via Token |
| `.pt-dashboard-grid` | Grid |
| `.pt-dashboard-card` | Card |
| `.pt-dashboard-tabular` | Tabular |
| `#market-v0-shell` Composition | Header, Safety Rail, Hero, Chart Height Clamps |
| `.pt-operator-overview-hero-grid` | Phase-2 Hero Grid |
| `@media (max-width: 1279px)` | Shell-Padding via `--pt-space-3` |
| Chart frame clamp | `min-height: var(--pt-primary-chart-min-height)` + `clamp(..., 42vh, 520px)` |

Utilities: Tailwind-ähnliche Klassen in Templates (`grid-cols-*`, Spacing, Farben).

---

# 6 Browser

## Playwright

| Fakt | Wert |
|---|---|
| Node `playwright.config.*` | nicht vorhanden |
| Integration | Python `playwright.sync_api` |
| Primär-Harness | `scripts/webui/market_dashboard_chrome_playwright_harness_v1.py` |
| Review-Server Helper | `scripts/webui/review_server_playwright_webserver_v1.py` |
| Review-Server Shell | `scripts/webui/review_server.sh` |
| Landmark Capture | `scripts/webui/market_dashboard_landmark_discovery_capture_v1.py` |
| Phase-1A Capture | `scripts/webui/market_dashboard_phase1a_composition_capture_v1.py` |
| Docs | `docs/webui/REVIEW_SERVER_HARNESS_V1.md` |
| Policy-Test | `tests/webui/test_market_dashboard_browser_policy_chrome_primary_v1.py` |
| Review-Server-Test | `tests/webui/test_review_server_harness_v1.py` |

## Chrome / Chromium / WebKit

| Browser | Status im Repo |
|---|---|
| Google Chrome | Primär: `PRIMARY_PLAYWRIGHT_CHANNEL=chrome`; Launch `playwright.chromium.launch(channel="chrome")` |
| Playwright Chromium | Fallback wenn `channel=chrome` fehlschlägt; muss berichtet werden (`BROWSER_ACTUAL=PLAYWRIGHT_CHROMIUM`); nicht als real Chrome claimen |
| WebKit | Sekundär laut Product Runbook v1.3; nicht als real Safari claimen |
| Safari | Optionaler sekundärer Kompatibilitätscheck; kein Merge-Blocker für normale Dashboard-Slices |

Harness-Report-Felder u. a.: `BROWSER_REQUESTED`, `PLAYWRIGHT_CHANNEL`, `BROWSER_ACTUAL`, `CHROMIUM_FALLBACK_USED`, `REAL_CHROME_VERIFIED`, Geometry/Composition, `screenshots`.

Default Viewport Harness: `1440x900`  
Default Path: `/market?timeframe=1h`

## Screenshot-Harness

- Schreibt unter Caller-`out_dir&#47;screenshots&#47;`
- Pfade in `BrowserReport.screenshots`
- Durable Evidence-Packs:
  - `docs/product/evidence/phase_minus_1_rebaseline_v1_20260716T210645Z/`
  - `docs/product/evidence/phase_1a_20260716T180101Z/`
  - `docs/product/evidence/phase_1b_20260716T181219Z/`
  - `docs/product/evidence/phase_2_20260716T184639Z/`
  - `docs/product/evidence/visual_foundation_rework_v1_20260716T214800Z/`
  - `docs&#47;product&#47;evidence&#47;visual_composition_first_refactor_v1_20260716T221000Z&#47;`

## Visual Regression

- Kein `playwright.config` pixel-diff / `toHaveScreenshot`-Framework unter `tests/`
- Praktische Regression: SSR-DOM-Marker-Contracts (pytest) + Chrome-Screenshot-Evidence + Composition-Geometry im Harness
- Product Runbook / Implementation Plan referenzieren Visual Regression als Ziel

---

# 7 Datenquellen

## Materialisierung / Manifeste

| Artefakt | Pfad / Inhalt |
|---|---|
| Materializer | `scripts/ops/materialize_market_dashboard_visual_operator_offline_bundles_v1.py` |
| Emitiert u. a. | `futures_ohlcv&#47;`, `ranking_funnel&#47;`, `f5_dashboard&#47;`, `SOURCE_PROVENANCE.json`, `economic_evidence_binding.json`, `MANIFEST.sha256` |
| Local Env Example | `docs/webui/market_visual_operator_surface_v1.local.example.env` |
| Readonly Start | `scripts/ops/start_market_dashboard_visual_operator_readonly_v1.sh` |

## Env-Gates → Bundles → Builder

| Surface-Daten | Enabled Env | Bundle/Root Env | Runtime / Builder |
|---|---|---|---|
| Ranking Funnel | `PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED` | `PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT` | `market_ranking_funnel_runtime_v0.py` → `market_ranking_funnel_readmodel_v0&#47;builder.py` (`ranking_funnel.json`) |
| Futures OHLCV | `PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED` | `PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT` | `market_futures_ohlcv_runtime_v0.py` → `market_futures_ohlcv_readmodel_v0&#47;builder.py` (`futures_ohlcv.json`) |
| F5 Dashboard | `PEAK_TRADE_F5_MARKET_DASHBOARD_ENABLED` | `PEAK_TRADE_F5_MARKET_DASHBOARD_BUNDLE_ROOT` | `futures_read_only_market_dashboard_runtime_v0.py` (`dashboard.json`) |
| Depth | `PEAK_TRADE_MARKET_DEPTH_ENABLED` | `PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT` | `market_depth_runtime_v0.py` → `market_depth_readmodel_v0&#47;builder.py` (`depth.json`) |
| Tape | `PEAK_TRADE_MARKET_TAPE_ENABLED` | `PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT` | `market_tape_readmodel_v0&#47;gate.py` + `builder.py` (`tape.json`) |
| Visual Evidence | — | `PEAK_TRADE_MARKET_VISUAL_OPERATOR_EVIDENCE_ROOT` | Funnel/Economic Loader via `contracts.py` / display modules |
| AI Linear | — | `PEAK_TRADE_MARKET_LINEAR_DIAGNOSTICS_BUNDLE_ROOT` | `ai_linear_diagnostics_display_v1.py` |
| Active Paper | `PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_ENABLED` | `PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_BRIDGE_ROOT` | `market_active_paper_run_runtime_v0.py` |
| Run Projection | `PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED` | `PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON` | `build_market_run_projection_display_context` |
| Consolidation | `PEAK_TRADE_MARKET_SINGLE_PAGE_CONSOLIDATION_V1_ENABLED` | Workflow/Archive + Last-Paper Envs | `workflow_dashboard_runtime_v1.py`, `last_paper_run_panel_runtime_v0.py` |
| Workflow Dashboard | `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED` | `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT` | `workflow_dashboard_readmodel_v1&#47;*` |
| Double Play | static | — | `_build_static_double_play_dashboard_display_snapshot_v0` / `build_static_dashboard_display_dict` |
| Current State | always-on | — | `market_dashboard_current_state_snapshot_v0.py` |

## Producers / Adapters (Workflow Dashboard Readmodel)

| Datei |
|---|
| `src/webui/workflow_dashboard_readmodel_v1/universe_selection_producer_v1.py` |
| `src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_fixture_source_v1.py` |
| `src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_real_metadata_source_v1.py` |
| `src/webui/workflow_dashboard_readmodel_v1/futures_universe_upstream_adapter_v1.py` |
| `src/webui/workflow_dashboard_readmodel_v1/universe_selection_contract_v1.py` |
| `src/webui/workflow_dashboard_readmodel_v1/universe_selection_reader_v1.py` |
| `src/webui/workflow_dashboard_readmodel_v1/kraken_metadata_coverage_reader_v1.py` |
| `src/webui/workflow_dashboard_readmodel_v1/builder.py` |
| `src/webui/workflow_dashboard_readmodel_v1/pipeline_builder.py` |

## Snapshot / Context Builder

| Rolle | Datei |
|---|---|
| Snapshot SSOT | `src/webui/market_dashboard_current_state_snapshot_v0.py` |
| Snapshot Display Context | `src/webui/market_dashboard_current_state_runtime_v0.py` |
| Page Context Orchestrator | `src/webui/market_surface.py` (`build_market_v0_page_template_context`) |
| Visual Operator Aggregate | `src/webui/market_visual_operator_surface_v1/runtime_v1.py` |
| Eligibility | `src/webui/market_instrument_eligibility_v0.py` |

## Test-Fixtures (Offline Bundles)

| Pfad |
|---|
| `tests/fixtures/futures_read_only_market_dashboard_v0/` |
| `tests/fixtures/market_depth_readmodel_v0/` |
| `tests/fixtures/market_tape_readmodel_v0/` |
| `tests/fixtures/market_ranking_funnel_readmodel_v0/` |
| `tests/fixtures/market_futures_ohlcv_readmodel_v0/` |
| `tests/fixtures/workflow_dashboard_readmodel_v1/` |

---

# 8 Dashboard-Grenzen

## Read-only Contracts

| Pfad | Inhalt |
|---|---|
| `docs/ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md` | F5 Display Boundary; F1–F4 Prerequisites; keine Execution/Live |
| `docs/webui/MARKET_SURFACE_V0.md` | SSR Display-only; Marker-Familien; Authority=false |
| `src/webui/market_visual_operator_surface_v1/contracts.py` | Activity States; Evidence Root; fail-closed JSON |
| `src/webui/workflow_dashboard_readmodel_v1/universe_selection_contract_v1.py` | Universe Selection Contract |
| `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py` | Strukturelle Marker / No-Authority Testowner |
| `tests/ops/test_futures_read_only_market_dashboard_contract_static_v0.py` | Static F5 Contract |
| `tests/ops/test_market_dashboard_readonly_run_projection_spec_v0.py` | Run-Projection Spec |
| `tests/ops/test_market_surface_ranking_funnel_env_schema_boundary_v0.py` | Env/Schema Boundary |

## Authority

- F5 Runtime: `_authority_boundaries()` — Authority-Flags alle false
- Template-Marker u. a.: `data-market-trading-authority-v1="false"`, `data-market-non-authorizing="true"`, `data-market-readonly="true"`, `data-market-live-locked-v1="true"`
- Header: `runtime_authority`, `orders_allowed`, `live_allowed` aus Visual-Operator Header VM

## Risk / Safety

| Element | Owner |
|---|---|
| Safety Matrix Context | `build_market_safety_matrix_display_context` in `market_surface.py` |
| Safety Template | `partials&#47;market_safety_compact_v1.html` |
| Safety Data Owner Konstante | `CANONICAL_SAFETY_DATA_OWNER` = F5 Runtime |
| Inventory | `risk_safety_owner` in `dashboard_component_inventory.json` |

## Economic

| Element | Owner |
|---|---|
| Display | `economic_observability_display_v1.py` |
| Template | `partials&#47;market_economic_observability_visual_v1.html` |
| Inventory | `economic_owner` |

## Decision

| Element | Owner |
|---|---|
| Funnel Display | `decision_funnel_display_v1.py` |
| Operator Overview | `operator_overview_display_v1.py` |
| Ranking | `market_ranking_funnel_runtime_v0.py` |
| Templates | `market_decision_funnel_visual_v1.html`, `market_governed_top20_primary_v1.html` |
| Inventory | `decision_surface_owner` |

## SSOT

| Pfad | Rolle |
|---|---|
| `docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md` | Product SSOT (Dashboard consumer-only) |
| `docs/webui/MARKET_SURFACE_V0.md` | Technical Market Surface Contract |
| `docs/product/evidence/phase_minus_1_rebaseline_v1_20260716T210645Z/dashboard_ssot_consumer_audit.json` | Consumer Audit (`dashboard_is_consumer_only: true`, `canonical_ssot: MASTER_V2_AND_DOUBLE_PLAY`) |
| `docs/product/matrices/dashboard_requirement_traceability_matrix.json` | Requirement Trace inkl. `R-SSOT-01` |
| `docs/webui/observability/REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md` | Futures Market-Data Source Chain |
| `src/webui/market_dashboard_current_state_snapshot_v0.py` | Current-State Display Snapshot Owner |
| `docs/ops/specs/MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md` | Observer Surface Inventory |
| `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md` | Double-Play Display Map |
| `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_RUNTIME_PRODUCER_DASHBOARD_PREREQUISITE_PARKING_MAP_V0.md` | Producer Prerequisite Parking Map |

Grenzaussage aus Audit/Product Docs: Business-SSOT bleibt Master V2 / Double Play; Dashboard ist Consumer/Display-only.

---

# 9 Test-Infrastruktur

## CI Focused Set

Selector: `scripts/ops/ci_test_selection_v1.py`  
Mode-Name: `market_dashboard_focused`  
Konstante: `CANONICAL_MARKET_DASHBOARD_FOCUSED_TESTS`

| Test |
|---|
| `tests/webui/test_market_dashboard_no_bitcoin_futures_v1.py` |
| `tests/webui/test_market_futures_only_canonical_completion_v1.py` |
| `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py` |
| `tests/webui/test_market_governed_top20_f5_default_wiring_v1.py` |
| `tests/webui/test_market_futures_universe_visual_matrix_v1.py` |
| `tests/webui/test_market_dashboard_selected_instrument_workspace_v1.py` |
| `tests/webui/test_market_dashboard_topn_navigation_visual_density_v1.py` |
| `tests/webui/test_market_futures_first_root_cause_eradication_v1.py` |
| `tests/webui/test_futures_read_only_market_dashboard_v0.py` |
| `tests/webui/test_market_canonical_short_url_title_real_values_ui_v1.py` |
| `tests/webui/test_market_ranking_funnel_readmodel_v0.py` |
| `tests/test_market_surface_api.py` |
| `tests/ci/test_ci_diff_aware_test_selection_v1.py` |

## Playwright / Browser Policy

| Test | Scope |
|---|---|
| `tests/webui/test_market_dashboard_browser_policy_chrome_primary_v1.py` | Chrome primary; Harness `channel=chrome` |
| `tests/webui/test_review_server_harness_v1.py` | Review Server + Playwright Channel Constants |

## DOM / Visual / Composition / Design System (pytest SSR)

| Test | Scope |
|---|---|
| `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py` | Read-only Structure Markers |
| `tests/webui/test_market_dashboard_phase_1a_layout_header_v1.py` | Safety Rail / Chart DOM Order |
| `tests/webui/test_market_dashboard_phase_1b_design_system_assets_v1.py` | Design-Token Owner / Self-only Assets |
| `tests/webui/test_market_dashboard_phase1a_composition_foundation_v1.py` | Composition Foundation |
| `tests/webui/test_market_dashboard_phase_2_operator_overview_v1.py` | Operator Overview Hero |
| `tests/webui/test_market_dashboard_visual_foundation_rework_v1.py` | Foundation Composition Markers |
| `tests/webui/test_market_dashboard_visual_system_transparency_v1.py` | Visual Encodings / Status Rails |
| `tests/webui/test_market_dashboard_responsive_polish_v1.py` | Overflow / a11y / SSR ohne JS |
| `tests/webui/test_market_dashboard_topn_navigation_visual_density_v1.py` | Top-N Nav + Density |
| `tests/webui/test_market_terminal_layout_v1.py` | Terminal Layout |
| `tests/webui/test_market_visual_operator_surface_v1.py` | Visual Operator Surface VMs |
| `tests/webui/test_market_dashboard_matrix_url_state_v1.py` | Matrix URL State |
| `tests/webui/test_market_dashboard_double_play_safety_matrix_v1.py` | DP + Safety Matrices |
| `tests/webui/test_market_dashboard_selected_instrument_workspace_v1.py` | Selected Instrument Workspace |
| `tests/webui/test_market_dashboard_current_state_sync_v0.py` | Current-State Snapshot Freshness |
| `tests/webui/test_market_dashboard_no_bitcoin_futures_v1.py` | Bitcoin Exclusion |

## Data / Runtime / Domain Contracts

| Test |
|---|
| `tests/webui/test_futures_read_only_market_dashboard_v0.py` |
| `tests/webui/test_futures_read_only_market_dashboard_runtime_v0.py` |
| `tests/webui/test_market_futures_ohlcv_runtime_v0.py` |
| `tests/webui/test_market_futures_ohlcv_readmodel_v0.py` |
| `tests/webui/test_market_ranking_funnel_runtime_v0.py` |
| `tests/webui/test_market_ranking_funnel_readmodel_v0.py` |
| `tests/webui/test_market_depth_api_v0.py` |
| `tests/webui/test_market_depth_runtime_v0.py` |
| `tests/webui/test_market_depth_readmodel_v0.py` |
| `tests/webui/test_market_depth_chart_ssr_v0.py` |
| `tests/webui/test_market_tape_ssr_v0.py` |
| `tests/webui/test_market_tape_readmodel_v0.py` |
| `tests/webui/test_market_active_paper_run_runtime_v0.py` |
| `tests/webui/test_market_registry_projection_overlay_v0.py` |
| `tests/webui/test_market_instrument_eligibility_v0.py` |
| `tests/webui/test_market_governed_top20_f5_default_wiring_v1.py` |
| `tests/webui/test_market_futures_universe_visual_matrix_v1.py` |
| `tests/webui/test_market_futures_only_canonical_completion_v1.py` |
| `tests/webui/test_market_futures_first_root_cause_eradication_v1.py` |
| `tests/webui/test_market_single_page_consolidation_runtime_v1.py` |
| `tests/webui/test_market_single_page_unified_consolidation_ui_v1.py` |
| `tests/webui/test_market_single_page_consolidation_structure_contract_v1.py` |
| `tests/webui/test_double_play_market_dashboard_v0.py` |
| `tests/webui/test_double_play_dashboard_display_json_route.py` |
| `tests/webui/test_workflow_dashboard_readmodel_v1.py` |
| `tests/webui/test_workflow_dashboard_runtime_v1.py` |
| `tests/webui/test_observability_workflow_dashboard_structure_contract_v1.py` |
| `tests/test_market_surface_api.py` |
| `tests/ops/test_futures_read_only_market_dashboard_contract_static_v0.py` |
| `tests/ops/test_market_dashboard_readonly_run_projection_spec_v0.py` |
| `tests/ops/test_market_surface_ranking_funnel_env_schema_boundary_v0.py` |
| `tests/scripts/test_materialize_market_dashboard_visual_operator_offline_bundles_v1.py` |

## Screenshot / Regression Evidence

- Harness Screenshots + Geometry Reports
- Durable Packs unter `docs&#47;product&#47;evidence&#47;**`
- Kein separates Pixel-Diff-Testpaket unter `tests/`

---

# 10 Dateibaum

Nur Dashboard-relevante Dateien (ohne `__pycache__`).

## Python — App / Surface / Runtimes

```
src/webui/app.py
src/webui/market_surface.py
src/webui/futures_read_only_market_dashboard_runtime_v0.py
src/webui/market_dashboard_current_state_snapshot_v0.py
src/webui/market_dashboard_current_state_runtime_v0.py
src/webui/market_active_paper_run_runtime_v0.py
src/webui/market_depth_api_v0.py
src/webui/market_depth_runtime_v0.py
src/webui/market_depth_readmodel_v0/__init__.py
src/webui/market_depth_readmodel_v0/builder.py
src/webui/market_tape_readmodel_v0/__init__.py
src/webui/market_tape_readmodel_v0/builder.py
src/webui/market_tape_readmodel_v0/gate.py
src/webui/market_ranking_funnel_runtime_v0.py
src/webui/market_ranking_funnel_readmodel_v0/__init__.py
src/webui/market_ranking_funnel_readmodel_v0/builder.py
src/webui/market_futures_ohlcv_runtime_v0.py
src/webui/market_futures_ohlcv_readmodel_v0/__init__.py
src/webui/market_futures_ohlcv_readmodel_v0/builder.py
src/webui/market_instrument_eligibility_v0.py
src/webui/double_play_dashboard_display_json_route_v0.py
src/webui/workflow_dashboard_runtime_v1.py
src/webui/last_paper_run_panel_runtime_v0.py
src/webui/last_paper_run_panel_readmodel_v0/
src/webui/market_visual_operator_surface_v1/__init__.py
src/webui/market_visual_operator_surface_v1/contracts.py
src/webui/market_visual_operator_surface_v1/runtime_v1.py
src/webui/market_visual_operator_surface_v1/decision_funnel_display_v1.py
src/webui/market_visual_operator_surface_v1/economic_observability_display_v1.py
src/webui/market_visual_operator_surface_v1/ai_linear_diagnostics_display_v1.py
src/webui/market_visual_operator_surface_v1/operator_header_display_v1.py
src/webui/market_visual_operator_surface_v1/operator_overview_display_v1.py
src/webui/workflow_dashboard_readmodel_v1/__init__.py
src/webui/workflow_dashboard_readmodel_v1/builder.py
src/webui/workflow_dashboard_readmodel_v1/pipeline_builder.py
src/webui/workflow_dashboard_readmodel_v1/paths.py
src/webui/workflow_dashboard_readmodel_v1/types.py
src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_fixture_source_v1.py
src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_real_metadata_source_v1.py
src/webui/workflow_dashboard_readmodel_v1/futures_universe_upstream_adapter_v1.py
src/webui/workflow_dashboard_readmodel_v1/kraken_metadata_coverage_reader_v1.py
src/webui/workflow_dashboard_readmodel_v1/universe_selection_contract_v1.py
src/webui/workflow_dashboard_readmodel_v1/universe_selection_producer_v1.py
src/webui/workflow_dashboard_readmodel_v1/universe_selection_reader_v1.py
```

## Templates

```
templates/peak_trade_dashboard/base.html
templates/peak_trade_dashboard/market_v0.html
templates/peak_trade_dashboard/double_play_market_dashboard_v0.html
templates/peak_trade_dashboard/futures_read_only_market_dashboard_v0.html
templates/peak_trade_dashboard/partials/double_play_market_compact_v1.html
templates/peak_trade_dashboard/partials/double_play_market_panel_v0.html
templates/peak_trade_dashboard/partials/futures_market_compact_v1.html
templates/peak_trade_dashboard/partials/futures_read_only_market_panel_v0.html
templates/peak_trade_dashboard/partials/last_paper_run_panel_v0.html
templates/peak_trade_dashboard/partials/market_ai_linear_diagnostics_visual_v1.html
templates/peak_trade_dashboard/partials/market_current_state_compact_v1.html
templates/peak_trade_dashboard/partials/market_decision_funnel_visual_v1.html
templates/peak_trade_dashboard/partials/market_diagnostics_drawer_v1.html
templates/peak_trade_dashboard/partials/market_economic_observability_visual_v1.html
templates/peak_trade_dashboard/partials/market_governed_top20_primary_v1.html
templates/peak_trade_dashboard/partials/market_legacy_operator_panels_v0.html
templates/peak_trade_dashboard/partials/market_primary_close_chart_v1.html
templates/peak_trade_dashboard/partials/market_primary_operator_hero_v1.html
templates/peak_trade_dashboard/partials/market_safety_compact_v1.html
templates/peak_trade_dashboard/partials/market_visual_operator_header_v1.html
templates/peak_trade_dashboard/partials/market_watchlist_compact_v1.html
templates/peak_trade_dashboard/partials/workflow_dashboard_v1_panels.html
```

## CSS / Vendor JS

```
static/css/peak_trade_dashboard_design_tokens_v1.css
static/css/peak_trade_dashboard_layout_v1.css
static/css/peak_trade_dashboard_utilities_v1.css
static/vendor/chartjs/4.4.1/chart.umd.min.js
static/vendor/chartjs/4.4.1/LICENSE.chartjs.txt
```

## Scripts / Config

```
scripts/webui/market_dashboard_chrome_playwright_harness_v1.py
scripts/webui/review_server_playwright_webserver_v1.py
scripts/webui/review_server.sh
scripts/webui/market_dashboard_landmark_discovery_capture_v1.py
scripts/webui/market_dashboard_phase1a_composition_capture_v1.py
scripts/ops/materialize_market_dashboard_visual_operator_offline_bundles_v1.py
scripts/ops/start_market_dashboard_visual_operator_readonly_v1.sh
scripts/ops/ci_test_selection_v1.py
config/ci/file_category_mapping.yaml
```

## Docs / Specs / Matrices / Evidence

```
docs/webui/MARKET_SURFACE_V0.md
docs/webui/REVIEW_SERVER_HARNESS_V1.md
docs/webui/market_visual_operator_surface_v1.local.example.env
docs/webui/observability/REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md
docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
docs/product/VISUAL_OPERATOR_DASHBOARD_IMPLEMENTATION_PLAN_V1.md
docs/product/matrices/dashboard_defect_closure_matrix_phase_1a.json
docs/product/matrices/dashboard_defect_closure_matrix_phase_1b.json
docs/product/matrices/dashboard_phase_binding_matrix.json
docs/product/matrices/dashboard_requirement_traceability_matrix.json
docs/ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md
docs/ops/specs/MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md
docs/ops/specs/MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md
docs/ops/specs/MASTER_V2_DOUBLE_PLAY_RUNTIME_PRODUCER_DASHBOARD_PREREQUISITE_PARKING_MAP_V0.md
docs/ops/specs/OPS_SUITE_DASHBOARD_VNEXT_SPEC.md
docs/product/evidence/phase_minus_1_rebaseline_v1_20260716T210645Z/
docs/product/evidence/phase_1a_20260716T180101Z/
docs/product/evidence/phase_1b_20260716T181219Z/
docs/product/evidence/phase_2_20260716T184639Z/
docs/product/evidence/visual_foundation_rework_v1_20260716T214800Z/
docs/product/evidence/visual_composition_first_refactor_v1_20260716T221000Z/
```

## Tests + Fixtures

```
tests/webui/test_market_dashboard_*.py
tests/webui/test_market_*.py
tests/webui/test_futures_read_only_market_dashboard_*.py
tests/webui/test_double_play_*.py
tests/webui/test_market_visual_operator_surface_v1.py
tests/webui/test_review_server_harness_v1.py
tests/webui/test_workflow_dashboard_*.py
tests/webui/test_observability_workflow_dashboard_structure_contract_v1.py
tests/test_market_surface_api.py
tests/ops/test_futures_read_only_market_dashboard_contract_static_v0.py
tests/ops/test_market_dashboard_readonly_run_projection_spec_v0.py
tests/ops/test_market_surface_ranking_funnel_env_schema_boundary_v0.py
tests/scripts/test_materialize_market_dashboard_visual_operator_offline_bundles_v1.py
tests/ci/test_ci_diff_aware_test_selection_v1.py
tests/fixtures/futures_read_only_market_dashboard_v0/
tests/fixtures/market_depth_readmodel_v0/
tests/fixtures/market_tape_readmodel_v0/
tests/fixtures/market_ranking_funnel_readmodel_v0/
tests/fixtures/market_futures_ohlcv_readmodel_v0/
tests/fixtures/workflow_dashboard_readmodel_v1/
```

## Runtime Artifacts (untracked)

```
.runtime/market-dashboard-composition-first.log
.runtime/market-dashboard-phase-minus-1-rebaseline.log
.runtime/market-dashboard-phase-minus-1-rebaseline.pid
.runtime/market-dashboard-pr5248.log
.runtime/market-dashboard-pr5249-merged.log
.runtime/market-dashboard-pr5250-review.log
```

---

END OF DISCOVERY


---

# Appendix

## Verwendung

1. PART I ist normativ und beschreibt die Zielarchitektur.
2. PART II dokumentiert den aktuellen technischen Ist-Zustand des Repositories.
3. Bei Abweichungen gilt:
   - Architektur- und Governance-Regeln aus PART I definieren das Ziel.
   - PART II dient als technische Referenz für Refactoring, Audits und Implementierung.
