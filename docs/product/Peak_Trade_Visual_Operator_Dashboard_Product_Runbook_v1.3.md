# Peak Trade — Visual Operator Dashboard Product Runbook v1.3

## Zweck

Dieses Runbook definiert die verbindliche Produkt-, UX-, Visualisierungs-, Daten-, Safety-, Qualitäts- und Umsetzungsstruktur für das **Peak Trade Visual Operator Dashboard**.

Das Ziel ist kein technisches Debug-Panel und keine Ansammlung von Statuskarten, sondern ein hochwertiges, professionelles, read-only Market-, AI-, Risk- und Observability-Produkt, das visuell mit modernen Crypto- und Trading-Plattformen vergleichbar ist.

Das Dashboard muss auch gegenüber technisch versierten externen Betrachtern präsentabel sein. Es soll unmittelbar verständlich, visuell konsistent, glaubwürdig, schnell erfassbar und ohne peinliche Leerräume, abgeschnittene Komponenten, unverständliche Statuswände oder halb fertige Diagnosekarten nutzbar sein.

---

# 0. Verbindlicher Zielzustand

```text
PRODUCT_NAME=PEAK_TRADE_VISUAL_OPERATOR_DASHBOARD
PRODUCT_MODE=READ_ONLY
TARGET_QUALITY=PROFESSIONAL_OPERATOR_GRADE
TARGET_AUDIENCE=OPERATOR,TECHNICAL_REVIEWER,FUTURE_USER,DEMO_AUDIENCE
COMPARISON_CLASS=MODERN_CRYPTO_EXCHANGE_AND_PROFESSIONAL_TRADING_DASHBOARD
ABOVE_THE_FOLD_REFERENCE_VIEWPORT=1440x900
PRIMARY_VIEW_MAX_VERTICAL_SCROLL=0
PRIMARY_STATUS_COUNT_MAX=8
PRIMARY_DECISION_SENTENCE_REQUIRED=true
```

Der Zielzustand ist erreicht, wenn ein Nutzer innerhalb von fünf Sekunden erkennen kann:

1. Welcher Futures-Markt aktuell relevant ist.
2. Welche Instrumente im Ranking vorne liegen.
3. Welche Marktstruktur und welches Regime vorliegen.
4. Was Bull- und Bear-Layer aktuell sehen.
5. Welche AI-/Decision-Komponenten aktiv Daten verarbeitet haben.
6. Welche Stufe eine Aktion blockiert.
7. Wie frisch, vollständig und belastbar die Daten sind.
8. Wie Risiko, Economic Validity und Authority aktuell stehen.
9. Dass keine Live-, Order- oder Runtime-Autorisierung besteht.
10. Dass das Dashboard professionell, stabil und vorzeigbar ist.

Zusätzlich muss der Operator Overview eine einzelne, natürlich lesbare Entscheidungsaussage erzeugen, die mindestens Instrument, Regime, Decision State und primären Blocker zusammenfasst.

Beispielstruktur:

```text
<INSTRUMENT> steht auf Rang <N>. Regime <STATE>. Decision <STATE>. Primärer Blocker: <REASON>.
```

Die Aussage darf keine unbelegte Interpretation, keine Profitabilitätsbehauptung und keine Autorisierungswirkung enthalten.

---



# 0A. Dashboard Authority Model

Dieses Runbook definiert ausschließlich die Präsentationsschicht des Dashboards. Es ersetzt, erweitert oder überschreibt niemals die fachliche Wahrheit des Peak_Trade-Core-Systems.

```text
CORE_SYSTEM_SINGLE_SOURCE_OF_TRUTH=true
CANONICAL_CORE_OWNER=MASTER_V2
DASHBOARD_ROLE=PRESENTATION_LAYER
DASHBOARD_IS_CONSUMER_ONLY=true
DASHBOARD_OWNS_NO_TRADING_SEMANTICS=true
DASHBOARD_OWNS_NO_DECISION_STATE=true
DASHBOARD_OWNS_NO_RISK_STATE=true
DASHBOARD_OWNS_NO_ECONOMIC_STATE=true
DASHBOARD_OWNS_NO_AUTHORITY_STATE=true
DASHBOARD_MAY_NOT_REIMPLEMENT_CORE_LOGIC=true
DASHBOARD_MAY_NOT_OVERRIDE_CORE_SEMANTICS=true
ALL_DASHBOARD_VALUES_MUST_BE_TRACEABLE_TO_CANONICAL_OWNER=true
DASHBOARD_PRODUCT_SPEC_SSOT=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
DERIVED_DOCUMENTS_MAY_NOT_OVERRIDE_PRODUCT_SPEC=true
CORE_SYSTEM_REMAINS_FUNCTIONAL_SSOT=true
```

SSOT-Unterscheidung:

- fachliche Core-SSOT = kanonisches Peak_Trade-Core-System / Master V2
- Dashboard-Produkt-SSOT = dieses Runbook (Presentation / UX / Implementation Spec only)
- Dashboard selbst = Consumer-only; besitzt keine Trading-, Risk-, Economic-, Decision- oder Authority-Ownership

Architekturgrundsatz:

- Das Core-System bleibt die einzige fachliche Wahrheit.
- Das Dashboard ist ausschließlich Consumer.
- Jeder dargestellte Wert muss auf einen kanonischen Core-Owner oder einen dokumentierten Adapter zurückführbar sein.
- Adapter dürfen Daten transformieren oder visualisieren, jedoch keine fachliche Logik, Entscheidungen oder Authority erzeugen.
- Existiert bereits ein kanonischer Owner, darf keine zweite Implementierung im Dashboard entstehen.
- Abgeleitete Docs (Implementation Plan, Patch-Empfehlungen, technische Surface-Chronicle) dürfen dieses Product Runbook nicht überschreiben.

---

# 0A. Kanonische Implementation Baseline

Diese Baseline bindet das Runbook an die reale, read-only geprüfte Dashboard-Architektur. Sie ist Ausgangspunkt für jede Umsetzung. Bei Abweichungen zwischen Annahme und Repository-Realität gilt: zuerst Discovery aktualisieren, dann Runbook patchen, erst danach mutieren.

```text
DISCOVERY_GO_TOKEN=GO_PEAK_TRADE_VISUAL_OPERATOR_DASHBOARD_IMPLEMENTATION_DISCOVERY_V1
DISCOVERY_BASELINE_HEAD=20969b4a155ffbdc0e1a9a55657311aa061511be
DISCOVERY_BASELINE_PR=5244
DISCOVERY_BASELINE_BRANCH=feat/market-dashboard-visual-operator-surface-v1
DISCOVERY_BASELINE_WORKTREE_CLEAN=true
DISCOVERY_READ_ONLY_CONFIRMED=true
DASHBOARD_ROUTE=/market
DASHBOARD_ROUTE_OWNER=src/webui/market_surface.py::create_market_router
PAGE_DATA_RESOLVER=src/webui/market_surface.py::resolve_market_page_data
DISPLAY_CONTEXT_OWNER=src/webui/market_surface.py::build_market_v0_page_template_context
SNAPSHOT_OWNER=src/webui/market_dashboard_current_state_snapshot_v0.py::market_dashboard_current_state_snapshot_v0
PRIMARY_TEMPLATE=templates/peak_trade_dashboard/market_v0.html
PRIMARY_CSS_OWNER=templates/peak_trade_dashboard/market_v0.html+base.html
PRIMARY_CHART_RENDERER=SSR_SVG
DETAIL_CHART_LIBRARY=Chart.js_4.4.1
MARKET_BROWSER_E2E_BASELINE=MISSING
PRIMARY_BROWSER_BASELINE=PLAYWRIGHT_CHANNEL_CHROME
REAL_SAFARI_BASELINE=SECONDARY_COMPATIBILITY_OPTIONAL
```

Die Commit- und PR-Angaben sind Discovery-Evidence, keine dauerhafte Freigabe für weitere Arbeiten. Vor jeder Mutation sind `origin&#47;main`, aktueller `HEAD`, PR-Zustand und Worktree erneut zu prüfen.

## 0A.1 Kanonische Render Chain

```text
Browser
  ↓ GET /market?symbol=<SYMBOL>&top_n=<20|50>
src/webui/app.py
  ↓ include_router(create_market_router(...))
src/webui/market_surface.py::create_market_router
  ↓ market_v0_page
src/webui/market_surface.py::resolve_market_page_data
  ↓ normalisierte URL-/Selection-Parameter
src/webui/market_surface.py::build_market_v0_page_template_context
  ├─ OHLCV builder
  ├─ Ranking builder
  ├─ F5 builder
  ├─ Decision / Double-Play builder
  ├─ Economic builder
  ├─ Linear diagnostics builder
  ├─ Safety / Governance builder
  └─ market_visual_operator_surface_v1 context
  ↓
templates/peak_trade_dashboard/market_v0.html
  ↓ SSR partials
Header → Hero → Chart → Ranking → Decision → Risk → Economic → Diagnostics → Governance
  ↓
Full SSR HTML in Google Chrome (Playwright channel=chrome);
Chromium fallback allowed when Chrome channel unavailable;
Safari / WebKit secondary compatibility only
```

Verbindlich:

