# Visual Composition-First Refactor v1 — Implementation Manifest

```text
SLICE=VISUAL_COMPOSITION_FIRST_REFACTOR_V1
GO_TOKEN=GO_VISUAL_OPERATOR_DASHBOARD_COMPOSITION_REFACTOR_V1
BASE=origin/main@b9be86aa
BRANCH=feat/market-dashboard-composition-first-refactor-v1
SCOPE=presentation_only
COMPOSITION_FIRST=true
CARD_FIRST=false
NO_TRADING_LOGIC=true
NO_DECISION_LOGIC=true
NO_RISK_LOGIC=true
NO_ECONOMIC_LOGIC=true
NO_DATA_PRODUCER_CHANGES=true
NO_AUTHORITY_CHANGES=true
NO_RUNTIME_CHANGES=true
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_PLAYWRIGHT_CHANNEL=chrome
HARNESS=scripts/webui/market_dashboard_chrome_playwright_harness_v1.py
VIEWPORT=1440x900
```

## Product goal

Operator sieht **eine** Trading-Oberfläche (Bloomberg / TradingView / Kraken Pro Gefühl),
nicht eine Card-Wall / Admin-Panel / Widget-Sammlung.

Blickführung:

```text
MARKET → DECISION → BLOCKER → CHART → RANKING → DETAIL
```

## Layout decisions (why)

| Entscheidung | Begründung |
|---|---|
| Hero-Rahmen / Card-BG entfernt | Hero ist Teil der Gesamtkomposition, kein Widget |
| System-Decision Nested-Card entfernt | Decision/Blocker gehören visuell zum Hero (nur dezente linke Achse ab lg) |
| Chart Outer-Card + Ring entfernt | Chart als dominante Bühne, nicht als weitere Box |
| Safety-Rail Border/BG entfernt | Quiet Meta-Linie statt Status-Strip-Card |
| Ranking ohne Violet-Card/Ring | Zweite Ebene, keine Konkurrenz zum Primary Stage |
| Ranking-Toolbar Badges → Meta-Text | Anti-Badge-Wall; Funktion (Top20/50) bleibt |
| Secondary Bands (Funnel/Economic/Linear) → Hairline statt Card | Risk/Economic/Diagnostics bleiben sekundär und ruhig |
| Details (Diagnostics/Governance) → Borderless + Hairline | Weniger UI-Chrome unterhalb der Bühne |
| Type ladder Tokens (Hero/Decision/Section/Meta) | Vier klare Typo-Ebenen; Decision lauter als Meta |
| Unified primary stage Marker | Hero+Chart als eine Fläche, nicht zwei konkurrierende Primaries |

## Anti-patterns addressed

- `CARD_WALL`
- `BADGE_WALL` (Ranking toolbar)
- `COMPETING_PRIMARY_SURFACES` (Hero card vs Chart card)
- `ENGINEERING_FIRST_LAYOUT` (chrome reduction)
- `MULTIPLE_VISUAL_STARTING_POINTS` (fused hero/decision)

## Non-scope (confirmed)

- Keine neuen Dashboard-Bereiche / Widgets / Features
- Keine Producer-/API-/Authority-/Runtime-Änderungen
- Keine Tests entfernt

## Owners reused

| Surface | Owner |
|---|---|
| Tokens | `static/css/peak_trade_dashboard_design_tokens_v1.css` |
| Layout/composition | `static/css/peak_trade_dashboard_layout_v1.css` |
| Page shell | `templates/peak_trade_dashboard/market_v0.html` |
| Hero / Decision | `templates&#47;peak_trade_dashboard&#47;partials&#47;market_primary_operator_hero_v1.html` |
| Chart | `templates&#47;peak_trade_dashboard&#47;partials&#47;market_primary_close_chart_v1.html` |
| Ranking | `templates&#47;peak_trade_dashboard&#47;partials&#47;market_governed_top20_primary_v1.html` |
| Safety rail | `templates&#47;peak_trade_dashboard&#47;partials&#47;market_visual_operator_header_v1.html` |
| Harness | `scripts&#47;webui&#47;market_dashboard_chrome_playwright_harness_v1.py` |

## Chrome Playwright composition (1440×900) — AFTER

```text
BROWSER_ACTUAL=GOOGLE_CHROME
REAL_CHROME_VERIFIED=true
HEADER_HEIGHT_PX=45.6875
SAFETY_RAIL_HEIGHT_PX=17.0
HERO_HEIGHT_PX=210.0
CHART_HEIGHT_PX=390.0
PRIMARY_CHART_VISUAL_SHARE_PCT≈53.79
PRIMARY_CHART_VISUAL_SHARE_MIN_MET=true
CHART_TOP_VISIBLE_1440x900=true
COMPOSITION_CONTRACT_PASS=true
CONSOLE_ERRORS=0
```

## Evidence paths

- Before: `before&#47;01_full_viewport_1440x900.png`, `before&#47;03_hero_1440x900.png`, `before&#47;04_chart_1440x900.png`, `before&#47;browser&#47;`
- After: `after&#47;01_full_viewport_1440x900.png`, `after&#47;03_hero_1440x900.png`, `after&#47;04_chart_1440x900.png`, `after&#47;browser&#47;`
- Focused tests: `test_output&#47;focused_tests.txt`

## Stop condition

Bounded PR offen für Operator-Review. **Kein Merge** in diesem Slice.