```text
RESOLVE_MARKET_REQUEST_STATE_EXISTS=false
CANONICAL_REQUEST_RESOLVER=resolve_market_page_data
NO_SECOND_RENDER_CHAIN_ALLOWED=true
NO_PARALLEL_DASHBOARD_TRUTH_ALLOWED=true
```

# 0B. Verbindlicher Visual Blueprint

## 0B.1 Above-the-fold Blueprint — 1440×900

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPACT GLOBAL HEADER + SINGLE SAFETY RAIL                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ SELECTED INSTRUMENT + DECISION NARRATIVE        │ CRITICAL SYSTEM STATE     │
│ compact metadata row                             │ compact, non-redundant    │
├─────────────────────────────────────────────────────────────────────────────┤
│ PRIMARY CANDLESTICK + VOLUME CHART                                      │   │
│ chart must begin and be materially visible inside 1440×900 viewport       │   │
└─────────────────────────────────────────────────────────────────────────────┘
```

Unterhalb des ersten Viewports:

```text
ROW_2=RANKING_PRIMARY + DECISION_SUMMARY
ROW_3=DECISION_CHAIN + RISK_SAFETY
ROW_4=ECONOMIC + DIAGNOSTIC_SUMMARY
ROW_5=COLLAPSED_GOVERNANCE_AND_ENGINEERING_DETAILS
```

Abnahmeregeln:

```text
CHART_TOP_VISIBLE_AT_1440x900=true
CHART_MEANINGFULLY_VISIBLE_AT_1440x900=true
DUAL_STATUS_RAILS_FORBIDDEN=true
F5_RAW_METADATA_IN_HERO_FORBIDDEN=true
PRIMARY_HERO_TECHNICAL_DUMP_FORBIDDEN=true
GIANT_EMPTY_REGION_ABOVE_CHART_FORBIDDEN=true
```

## 0B.2 Visual Priority Matrix

| Priorität | Surface | Visuelles Gewicht | Primäre Frage |
|---:|---|---|---|
| 1 | Market Chart | dominant | Was macht der Markt? |
| 2 | Decision Narrative / State | sehr hoch | Was sieht und entscheidet das System? |
| 3 | Ranking | hoch | Welche Instrumente sind aktuell relevant? |
| 4 | Regime / Bull-Bear | mittel-hoch | Warum ist der Zustand so? |
| 5 | Risk / Safety | mittel | Was wäre riskant oder blockiert? |
| 6 | Economic Observability | mittel | Ist die Evidence wirtschaftlich tragfähig? |
| 7 | AI / Linear Diagnostics | niedrig-mittel | Wie belastbar sind Modell-/Diagnoseaussagen? |
| 8 | Governance / Engineering | niedrig, eingeklappt | Woher stammt die technische Evidence? |

Kein niedriger priorisierter Bereich darf durch Höhe, Badge-Dichte, Farbe oder Textmenge einen höher priorisierten Bereich dominieren.

# 0C. Component-, Owner- und Reuse-Matrix

| Component | Kanonischer Owner / Template | Discovery-Zustand | Verbindliche Behandlung | Zielphase |
|---|---|---|---|---|
| Legacy Status Rail | `market_v0.html` | redundant, Badge-Wall | entfernen oder in Single Safety Rail konsolidieren | 1A |
| Visual Operator Header | `partials&#47;market_visual_operator_header_v1.html` | teilweise korrekt | reuse + verdichten | 1A |
| Selected Instrument Hero | `partials&#47;market_primary_operator_hero_v1.html` | zu dicht, F5-/Gov-Dump | strukturell überarbeiten | 1A/2 |
| Primary Chart | `partials&#47;market_primary_close_chart_v1.html` | reale 120 Bars, unter Fold | reuse + reposition + polish | 1A/3 |
| Ranking | `partials&#47;market_governed_top20_primary_v1.html` | real Top20/50, sparse columns | single canonical component; contract-first | 4A–4C |
| Decision Funnel | `partials&#47;market_decision_funnel_visual_v1.html` | nicht selection-bound; `ACTIVE` | rewire + activity contract | 5A/5B |
| Economic | `partials&#47;market_economic_observability_visual_v1.html` | teilweise, Kurven fehlen | reuse; Scope sichtbar; honest missing | 7 |
| Linear Diagnostics | `partials&#47;market_ai_linear_diagnostics_visual_v1.html` | sparse | summary in Level 2, Details Level 3 | 8 |
| F5 Compact | `partials&#47;futures_market_compact_v1.html` | unvollständige Feld-Dumps | narrow adapter; aus Hero entfernen | 1A/9 |
| Double-Play Compact | `partials&#47;double_play_market_compact_v1.html` | static fixture, nicht selection-bound | klar labeln oder nicht primär zeigen | 5A/5B |
| Safety Compact | `partials&#47;market_safety_compact_v1.html` | badge-dense | semantic groups Risk/Safety | 6 |
| Watchlist | `partials&#47;market_watchlist_compact_v1.html` | brauchbar | reuse as navigation aid | 4B |
| Detail Anchors | DP/F5 Detail Partials | CDN, doppelt | Governance/Detail only; vendorize assets | 1B/9 |
| Current State | `partials&#47;market_current_state_compact_v1.html` | korrekt collapsed | reuse | 9 |
| Diagnostics Drawer | `partials&#47;market_diagnostics_drawer_v1.html` | legacy density | consolidate or retire | 8/9 |

## 0C.1 Reuse Decision Matrix

```text
OHLCV=REUSE_AS_IS
RANKING=REUSE_AS_IS_DATA_OWNER;REWORK_VISUAL_CONTRACT
F5=REUSE_WITH_NARROW_ADAPTER
DECISION_FUNNEL=REWIRE_EXISTING
ECONOMIC=REWIRE_EXISTING_SCOPE_AND_CONTEXT
LINEAR=REUSE_WITH_NARROW_ADAPTER
DOUBLE_PLAY=REUSE_AS_IS_ONLY_WITH_EXPLICIT_FIXTURE_OR_SCOPE_LABEL
SAFETY=REUSE_DERIVATION;REWORK_VISUAL_SEMANTICS
CURRENT_STATE=REUSE_AS_IS_COLLAPSED
```

Neue Komponenten sind nur zulässig, wenn keine kanonische Owner-Struktur existiert oder ein dokumentierter Contract-Gap dies erfordert.

# 0D. Data Owner und Source Binding Matrix

| Datenfeld / Surface | Kanonischer Owner | Source Class | Instrument-scoped | Status / Regel |
|---|---|---|---:|---|
| OHLCV / Volume | `market_futures_ohlcv_runtime_v0.py` | `CANONICAL_LOCAL_READ_ONLY_BUNDLE` | ja | reuse, kein Request-Time-Netzwerk |
| Ranking Top20/50 | `market_ranking_funnel_runtime_v0.py` | Offline volume-rank bundle | ja | real distinct views; Target: Bitcoin-direction disabled (Default-Gap siehe §1) |
| Score | Ranking `display_score` | deterministic derivation | ja | implemented |
| Rank Delta | kein Owner | — | — | data-blocked; nicht erfinden |
| Regime | Ranking passthrough | unvollständig | teilweise | hide/de-emphasize until producer exists |
| Momentum / Volatility / Liquidity | OHLCV derivation | deterministic | ja | partial; Quality sichtbar |
| Bull/Bear Assessment | Double-Play display fixture | static in-process fixture | nein | nicht als aktuelle Instrument-Evidence darstellen |
| Decision Funnel | `decision_funnel_display_v1.py` | manifest-verified offline evidence | nein, baseline | explizit `NOT_INSTRUMENT_SCOPED` bis Rewire |
| Risk / Safety / Authority | Safety matrix + current state | deterministic / repo snapshot | teilweise | Semantik getrennt darstellen |
| Economic | `economic_observability_display_v1.py` | baseline evidence | nein, baseline | Scope/Compatibility sichtbar |
| Linear Diagnostics | `ai_linear_diagnostics_display_v1.py` | evidence bundle | scope-abhängig | Scope sichtbar |
| Selection Context ID | kein Owner | — | — | Pflicht neu einzuführen |
| Snapshot ID | nur Snapshot-Version vorhanden | repo snapshot | — | kohärenten UI-Vertrag einführen |

Browser-CDNs zählen als externe Request-Time-Abhängigkeit des Produkts und sind nicht durch die Venue-/Credential-Netzwerkfreiheit ausgenommen.

```text
TAILWIND_CDN_ALLOWED_IN_TARGET_STATE=false
CHART_JS_CDN_ALLOWED_IN_TARGET_STATE=false
VENDORED_OR_BUNDLED_ASSETS_REQUIRED=true
NETWORK_ALLOWLIST_DEFAULT=SELF_ONLY
```

# 0E. Selection Context und Snapshot Identity Contract

Der wichtigste Integritätsvertrag des Dashboards ist eine atomare, nachvollziehbare Auswahl- und Snapshot-Identität.

```text
selection_context_id = digest(
  selected_symbol,
  timeframe,
  ranking_limit,
  market_snapshot_id,
  decision_snapshot_id_or_scope_marker,
  economic_snapshot_id_or_scope_marker,
  risk_snapshot_id_or_scope_marker
)
```

Jeder Surface Context muss mindestens enthalten:

```text
selection_context_id
snapshot_id
instrument_scope
scope_compatibility
source_id
freshness_state
quality_state
```

Zulässige Scope-Kompatibilität:

```text
MATCHED_SELECTED_INSTRUMENT
FLEET_LEVEL_NOT_INSTRUMENT_SCOPED
PORTFOLIO_LEVEL_NOT_INSTRUMENT_SCOPED
STRATEGY_FAMILY_LEVEL_NOT_INSTRUMENT_SCOPED
INCOMPATIBLE_WITH_SELECTION
UNKNOWN_SCOPE
```

Atomare SSR-Regel:

```text
ONE_REQUEST_ONE_COMMITTED_SELECTION_CONTEXT=true
ALL_CONTEXT_BUILDERS_COMPLETE_BEFORE_RENDER=true
PARTIAL_SURFACE_COMMIT_FORBIDDEN=true
MISMATCHED_CONTEXT_RENDER_FORBIDDEN=true
```

Implementierungsstand (Discovery / Bootstrap, docs-only):

```text
SELECTION_CONTEXT_IMPLEMENTED=false
SELECTION_CONTEXT_REQUIRED_BEFORE_PHASE_4C_COMPLETE=true
SELECTION_CONTEXT_PSEUDO_ID_FORBIDDEN=true
```

`selection_context_id` ist ein verpflichtender offener Contract-Gap. Es darf nicht als bereits implementiert dargestellt, nicht durch Pseudo-IDs ersetzt und nicht durch stille Fallbacks vorgetäuscht werden. Closure nur in Phase 4C mit Owner-, Test- und Screenshot-Binding.

Eine fleet-level oder baseline-level Surface darf unverändert bleiben, wenn ein Instrument gewechselt wird, aber nur, wenn sie sichtbar als nicht instrument-scoped markiert ist. Sie darf nicht den Eindruck erwecken, zur neu ausgewählten Zeile zu gehören.

# 0F. Discovery Defect Closure Matrix

| Defect | Befund | Severity | Verbindliche Zielphase | Closure Evidence |
|---|---|---:|---|---|
| D1 | Duale Badge-/Status-Rails | HIGH | 1A | single header/safety rail screenshot + DOM assertion |
| D2 | Chart unter 1440×900 Fold | HIGH | 1A | viewport screenshot + bounding-box assertion |
| D3 | wahrgenommene große Leerregion | HIGH | 1A | screenshot diff + geometry check |
| D4 | `unavailable` dominiert Ranking | HIGH | 4A/4B | column policy tests + screenshot |
| D5 | Ranking min-width Overflow-Risiko | MED | 4B | DOM overflow assertion |
| D6 | schwache Hierarchie / Engineering im Hero | HIGH | 1A/2 | visual review + content ownership test |
| D7 | Statusduplikation Header/Rail/Safety | MED | 1A/6 | semantic uniqueness test |
| D8 | irreführendes grünes `ACTIVE` | MED | 5A | state-contract tests |
| D9 | unerwartete Browser-CDNs | MED | 1B | network allowlist test; zero external requests |
| D10 | fragmentiertes Design System | HIGH | 1B | central token owner + no duplicate inline tokens test |

Kein Defect darf nur kosmetisch als geschlossen markiert werden. Closure benötigt Code-/Contract-Evidence, fokussierte Tests und Screenshot-Evidence.

---

# 1. Nicht verhandelbare Grenzen

```text
READ_ONLY=true
FUTURES_ONLY=true
BITCOIN_DIRECTION_ALLOWED=false
SPOT_ALLOWED=false
SYNTHETIC_SPOT_ALLOWED=false

LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false
SHADOW_AUTHORIZED=false
PAPER_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false

NO_REQUEST_TIME_NETWORK_ACCESS=true
NO_IMPLICIT_VENUE_CONNECTION=true
NO_CREDENTIAL_USE=true
NO_SIDE_EFFECTS=true
NO_FAKE_MARKET_DATA=true
NO_SYNTHETIC_REPLACEMENT_FOR_MISSING_PRODUCTION_DATA=true
NO_DEMO_DATA_PRESENTED_AS_REAL=true

DASHBOARD_REQUEST_HANDLER_NETWORK_FREE=true
DASHBOARD_IMPORT_GRAPH_CREDENTIAL_FREE=true
DASHBOARD_RENDER_SIDE_EFFECT_FREE=true
DASHBOARD_DATA_ACCESS_ALLOWLIST_REQUIRED=true
DASHBOARD_ROUTE_MUTATION_CONTROLS_FORBIDDEN=true
```

Discovery-/Default-Gap (dokumentarisch; keine Runtime-Mutation in diesem Slice):

```text
TARGET_CONTRACT_FUTURES_ONLY=true
TARGET_CONTRACT_BITCOIN_DIRECTION_DISABLED=true
CURRENT_REPO_OR_DOCS_DEFAULT_MAY_INCLUDE_KRAKEN_OR_BTC=true
CURRENT_DEFAULT_MUST_NOT_BE_CLAIMED_AS_ALREADY_COMPLIANT=true
BTC_KRAKEN_DEFAULT_GAP_REQUIRES_SEPARATE_BOUNDED_SLICE=true
```

Der Target Contract bleibt Futures-only und Bitcoin-direction-disabled. Ein aktueller Repo- oder Docs-Default (z. B. Kraken/BTC in der technischen Surface-Chronicle) darf nicht als bereits compliant dargestellt werden. Die Behebung benötigt einen separaten bounded Slice mit Owner- und Test-Bindung; Runtime-/Producer-Defaults werden hier nicht geändert.

Das Dashboard darf Daten darstellen, erklären, vergleichen und visualisieren.

Das Dashboard darf niemals:

- Orders auslösen,
- Sessions aktivieren,
- Broker- oder Exchange-Zugriffe starten,
- Runtime Authority erzeugen,
- Strategy Authority erzeugen,
- Positionen verändern,
- Risk-, Sizing-, Safety- oder Promotion-Gates überschreiben,
- Daten erfinden,
- fehlende Daten durch stillschweigende Fallbacks ersetzen.

Diese Grenzen müssen durch statische und browserbasierte Tests belegbar sein. Insbesondere sind verbotene Imports, Provider-Aufrufe, Credential-Zugriffe, mutierende Controls und unerwartete Browser-Netzwerkzugriffe im Dashboard-Pfad als Merge-Blocker zu behandeln.

---

# 2. Produktprinzipien

## 2.1 Operator-first

Die Oberfläche wird nach Nutzerfragen strukturiert, nicht nach internen Modulen.

Primäre Nutzerfragen:

```text
WHAT_IS_HAPPENING?
WHY_IS_IT_HAPPENING?
WHAT_DOES_THE_SYSTEM_SEE?
WHAT_IS_BLOCKING_ACTION?
HOW_FRESH_IS_THE_DATA?
WHAT_IS_THE_CURRENT_RISK?
WHAT_IS_THE_ECONOMIC_STATE?
```

Interne Owner, Contracts, Manifest-Digests und Debug-Felder gehören in sekundäre, einklappbare Bereiche.

## 2.2 Show, do not dump

Erlaubt:

- Charts,
- Heatmaps,
- Sparklines,
- Score Bars,
- Funnel,
- Timelines,
- Matrices,
- compact KPIs,
- visual status rails.

Nicht als primäre Darstellung erlaubt:

- lange Rohtextblöcke,
- Status-Badge-Wände,
- unstrukturierte `missing`-Listen,
- endlose Kartenstapel,
- breite Tabellen mit überwiegend `unavailable`,
- technische Felder ohne visuelle Priorisierung.

## 2.3 Data truth before decoration

```text
REAL_DATA_FIRST=true
PROVENANCE_VISIBLE=true
FRESHNESS_VISIBLE=true
QUALITY_VISIBLE=true
MISSING_DATA_EXPLICIT=true
```

Schöne Visualisierung ist nur zulässig, wenn Datenherkunft und Zustandssemantik korrekt bleiben.

## 2.4 Progressive disclosure

Drei Ebenen:

```text
LEVEL_1=OPERATOR_OVERVIEW
LEVEL_2=ANALYTICAL_DETAIL
LEVEL_3=ENGINEERING_AND_GOVERNANCE_DETAIL
```

Level 1 muss ohne Scroll-Wüste verständlich sein.

Verbindliche Zuordnung:

```text
LEVEL_1_CONTENT=HEADER,HERO,MARKET_CHART,RANKING,DECISION_SUMMARY
LEVEL_2_CONTENT=DECISION_CHAIN,RISK,ECONOMIC,DIAGNOSTIC_SUMMARY
LEVEL_3_CONTENT=PROVENANCE,CONTRACTS,MANIFESTS,RAW_EVIDENCE,ENGINEERING_DETAILS
```

Level 3 darf umfangreich sein, ist aber standardmäßig eingeklappt.

Zusätzliche Regeln zur visuellen Ruhe:

```text
MAX_SIMULTANEOUS_ACCENT_COLORS=4
MAX_BADGES_PER_PRIMARY_CARD=3
MAX_PRIMARY_CARDS_ABOVE_FOLD=5
ONE_DOMINANT_VISUAL_PER_SECTION=true
```

---

# 3. Verbindliche Informationsarchitektur

## 3.1 Global Header

Der Header muss kompakt bleiben und folgende Informationen enthalten:

- Peak Trade Logo / Produktname
- Read-only Status
- Futures-only Status
- Daten-Freshness
- Datenquelle
- Economic Gate
- Runtime Authority
- Orders
- Live
- aktueller Snapshot-Zeitpunkt

Verbindliche visuelle Gruppierung:

```text
HEADER_LEFT=PRODUCT_IDENTITY
HEADER_CENTER=SNAPSHOT_TIME,SOURCE,FRESHNESS
HEADER_RIGHT=READ_ONLY,ECONOMIC_STATE,AUTHORITY_STATE
SAFETY_RAIL=EXECUTION_DISABLED,ORDERS_DISABLED,LIVE_DISABLED,FUTURES_ONLY
```

Orders, Live, Runtime und Futures-only dürfen nicht als vier konkurrierende Hauptbadges erscheinen. Sie sind als kompakter Safety Rail zu bündeln. Nur Abweichungen oder Inkonsistenzen erhalten erhöhte visuelle Priorität.

Nicht erlaubt:

- mehrere redundante Badge-Reihen,
- unklare doppelte Statusanzeigen,
- technische Versionsblöcke im Hauptfokus,
- mehr als drei prominente Statusbadges im Header,
- starke visuelle Alarmierung für erwartete sichere Zustände wie `LIVE_DISABLED`.

## 3.2 Operator Overview Hero

Der erste sichtbare Inhaltsbereich muss folgende Elemente enthalten:

### A. Selected Instrument
- Symbol
- Exchange
- Contract Type
- Timeframe
- Last Price
- Change
- High / Low
- Volume
- Rank
- Score

### B. Market Regime
- Trend
- Momentum
- Volatility
- Liquidity
- Bull/Bear Balance
- Confidence / evidence state
- Freshness

### C. Current Decision State
- Observe / Candidate / Confirmed / Blocked
- Long / Short / Neutral
- Top block reason
- Current pipeline stage
- AI activity state
- data quality state

### D. Critical System State
- Economic Validity
- Runtime Authority
- Orders
- Live
- Risk status
- Safety status

Dieser Bereich muss auf einem normalen Desktop ohne übermäßiges Scrollen sichtbar sein.

Verbindliche Hierarchie:

```text
HERO_PRIMARY=SELECTED_INSTRUMENT_AND_DECISION_NARRATIVE
HERO_SECONDARY=MARKET_REGIME
HERO_TERTIARY=CRITICAL_SYSTEM_STATE
HERO_LAYOUT_REFERENCE=8_COLUMNS_PRIMARY,4_COLUMNS_SYSTEM_STATE
```

High, Low, Volume, Rank und Score werden als kompakte Metadatenzeile dargestellt und nicht als eigenständige KPI-Kachelreihe. Die aktuelle Entscheidungsaussage besitzt höhere visuelle Priorität als der letzte Preis.

## 3.3 Market Chart

Pflicht:

- Candlestick Chart
- Volume
- Zeitachse
- Preisachse
- Tooltip
- Instrument
- Timeframe
- Bar count
- Freshness
- Source
- O/H/L/C
- Zoom oder auswählbare Fenster, sofern vorhandene Architektur dies unterstützt

Optional später:

- VWAP
- volatility bands
- entry / exit markers
- regime overlays
- strategy markers

Leere Chartflächen ohne präzise Erklärung sind verboten.

Zusätzliche Chart-Verträge:

```text
DEFAULT_VISIBLE_BARS=120
SUPPORTED_CHART_WINDOWS=50,120,250,ALL
GAP_RENDERING_POLICY=EXPLICIT
STALE_DATA_OVERLAY_REQUIRED=true
MISSING_INTERVALS_MARKED=true
TIMEZONE_VISIBLE=true
PRICE_PRECISION_SOURCE_BOUND=true
NO_VISUAL_INTERPOLATION_OF_MISSING_BARS=true
```

Volume bleibt dem Preisbereich visuell untergeordnet. Source, Freshness und Bar Count werden in einer kompakten Chart-Metazeile geführt.

## 3.4 Ranking Surface

Top 20 und Top 50 müssen echte unterschiedliche Datenansichten sein.

Primär sichtbare Pflichtspalten:

- Rank
- Instrument
- Score
- Rank change
- Long/Short balance
- Regime
- Momentum
- Volatility
- Last / Change
- Freshness

Sekundäre Detailfelder über Row Expansion, Detail Drawer oder Tooltip:

- Eligibility
- Liquidity
- Bull / Long
- Bear / Short
- Data status
- Source details

Pflichtinteraktion:

- Instrument anklicken
- Chart aktualisiert sich
- AI-/Decision-Bereich aktualisiert sich
- Risk-/Economic-Kontext aktualisiert sich
- ausgewählte Zeile bleibt sichtbar markiert

Pflichtvisualisierung:

- Score Bar
- Rank delta
- Momentum indicator
- Volatility indicator
- Liquidity indicator
- Long/Short balance
- kleine Sparkline, sofern Daten vorhanden

Zusätzliche Ranking-Verträge:

```text
RANKING_SINGLE_CANONICAL_COMPONENT=true
RANKING_LIMIT_STATE_EXPLICIT=true
RANKING_STABLE_SORT_REQUIRED=true
RANKING_TIE_BREAK_POLICY_REQUIRED=true
SELECTED_ROW_PERSISTS_AFTER_SORT=true
SELECTION_URL_STATE_REQUIRED=true
NO_ROW_SELECTION_WITHOUT_COMPLETE_CONTEXT_UPDATE=true
```

Nicht erlaubt:

- Top 20 und Top 50 als bloße Labels ohne echte Datenumschaltung,
- Tabellen, in denen `unavailable` visuell dominiert,
- horizontale Überläufe,
- abgeschnittene Spalten,
- zwei getrennte Ranking-Implementierungen mit divergierender Semantik.

## 3.5 AI / Canonical Decision Chain

Das Dashboard muss den AI-/Decision-Layer als tatsächliche Verarbeitungskette visualisieren.

Pflichtstufen:

```text
Market Input
→ Market Context
→ Bull Assessment
→ Bear Assessment
→ State Transition
→ Survival
→ Suitability
→ Double Play
→ Entry Preconditions
→ Risk / Sizing
→ Portfolio Admissibility
→ Decision Outcome
```

Für jede Stufe muss ein Activity State existieren:

```text
NOT_AVAILABLE
AVAILABLE_NOT_RUN
PROCESSED
BLOCKED
STALE
FAILED
```

`ACTIVE` alleine ist verboten.

Eine Stufe darf nur als `PROCESSED` erscheinen, wenn aktuelle Evidence tatsächliche Verarbeitung belegt.

Verbindliche Gruppierung:

```text
INPUT=MARKET_INPUT,MARKET_CONTEXT
ASSESSMENT=BULL_ASSESSMENT,BEAR_ASSESSMENT,STATE_TRANSITION
VALIDATION=SURVIVAL,SUITABILITY,DOUBLE_PLAY
ADMISSIBILITY=ENTRY_PRECONDITIONS,RISK_SIZING,PORTFOLIO_ADMISSIBILITY
OUTCOME=DECISION_OUTCOME
```

Die Gruppen bilden die primäre Visualisierung. Einzelstufen werden innerhalb der Gruppe oder nach Expansion sichtbar.

Jede Stufe benötigt mindestens:

```text
state
reason_code
evidence_ref
processed_at
input_snapshot_id
```

Semantische Trennschärfe:

```text
BLOCKED != FAILED
STALE != NOT_AVAILABLE
AVAILABLE_NOT_RUN != PROCESSED_WITH_NEUTRAL_RESULT
```

### Pflichtvisualisierungen

- Decision Funnel
- Bull vs Bear Score
- Bull/Bear contribution bars
- Survival subcheck matrix
- Suitability result
- Double-Play composition matrix
- current decision timeline
- block reason histogram
- reason-code timeline
- change since previous snapshot

## 3.6 Risk and Safety

Der Risk-/Safety-Bereich muss kompakt, verständlich und visuell sein.

Pflicht:

- Risk availability
- Risk gate
- Safety guard
- KillSwitch
- exposure
- leverage
- margin usage
- liquidation distance
- funding risk
- reconciliation state
- authority state

Risk und Safety werden als getrennte semantische Gruppen dargestellt:

```text
RISK=EXPOSURE,LEVERAGE,MARGIN_USAGE,LIQUIDATION_DISTANCE,FUNDING_RISK
SAFETY=AUTHORITY,KILLSWITCH,RECONCILIATION,EXECUTION_PERMISSION
```

Fehlende oder nicht anwendbare Werte müssen differenziert werden:

```text
NOT_APPLICABLE_NO_POSITION
MISSING_EXPECTED_SOURCE
UNAVAILABLE_RUNTIME_DISABLED
STALE
INVALID
```

Fehlende Werte werden als kompakte Hinweise dargestellt, nicht als lange gelbe Feldlisten im Hauptbereich. Ein erwarteter sicherer Zustand wie `UNAVAILABLE_RUNTIME_DISABLED` darf nicht wie ein Datenfehler aussehen.

## 3.7 Economic Observability

Wenn Economic Evidence vorhanden ist:

- Equity curve
- Drawdown curve
- Gross / Cost / Net
- Fees
- Slippage
- Funding
- Profit Factor
- Expectancy
- Break-even cost
- Required gross edge
- Trade count
- Turnover
- Max Drawdown
- Sharpe / Sortino
- regime contribution
- long / short contribution

Negative Evidence wird sichtbar und unverändert dargestellt.

Zero trades werden nicht versteckt.

Keine Profitabilitätsbehauptung ohne manifest-verifizierte Evidence.

Economic Evidence muss immer sichtbar an ihren tatsächlichen Gültigkeitsbereich gebunden sein:

```text
ECONOMIC_SCOPE_VISIBLE=true
ECONOMIC_BINDING_ID_VISIBLE=true
ECONOMIC_EVIDENCE_AGE_VISIBLE=true
ECONOMIC_SELECTED_INSTRUMENT_COMPATIBILITY_VISIBLE=true
```

Der Nutzer muss erkennen können, ob Evidence für ein einzelnes Instrument, eine Strategy Family, ein Portfolio, einen Offline-Baseline-Run oder ein anderes Zeitfenster gilt.

## 3.8 AI / Linear Diagnostics

Wenn vorhanden:

- coefficient contribution
- factor exposure
- orthogonality matrix
- correlation matrix
- residual diagnostics
- train vs validation error
- condition number
- parameter sensitivity
- rolling drift

Wenn nicht vorhanden:

- kompakte Empty-State Card
- fehlender Owner
- fehlendes Evidence-Artefakt
- nächster zulässiger Offline-Slice

Keine große leere Fläche.

Im Level-2-Hauptfluss werden nur folgende Diagnostics-Zusammenfassungen gezeigt:

```text
MODEL_DIAGNOSTIC_STATE
TOP_CONTRIBUTING_FACTORS
DRIFT_STATE
VALIDATION_STATE
```

Orthogonality Matrix, Correlation Matrix, Residual Diagnostics, Condition Number und detaillierte Sensitivity-Auswertungen gehören in Level 3 oder in eine eigene Diagnostics-Detailansicht.

## 3.9 Governance and Engineering Details

Standardmäßig eingeklappt.

Enthält:

- current state snapshot
- PR references
- manifest verification
- owner paths
- F1–F5 details
- provenance
- debug internals
- raw reason codes
- contract fields
- source metadata
- test references

Dieser Bereich darf umfangreich sein, aber nicht die Hauptoberfläche dominieren.

Verbindliche Regeln:

```text
GOVERNANCE_DEFAULT_COLLAPSED=true
GOVERNANCE_STATE_NOT_PERSISTED_ACROSS_DEMO_SESSION=true
RAW_JSON_NOT_RENDERED_BY_DEFAULT=true
COPY_EVIDENCE_ACTION_ALLOWED=true
```

Ein negativer Gate-Status darf Governance Details nicht automatisch öffnen.

---

# 4. Visual Design System

## 4.1 Gestaltungsziel

```text
VISUAL_STYLE=PROFESSIONAL_DARK_TRADING_TERMINAL
VISUAL_TONE=CALM,PRECISE,PREMIUM,TECHNICAL
DENSITY=HIGH_BUT_READABLE
```

Die Oberfläche soll modern, hochwertig und glaubwürdig wirken.

Sie darf nicht wirken wie:

- ein internes Admin-Panel,
- ein Test Harness,
- eine HTML-Debug-Ausgabe,
- ein unvollständiges Dashboard,
- ein Kartenfriedhof.

## 4.2 Verbindliche Design Tokens

Die konkrete Wertbelegung erfolgt repo-gebunden in Phase 1. Die Token-Namen und ihre zentrale Eigentümerschaft sind jedoch verpflichtend:

```text
CONTENT_MAX_WIDTH
PAGE_PADDING
GRID_GAP
CARD_PADDING
CARD_RADIUS
CARD_BORDER
HEADER_HEIGHT

FONT_FAMILY
MONO_FONT
FONT_SIZE_XS
FONT_SIZE_SM
FONT_SIZE_MD
FONT_SIZE_LG
FONT_SIZE_XL
LINE_HEIGHT

COLOR_BACKGROUND
COLOR_SURFACE_1
COLOR_SURFACE_2
COLOR_BORDER
COLOR_TEXT_PRIMARY
COLOR_TEXT_SECONDARY
COLOR_POSITIVE
COLOR_NEGATIVE
COLOR_WARNING
COLOR_INFO
COLOR_MODEL
COLOR_MUTED
```

Zusätzlich:

```text
NO_GRADIENT_OVERUSE=true
NO_GLOW_OVERUSE=true
NO_GLASSMORPHISM_BY_DEFAULT=true
NO_DUPLICATE_INLINE_DESIGN_TOKENS=true
```

Verbindliche Ausgangsskalen, sofern Phase 1B keine repo-gebundene begründete Abweichung ratifiziert:

```text
SPACING_SCALE_PX=4,8,12,16,24,32,48
CARD_RADIUS_PX=10
PRIMARY_CARD_MIN_HEIGHT_PX=280
SECONDARY_CARD_MIN_HEIGHT_PX=160
HEADER_TARGET_HEIGHT_PX=56
TABLE_ROW_HEIGHT_PX=44
ICON_SIZE_PX=14,16,20
BREAKPOINT_NARROW_DESKTOP_PX=1280
BREAKPOINT_REFERENCE_DESKTOP_PX=1440
BREAKPOINT_WIDE_DESKTOP_PX=1728
NUMBER_ALIGNMENT=TABULAR_OR_MONOSPACED
```

## 4.3 Layout

Pflicht:

- 12-column responsive grid oder funktional äquivalentes System
- konsistente Abstände
- definierte Content Max Width
- klare vertikale Rhythmik
- keine überbreiten Textzeilen
- keine extreme Leerräume
- keine schmalen Kartenkolonnen neben riesigen Leerflächen
- keine abgeschnittenen Inhalte
- keine horizontalen Scrollbalken im Hauptlayout

## 4.4 Card Hierarchy

Drei Kartenebenen:

```text
PRIMARY_CARD
SECONDARY_CARD
DETAIL_CARD
```

Primary Cards:
- Chart
- Ranking
- Decision Chain
- Economic
- Risk

Secondary Cards:
- regime
- contributions
- block reasons
- selected instrument details

Detail Cards:
- provenance
- raw diagnostics
- contracts
- manifests

## 4.5 Farbsemantik

Farben müssen semantisch konsistent sein:

- Grün: positive / pass / fresh / processed
- Rot: fail / blocked / negative
- Gelb: warning / partial / stale risk
- Blau: informational / neutral
- Violett: ranking / model / AI
- Grau: unavailable / inactive / not run

Farben dürfen nie alleinige Informationsträger sein. Text oder Icons sind zusätzlich erforderlich.

## 4.6 Typografie

Pflicht:

- klare Hierarchie
- Zahlen monospaced, wo sinnvoll
- Labels kleiner als Werte
- keine unlesbaren Mini-Texte
- keine übermäßig dichten Statuszeilen
- konsistente Groß-/Kleinschreibung

## 4.7 Charts

Pflicht:

- gut lesbare Achsen
- Tooltips
- Legenden nur, wenn hilfreich
- ausreichender Kontrast
- kein dekorativer Chart ohne Aussage
- keine Chart-Fläche ohne Daten
- keine falsche Präzision

---

# 5. Verbindlicher Interaktionsfluss

Ein Nutzer klickt ein Instrument im Ranking an.

Danach müssen synchron aktualisiert werden:

```text
selected instrument
market chart
market regime
bull assessment
bear assessment
survival
suitability
double play
block reasons
risk context
economic context
source and freshness
```

Der Nutzer darf nicht das Gefühl haben, dass verschiedene Dashboard-Bereiche voneinander unabhängig oder nur dekorativ sind.

Verbindlicher Selection-Context-Vertrag:

```text
SELECTION_CONTEXT_ID_REQUIRED=true
ALL_SURFACES_SHARE_SELECTION_CONTEXT=true
PARTIAL_CONTEXT_COMMIT_FORBIDDEN=true
STALE_SELECTION_RESPONSE_DISCARDED=true
URL_DEEP_LINK_REQUIRED=true
BROWSER_BACK_FORWARD_SUPPORTED=true
```

Chart, Regime, Decision Chain, Risk, Economic, Freshness und Provenance dürfen zu keinem Zeitpunkt unterschiedliche Instrumente oder Snapshot-Identitäten als gemeinsamen aktuellen Zustand präsentieren.

---

# 6. Daten- und Provenance-Vertrag

Jeder dargestellte Datenblock benötigt:

```text
source_id
source_type
snapshot_id
schema_version
producer_version
content_digest
selection_context_id
evidence_generated_at
bundle_created_at
dashboard_rendered_at
data_start
data_end
freshness_state
quality_state
record_count
instrument_scope
timeframe
manifest_ref_if_available
```

Zulässige Freshness States:

```text
FRESH
AGING
STALE
UNKNOWN
```

Zulässige Quality States:

```text
READY
PARTIAL
INCOMPLETE
INVALID
MISSING
```

Dashboard-Daten dürfen nur aus folgenden Klassen stammen:

```text
MANIFEST_VERIFIED_OFFLINE_EVIDENCE
CANONICAL_REPO_SNAPSHOT
CANONICAL_LOCAL_READ_ONLY_BUNDLE
DETERMINISTIC_DERIVATION_FROM_CANONICAL_SOURCE
```

Zeitsemantik:

```text
evidence_generated_at=ZEITPUNKT_DER_FACHLICHEN_EVIDENCE
bundle_created_at=ZEITPUNKT_DER_READ_ONLY_BUNDLE_ERZEUGUNG
dashboard_rendered_at=ZEITPUNKT_DER_UI_DARSTELLUNG
```

Diese Zeitpunkte dürfen nicht stillschweigend gleichgesetzt werden.

Nicht zulässig:

```text
UNLABELED_FIXTURE
RANDOM_DATA
SYNTHETIC_MARKET_SERIES
SPOT_FALLBACK
UNVERIFIED_EXTERNAL_JSON
REQUEST_TIME_PROVIDER_CALL
```

---

# 7. Umsetzung in Phasen


## 7.0 Verbindliche Slice- und PR-Bindings

Jede Phase ist ein Bauabschnitt mit eigener Owner-, Datei-, Test-, Screenshot- und Stop-Grenze. Die folgende Matrix ist verbindlich; konkrete Dateilisten dürfen nach aktueller Repo-Prüfung enger, aber nicht stillschweigend breiter werden.

| Slice | Ziel | Kandidaten-Owner / Dateien | Pflicht-Tests | Pflicht-Screenshots | Verboten |
|---|---|---|---|---|---|
| Phase -1 | Discovery aktualisieren | Discovery docs/evidence only | traceability completeness | baseline viewports | produktive Mutation |
| Phase 0 | Inventar durabel binden | evidence/docs + test fixtures | artifact schema/digest | current full page | UI-Semantik ändern |
| Phase 1A | Compact Header + Chart above fold | `market_v0.html`, operator header, hero, chart partial | geometry, duplicate status, no semantic changes | 1440×900 header/hero/chart | Datenproducer ändern |
| Phase 1B | Tokens, Grid, vendorized assets | central CSS/token owner, `base.html`, asset bundle | token uniqueness, network allowlist, responsive grid | desktop/narrow/wide | neue Produktfeatures |
| Phase 2 | Operator Overview | hero/context display adapters | decision sentence, priority/content tests | overview states | Interpretation erfinden |
| Phase 3 | Chart Polish | primary chart partial + narrow context adapter | real-data, gaps, tooltip metadata, stale overlay | chart fresh/stale/missing | synthetische Bars |
| Phase 4A | Ranking Data Contract | ranking runtime/readmodel | stable sort, tie-break, sparse-field policy | data-state samples | fehlende Felder erfinden |
| Phase 4B | Ranking Visual Surface | canonical ranking partial | overflow, Top20/50, selection marker | Top20/Top50/narrow | zweite Ranking-Komponente |
| Phase 4C | Selection Context Binding | `market_surface.py`, display contexts | atomic context, URL state, back/forward | symbol switch | partial update |
| Phase 5A | Activity State Contract | decision display contracts | no bare ACTIVE, evidence-required PROCESSED | all states | counts/stages fabrizieren |
| Phase 5B | Funnel Visual Alignment | funnel partial/context | canonical stage order, scope markers | funnel/block states | Instrument-Scope vortäuschen |
| Phase 6 | Risk/Safety Compact | safety context + partial | state taxonomy, authority ambiguity | no-position/missing/stale | Authority verändern |
| Phase 7 | Economic Visuals | economic display + partial | scope compatibility, negative/zero preservation | fail/zero/missing curves | Profitabilität behaupten |
| Phase 8 | Linear Diagnostics | diagnostics display + partial | summary/detail separation | summary + expanded details | große leere Karten |
| Phase 9 | Governance Consolidation | current state/details/drawers | collapsed default, no raw JSON default | collapsed/expanded | Hauptfluss dominieren |
| Phase 10 | Demo Readiness | browser test infra/evidence | visual regression, console, network, accessibility | complete matrix | Merge bei offenen Blockern |

Jeder Slice endet mit:

```text
STATUS=<PASS|FAIL>
VERDICT=<SLICE_SPECIFIC_VERDICT>
GO_TOKEN=<SLICE_SPECIFIC_GO_TOKEN>
HEAD_BEFORE=<sha>
HEAD_AFTER=<sha>
ORIGIN_MAIN=<sha>
WORKTREE_CLEAN=true
FOCUSED_TESTS_PASS=true
BROWSER_EVIDENCE_COMPLETE=true
VISUAL_EVIDENCE_COMPLETE=true
SOURCE_PROVENANCE_VERIFIED=true
TRADING_SEMANTICS_EFFECT=NONE
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
STOP_BEFORE_MERGE=true
```


## PHASE -1 — Implementation Discovery and Feasibility Binding

Ziel:

- reale Dashboard-Route und Render Chain identifizieren,
- Templates, CSS, JavaScript und Komponenten-Owner erfassen,
- verfügbare Datenowner und Evidence-Verträge bestimmen,
- Browser-, Screenshot- und Test-Infrastruktur prüfen,
- jede Runbook-Anforderung auf konkrete Pfade, Symbole, Tests und PR-Grenzen abbilden.

Pflichtartefakte:

```text
implementation_discovery_report.md
dashboard_requirement_traceability_matrix.json
dashboard_phase_binding_matrix.json
recommended_runbook_patch_list.md
dashboard_component_inventory.json
data_owner_inventory.json
layout_defect_inventory.json
source_binding_matrix.json
visual_gap_assessment.md
```

Exit-Kriterium:

```text
CANONICAL_RENDER_CHAIN_IDENTIFIED=true
ALL_PRIMARY_OWNERS_IDENTIFIED=true
ALL_REQUIREMENTS_TRACEABLE=true
PHASE_FILE_BINDINGS_DEFINED=true
PHASE_TEST_BINDINGS_DEFINED=true
IMPLEMENTATION_READY_OR_EXPLICITLY_BLOCKED=true
```

Keine produktive UI-Mutation ist in Phase -1 zulässig.

## PHASE 0 — Baseline Audit

Ziel:

- aktuellen Stand vollständig inventarisieren,
- Layout-Defekte dokumentieren,
- Datenquellen und leere Flächen auflösen,
- bestehende Komponenten bewerten.

Pflichtartefakte:

```text
dashboard_component_inventory.json
data_owner_inventory.json
layout_defect_inventory.json
visual_gap_assessment.md
source_binding_matrix.json
```

Exit-Kriterium:

```text
ALL_PRIMARY_SURFACES_CLASSIFIED=true
ALL_DATA_OWNERS_CLASSIFIED=true
ALL_LAYOUT_DEFECTS_DOCUMENTED=true
```

## PHASE 1 — Design System and Layout Foundation

Ziel:

- stabiles Grid,
- responsive container,
- Card Hierarchy,
- typography,
- color semantics,
- spacing,
- empty states,
- loading states,
- error states.

Keine neuen Produktfeatures vor stabilem Layout.

Exit-Kriterium:

```text
NO_MAJOR_LAYOUT_BREAKS=true
NO_LARGE_UNEXPLAINED_EMPTY_SPACE=true
NO_HORIZONTAL_OVERFLOW=true
PRIMARY_CARD_SYSTEM_BOUND=true
```

## PHASE 2 — Operator Overview

Ziel:

- Hero Area,
- selected instrument,
- market regime,
- current decision,
- critical system state.

Exit-Kriterium:

```text
FIVE_SECOND_OPERATOR_SUMMARY_PASS=true
```

## PHASE 3 — Market Chart

Ziel:

- echte Candles,
- volume,
- tooltip,
- source,
- freshness,
- selected instrument binding.

Exit-Kriterium:

```text
CANDLE_CHART_REAL_DATA=true
CHART_SELECTED_INSTRUMENT_SYNC=true
NO_EMPTY_CHART_WHEN_DATA_EXISTS=true
```

## PHASE 4 — Ranking

Ziel:

- Top 20,
- Top 50,
- sorting,
- filtering,
- instrument selection,
- visual score indicators.

Exit-Kriterium:

```text
TOP20_REAL=true
TOP50_REAL=true
TOP20_TOP50_DISTINCT=true
RANKING_INTERACTION_PASS=true
```

## PHASE 5 — AI / Decision Chain

Ziel:

- funnel,
- bull/bear,
- survival,
- suitability,
- double play,
- block reasons,
- activity states.

Exit-Kriterium:

```text
AI_ACTIVE_LABEL_REMOVED_OR_REPLACED=true
ACTIVITY_STATE_CONTRACT_BOUND=true
DECISION_CHAIN_VISUAL_COMPLETE=true
```

## PHASE 6 — Risk / Safety

Ziel:

- verständliche risk surface,
- kompakte missing states,
- no authority ambiguity.

Exit-Kriterium:

```text
RISK_SURFACE_OPERATOR_READABLE=true
SAFETY_STATUS_UNAMBIGUOUS=true
```

## PHASE 7 — Economic Observability

Ziel:

- metrics,
- curves,
- cost attribution,
- negative evidence visibility.

Exit-Kriterium:

```text
ECONOMIC_EVIDENCE_VISUALIZED=true
NO_PROFITABILITY_OVERCLAIM=true
```

## PHASE 8 — AI / Linear Diagnostics

Ziel:

- Contributions,
- factor exposure,
- drift,
- sensitivity,
- orthogonality.

Exit-Kriterium:

```text
AI_DIAGNOSTIC_VISUALS_BOUND_OR_EXPLICITLY_MISSING=true
```

## PHASE 9 — Governance Consolidation

Ziel:

- alle technischen Details standardmäßig einklappen,
- keine Governance-Dominanz im Hauptfluss.

Exit-Kriterium:

```text
PRIMARY_VIEW_OPERATOR_FIRST=true
ENGINEERING_DETAILS_SECONDARY=true
```

## PHASE 10 — Final UX and Demo Readiness

Ziel:

- Google Chrome (Playwright `channel="chrome"`) als primäre Browser-Abnahme,
- Safari / WebKit nur als sekundärer Kompatibilitätscheck,
- responsive,
- no console errors,
- no clipped content,
- no empty areas,
- no embarrassing unfinished surfaces.

Exit-Kriterium:

```text
DEMO_READY=true
EXTERNAL_VIEWER_READY=true
```

---

# Browser Verification Policy

Ab dieser Klarstellung gilt für Entwicklung, visuelle Abnahme, Screenshots und automatisierte Evidence des Visual Operator Dashboards verbindlich:

```text
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_BROWSER_AUTOMATION=PLAYWRIGHT
PRIMARY_PLAYWRIGHT_CHANNEL=chrome
PRIMARY_BROWSER_SCREENSHOTS=CHROME
PRIMARY_DOM_ASSERTIONS=CHROME
PRIMARY_CONSOLE_ASSERTIONS=CHROME
PRIMARY_NETWORK_ASSERTIONS=CHROME
PRIMARY_INTERACTION_ASSERTIONS=CHROME

CHROMIUM_FALLBACK_ALLOWED=true
CHROMIUM_FALLBACK_MUST_BE_REPORTED=true
PLAYWRIGHT_CHROMIUM_IS_NOT_REAL_CHROME=true

WEBKIT_VERIFICATION=SECONDARY
REAL_SAFARI_VERIFICATION=SECONDARY
SAFARI_REQUIRED_FOR_NORMAL_SLICE_MERGE=false
SAFARI_FAILURE_BLOCKS_NORMAL_SLICE=false
WEBKIT_IS_NOT_REAL_SAFARI=true
SAFARI_ROLE=SECONDARY_COMPATIBILITY_CHECK
WEBKIT_ROLE=SECONDARY_ENGINE_COMPATIBILITY_CHECK

PRIMARY_BROWSER_EVIDENCE=PLAYWRIGHT_REAL_CHROME
PRIMARY_INTERACTIVE_REVIEW=REAL_CHROME
POST_SLICE_INTERACTIVE_OPEN=REAL_CHROME
```

### Playwright Channel

Playwright muss, sofern lokal Google Chrome installiert ist, den installierten Chrome-Channel verwenden:

```text
channel="chrome"
```

Das gebündelte Chromium ist nur Fallback. Wenn Chromium statt `channel="chrome"` genutzt wird, muss die Evidence `CHROMIUM_FALLBACK_USED=true` ausweisen.

### Safari / WebKit

Safari und WebKit sind ausschließlich sekundäre Kompatibilitätschecks.

- `SAFARI_REQUIRED_FOR_NORMAL_SLICE_MERGE=false`
- `SAFARI_FAILURE_BLOCKS_NORMAL_SLICE=false`
- Ein Safari-/WebKit-Fail blockiert einen normalen Slice-Merge nicht, solange Chrome/Playwright vollständig PASS ist und kein explizit Safari-spezifischer Release-Gate angeordnet wurde.
- Ein bestandener WebKit-Lauf darf nicht als realer Safari-Nachweis und nicht als Ersatz für Chrome-Primary-Evidence bezeichnet werden.

### Interaktive Review

Nach erfolgreichen Slice-Läufen ist das Dashboard für die interaktive visuelle Review sichtbar in Google Chrome zu öffnen (`PRIMARY_INTERACTIVE_REVIEW=REAL_CHROME`). Safari ist dafür nicht der Primärpfad.

### Pflicht-Reporting (getrennt)

```text
CHROME_PLAYWRIGHT_VERIFIED=<true|false>
CHROMIUM_FALLBACK_USED=<true|false>
WEBKIT_AUTOMATION_VERIFIED=<true|false>
REAL_SAFARI_VERIFIED=<true|false>
```

`REAL_SAFARI_VERIFIED` und `WEBKIT_AUTOMATION_VERIFIED` sind Reporting-Felder, keine normalen Slice-Merge-Blocker.

---

# 8. Pflicht-Testmatrix

## 8.1 Data Truth

- real OHLCV only
- no fake bars
- no spot fallback
- no synthetic fallback
- Bitcoin excluded
- freshness correct
- provenance correct
- stale state correct
- missing source correct

## 8.2 Layout

- desktop Google Chrome (Playwright `channel="chrome"`; primary)
- Chromium fallback only when Chrome channel unavailable (must be reported)
- desktop Safari / WebKit (secondary compatibility only; not a normal merge blocker)
- common laptop width
- wide desktop
- no horizontal overflow
- no clipped cards
- no giant empty regions
- no broken two-column grids
- no cards narrower than minimum readable width

## 8.3 Ranking

- Top 20 count
- Top 50 count
- distinct views
- selected instrument binding
- sorting
- filtering
- rank delta
- score visualization

## 8.4 Decision Chain

- every stage has valid state
- `PROCESSED` requires evidence
- `AVAILABLE_NOT_RUN` distinct
- `BLOCKED` reason visible
- funnel stage counts consistent
- bull/bear values consistent
- decision state consistent

## 8.5 Economic

- negative values remain negative
- zero trades remain zero
- costs not hidden
- gross/net distinction correct
- no positive claim from missing evidence

## 8.6 Safety

- no live
- no orders
- no authority
- no runtime start
- no scheduler
- no credentials
- no network calls
- no action controls

## 8.7 Browser, DOM and Visual Regression

Primär gemäß `# Browser Verification Policy`:

- Google Chrome via Playwright (`channel="chrome"`) für Screenshots, DOM-, Console-, Network- und Interaction-Assertions
- visual regression baseline (Chrome)
- DOM overflow assertions (Chrome)
- console error assertions (Chrome)
- failed asset assertions (Chrome)
- unexpected network request assertions (Chrome)
- selection-context consistency assertions
- stale response discard assertions
- Chromium fallback allowed only when Chrome channel unavailable; must be reported
- WebKit verification secondary only
- real Safari verification secondary only; not required for normal slice merge
- WebKit result not presented as equivalent to real Safari and not as Chrome-primary substitute

## 8.8 Accessibility

- keyboard focus
- meaningful labels
- sufficient contrast
- color not sole carrier
- readable font sizes
- tooltips or accessible alternatives

---

# 9. Visual Acceptance Criteria

Ein Slice darf nur als visuell erfolgreich gelten, wenn:

```text
NO_BROKEN_LAYOUT=true
NO_GIANT_EMPTY_SPACE=true
NO_DEBUG_CONSOLE_APPEARANCE=true
NO_BADGE_WALL_AS_PRIMARY_UI=true
NO_RAW_MISSING_FIELD_DUMP_AS_PRIMARY_UI=true
NO_UNLABELED_DATA=true
NO_FAKE_DATA=true
NO_CLIPPED_CONTENT=true
NO_HORIZONTAL_MAIN_SCROLL=true
NO_PARTIAL_SELECTION_CONTEXT=true
NO_UNEXPECTED_BROWSER_NETWORK_REQUEST=true
NO_DUPLICATE_DESIGN_TOKEN_OWNER=true
```

Zusätzlich:

```text
PRIMARY_QUESTIONS_ANSWERED_WITHIN_5_SECONDS=true
SELECTED_INSTRUMENT_FLOW_COHERENT=true
AI_PROCESSING_VISUALLY_EXPLAINED=true
BLOCK_REASON_VISIBLE=true
RISK_VISIBLE=true
ECONOMIC_STATE_VISIBLE=true
FRESHNESS_VISIBLE=true
```

---


# 9A. Fünf-Sekunden-Demo-Test

Der Demo-Test wird von mindestens einer Person durchgeführt, die die konkrete Implementierung nicht erstellt hat. Nach fünf Sekunden Betrachtung des 1440×900 Operator Overview muss sie ohne technische Detailansicht beantworten können:

| Frage | Muss erkennbar sein |
|---|---|
| Welches Instrument ist ausgewählt? | Symbol + Markt-/Contract-Kontext |
| Was macht der Markt? | Chart + kompakter Regime-Zustand |
| Was sieht das System? | Decision State + Bull/Bear/Context |
| Was blockiert? | primärer Blocker + Pipeline-Gruppe |
| Wie frisch sind die Daten? | Freshness + Snapshot-Zeit |
| Wie steht Risk/Safety? | kompakter, eindeutiger Zustand |
| Wie steht Economic Validity? | Gate + Scope + Evidence-Zustand |
| Darf gehandelt werden? | klar: nein; keine Authority/Orders/Live |

```text
FIVE_SECOND_DEMO_TEST_PASS=true
TECHNICAL_EXPLANATION_REQUIRED_FOR_BASIC_STATE=false
AMBIGUOUS_SCOPE_COUNT=0
MISLEADING_STATUS_COUNT=0
```


# 10. Screenshot-basierte Abnahme

Jeder PR mit visuellen Änderungen muss Screenshots erzeugen:

1. Full page desktop.
2. Header + operator overview.
3. Chart.
4. Top 20.
5. Top 50.
6. Selected instrument interaction.
7. Decision funnel.
8. Bull/Bear view.
9. Risk/Safety.
10. Economic view.
11. AI diagnostics.
12. Governance collapsed.
13. Governance expanded.
14. Missing-source state.
15. Stale-data state.
16. narrow desktop viewport.

Screenshots sind Bestandteil der PR-Evidence und werden primär mit Google Chrome (Playwright `channel="chrome"`) erzeugt. Safari-Screenshots sind optionaler sekundärer Kompatibilitätsnachweis, keine generelle PR-Pflicht für normale Slices.

Browser-Abnahme muss unterscheiden:

```text
CHROME_PLAYWRIGHT_VERIFIED=<true|false>
CHROMIUM_FALLBACK_USED=<true|false>
WEBKIT_AUTOMATION_VERIFIED=<true|false>
REAL_SAFARI_VERIFIED=<true|false>
```

Ein bestandener WebKit-Lauf darf nicht als vollständiger realer Safari-Nachweis und nicht als Ersatz für Chrome-Primary-Evidence bezeichnet werden.
`REAL_SAFARI_VERIFIED=false` ist für normale Slice-Merges zulässig, solange Chrome/Playwright PASS ist.

---

# 11. PR- und Merge-Regeln

Jeder Slice:

```text
ONE_BOUNDED_PR=true
STOP_BEFORE_MERGE=true
FOCUSED_TESTS_REQUIRED=true
VISUAL_SCREENSHOTS_REQUIRED=true
SOURCE_MANIFEST_VERIFY_REQUIRED=true
IMPLEMENTATION_MANIFEST_REQUIRED=true
```

Kein Merge bei:

```text
BROKEN_LAYOUT
UNRESOLVED_DATA_PROVENANCE
FAKE_DATA
UNEXPECTED_SPOT_FALLBACK
BITCOIN_PRESENT
AI_ACTIVE_WITHOUT_PROCESSING_EVIDENCE
LARGE_EMPTY_LAYOUT_REGION
HORIZONTAL_OVERFLOW
CONSOLE_ERRORS
LIVE_OR_ORDER_AUTHORITY_CHANGE
PARTIAL_SELECTION_CONTEXT
UNEXPECTED_BROWSER_NETWORK_REQUEST
UNBOUND_DESIGN_TOKEN_DUPLICATION
```

---

# 12. Definition of Done

Das Produkt ist abgeschlossen, wenn:

```text
OPERATOR_OVERVIEW_COMPLETE=true
CANDLE_CHART_COMPLETE=true
TOP20_COMPLETE=true
TOP50_COMPLETE=true
INSTRUMENT_SELECTION_COMPLETE=true
MARKET_REGIME_COMPLETE=true
AI_DECISION_CHAIN_COMPLETE=true
BULL_BEAR_COMPLETE=true
SURVIVAL_COMPLETE=true
SUITABILITY_COMPLETE=true
DOUBLE_PLAY_COMPLETE=true
BLOCK_REASON_VISUALS_COMPLETE=true
RISK_SAFETY_COMPLETE=true
ECONOMIC_OBSERVABILITY_COMPLETE=true
AI_LINEAR_DIAGNOSTICS_COMPLETE_OR_EXPLICITLY_NOT_AVAILABLE=true
GOVERNANCE_SECONDARY=true
RESPONSIVE_PASS=true
CHROME_PASS=true
CHROME_PLAYWRIGHT_VERIFIED=true
SAFARI_PASS=OPTIONAL_SECONDARY_OR_EXPLICIT_RELEASE_GATE
CONSOLE_CLEAN=true
SCREENSHOT_REVIEW_PASS=true
VISUAL_REGRESSION_PASS=true
DOM_OVERFLOW_ASSERTIONS_PASS=true
SELECTION_CONTEXT_ATOMIC=true
SNAPSHOT_IDENTITY_COHERENT=true
UNEXPECTED_NETWORK_REQUESTS_ZERO=true
WEBKIT_VERIFIED=OPTIONAL_SECONDARY
REAL_SAFARI_VERIFIED=OPTIONAL_SECONDARY
DEMO_READY=true
```

Zusätzlich:

```text
TRADING_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
EXECUTION_SEMANTICS_CHANGED=false
PROMOTION_GATE_CHANGED=false
ECONOMIC_GATE_CHANGED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
```

---

# 13. Cursor Master Instruction

```text
GO_PEAK_TRADE_VISUAL_OPERATOR_DASHBOARD_PRODUCT_V1_3

Implementiere dieses Runbook strikt phasenweise.

Arbeitsregeln:

1. Vor jeder Mutation origin/main, HEAD, Worktree und relevante Source-Evidence verifizieren.
2. Keine Phase überspringen.
3. Keine neue Visualisierung ohne geklärte Datenquelle.
4. Keine Fake-, Demo-, Random-, Spot- oder Synthetic-Fallback-Daten.
5. Keine Live-, Order-, Runtime-, Scheduler-, Credential- oder Authority-Wirkung.
6. Reuse-first.
7. Pro Phase genau ein bounded PR.
8. Jeder PR benötigt:
   - Focused Tests,
   - Browser Render Verification via Google Chrome / Playwright (`channel="chrome"`),
   - Chrome Screenshots (primär),
   - Layout Checks,
   - Console Error Check,
   - Source Provenance Proof,
   - MANIFEST.sha256.
   Safari-Screenshots sind optionaler sekundärer Kompatibilitätsnachweis und keine normale Slice-Merge-Pflicht.
9. Stoppe vor jedem Merge.
10. Kein PR gilt als erfolgreich, wenn nur zusätzliche Karten, Badges oder Rohtext ergänzt wurden.
11. Primärziel ist visuelle Verdichtung und Operator-Verständlichkeit.
12. Engineering- und Governance-Details bleiben sekundär und einklappbar.
13. Ein grünes ACTIVE ist ohne Processing Evidence verboten.
14. Große Leerflächen, gebrochene Grids, abgeschnittene Karten und horizontale Überläufe sind Merge-Blocker.
15. Nach jeder Phase Screenshot-Abnahme gegen dieses Runbook (Chrome primary).
16. Phase -1 ist vor jeder produktiven Dashboard-Mutation verpflichtend.
17. Jede Phase benötigt konkrete Owner-, Datei-, Test- und Screenshot-Bindings.
18. Selection Context und Snapshot Identity müssen über alle synchronen Oberflächen atomar konsistent sein.
19. Chrome/Playwright ist primär; WebKit und echter Safari sind sekundär und getrennt zu berichten. Safari-/WebKit-Fails blockieren normale Slices nicht, sofern Chrome PASS ist und kein expliziter Safari-Release-Gate gilt.
20. Unerwartete Browser-Netzwerkzugriffe sind Merge-Blocker.
20a. Nach erfolgreichen Slice-Läufen ist das Dashboard sichtbar in Google Chrome zu öffnen (`POST_SLICE_INTERACTIVE_OPEN=REAL_CHROME`).
21. Risk-Zustände `NOT_APPLICABLE`, `MISSING`, `STALE` und `INVALID` dürfen nicht visuell oder semantisch vermischt werden.
22. Economic Evidence muss ihren Scope und ihre Kompatibilität mit dem ausgewählten Instrument sichtbar ausweisen.
23. Design-Tokens müssen zentral gebunden sein; divergierende Inline-Token sind nicht zulässig.
24. Die kanonische Render Chain und die Owner-Matrix dieses Runbooks sind vor jedem Slice gegen den aktuellen Repo-Stand zu verifizieren.
25. Discovery-Defects D1–D10 dürfen nur mit Tests und Screenshot-Evidence geschlossen werden.
26. Fleet-, Portfolio-, Strategy-Family- oder Baseline-Evidence muss sichtbar als nicht instrument-scoped markiert werden.
27. Der Chart muss im Referenzviewport 1440×900 materiell sichtbar sein; bloßes Vorhandensein im DOM reicht nicht.
28. Ranking-Spalten ohne belastbaren Producer werden verborgen, sekundär dargestellt oder explizit als data-blocked behandelt; `unavailable` darf nicht dominieren.
29. Tailwind- und Chart.js-CDNs sind aus dem Target-State zu entfernen oder lokal zu vendorisieren; Browser-Netzwerk-Allowlist ist self-only.
30. Nach Abschluss jedes Slices ist die Requirement-Traceability-Matrix zu aktualisieren.
31. Das Dashboard ist ausschließlich Consumer des kanonischen Core-Systems.
32. Dashboard-Code darf keine Trading-, Risk-, Economic-, Authority- oder Decision-Semantik besitzen.
33. Existiert bereits ein kanonischer Core-Owner, ist dessen Output zu verwenden; Reimplementierungen sind unzulässig.
34. Jeder neue Dashboard-Kontext muss auf einen bestehenden Core-Owner oder einen dokumentierten Adapter zurückführbar sein.
35. Das Dashboard darf niemals eine zweite fachliche Wahrheit erzeugen.
```

---

# 14. Abschlussgrundsatz

Das Peak Trade Dashboard ist kein Repository-Statusbericht im Browser.

Es ist die visuelle Operator-Schnittstelle des Systems.

Es muss zeigen:

```text
what the market is doing
what the system sees
why the system sees it
what is blocking action
how trustworthy the data is
how risk and economic validity currently stand
```

Alles andere ist sekundär.

