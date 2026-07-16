# Peak Trade --- Visual Operator Dashboard Product Runbook v1.3

## Zweck

Dieses Runbook definiert die verbindliche Produkt-, UX-,
Visualisierungs-, Daten-, Safety-, Qualitäts- und Umsetzungsstruktur für
das **Peak Trade Visual Operator Dashboard**.

Das Ziel ist kein technisches Debug-Panel und keine Ansammlung von
Statuskarten, sondern ein hochwertiges, professionelles, read-only
Market-, AI-, Risk- und Observability-Produkt, das visuell mit modernen
Crypto- und Trading-Plattformen vergleichbar ist.

Das Dashboard muss auch gegenüber technisch versierten externen
Betrachtern präsentabel sein. Es soll unmittelbar verständlich, visuell
konsistent, glaubwürdig, schnell erfassbar und ohne peinliche Leerräume,
abgeschnittene Komponenten, unverständliche Statuswände oder halb
fertige Diagnosekarten nutzbar sein.

------------------------------------------------------------------------

# 0. Verbindlicher Zielzustand

``` text
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

Der Zielzustand ist erreicht, wenn ein Nutzer innerhalb von fünf
Sekunden erkennen kann:

1.  Welcher Futures-Markt aktuell relevant ist.
2.  Welche Instrumente im Ranking vorne liegen.
3.  Welche Marktstruktur und welches Regime vorliegen.
4.  Was Bull- und Bear-Layer aktuell sehen.
5.  Welche AI-/Decision-Komponenten aktiv Daten verarbeitet haben.
6.  Welche Stufe eine Aktion blockiert.
7.  Wie frisch, vollständig und belastbar die Daten sind.
8.  Wie Risiko, Economic Validity und Authority aktuell stehen.
9.  Dass keine Live-, Order- oder Runtime-Autorisierung besteht.
10. Dass das Dashboard professionell, stabil und vorzeigbar ist.

Zusätzlich muss der Operator Overview eine einzelne, natürlich lesbare
Entscheidungsaussage erzeugen, die mindestens Instrument, Regime,
Decision State und primären Blocker zusammenfasst.

Beispielstruktur:

``` text
<INSTRUMENT> steht auf Rang <N>. Regime <STATE>. Decision <STATE>. Primärer Blocker: <REASON>.
```

Die Aussage darf keine unbelegte Interpretation, keine
Profitabilitätsbehauptung und keine Autorisierungswirkung enthalten.

------------------------------------------------------------------------

# 0A. Dashboard Authority Model

Dieses Runbook definiert ausschließlich die Präsentationsschicht des
Dashboards. Es ersetzt, erweitert oder überschreibt niemals die
fachliche Wahrheit des Peak_Trade-Core-Systems.

``` text
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
```

Architekturgrundsatz:

-   Das Core-System bleibt die einzige fachliche Wahrheit.
-   Das Dashboard ist ausschließlich Consumer.
-   Jeder dargestellte Wert muss auf einen kanonischen Core-Owner oder
    einen dokumentierten Adapter zurückführbar sein.
-   Adapter dürfen Daten transformieren oder visualisieren, jedoch keine
    fachliche Logik, Entscheidungen oder Authority erzeugen.
-   Existiert bereits ein kanonischer Owner, darf keine zweite
    Implementierung im Dashboard entstehen.

------------------------------------------------------------------------

# 0A. Kanonische Implementation Baseline

Diese Baseline bindet das Runbook an die reale, read-only geprüfte
Dashboard-Architektur. Sie ist Ausgangspunkt für jede Umsetzung. Bei
Abweichungen zwischen Annahme und Repository-Realität gilt: zuerst
Discovery aktualisieren, dann Runbook patchen, erst danach mutieren.

``` text
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
REAL_SAFARI_BASELINE=OPTIONAL_SECONDARY_MANUAL_CHECK
```

Die Commit- und PR-Angaben sind Discovery-Evidence, keine dauerhafte
Freigabe für weitere Arbeiten. Vor jeder Mutation sind `origin/main`,
aktueller `HEAD`, PR-Zustand und Worktree erneut zu prüfen.

## 0A.1 Kanonische Render Chain

``` text
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
Full SSR HTML in Google Chrome via Playwright; Chromium fallback allowed; Safari/WebKit secondary only
```

Verbindlich:

``` text
RESOLVE_MARKET_REQUEST_STATE_EXISTS=false
CANONICAL_REQUEST_RESOLVER=resolve_market_page_data
NO_SECOND_RENDER_CHAIN_ALLOWED=true
NO_PARALLEL_DASHBOARD_TRUTH_ALLOWED=true
```

# 0B. Verbindlicher Visual Blueprint

## 0B.1 Above-the-fold Blueprint --- 1440×900

``` text
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

``` text
ROW_2=RANKING_PRIMARY + DECISION_SUMMARY
ROW_3=DECISION_CHAIN + RISK_SAFETY
ROW_4=ECONOMIC + DIAGNOSTIC_SUMMARY
ROW_5=COLLAPSED_GOVERNANCE_AND_ENGINEERING_DETAILS
```

Abnahmeregeln:

``` text
CHART_TOP_VISIBLE_AT_1440x900=true
CHART_MEANINGFULLY_VISIBLE_AT_1440x900=true
DUAL_STATUS_RAILS_FORBIDDEN=true
F5_RAW_METADATA_IN_HERO_FORBIDDEN=true
PRIMARY_HERO_TECHNICAL_DUMP_FORBIDDEN=true
GIANT_EMPTY_REGION_ABOVE_CHART_FORBIDDEN=true
```

## 0B.2 Visual Priority Matrix

  -------------------------------------------------------------------------------
           Priorität Surface         Visuelles        Primäre Frage
                                     Gewicht          
  ------------------ --------------- ---------------- ---------------------------
                   1 Market Chart    dominant         Was macht der Markt?

                   2 Decision        sehr hoch        Was sieht und entscheidet
                     Narrative /                      das System?
                     State                            

                   3 Ranking         hoch             Welche Instrumente sind
                                                      aktuell relevant?

                   4 Regime /        mittel-hoch      Warum ist der Zustand so?
                     Bull-Bear                        

                   5 Risk / Safety   mittel           Was wäre riskant oder
                                                      blockiert?

                   6 Economic        mittel           Ist die Evidence
                     Observability                    wirtschaftlich tragfähig?

                   7 AI / Linear     niedrig-mittel   Wie belastbar sind
                     Diagnostics                      Modell-/Diagnoseaussagen?

                   8 Governance /    niedrig,         Woher stammt die technische
                     Engineering     eingeklappt      Evidence?
  -------------------------------------------------------------------------------

Kein niedriger priorisierter Bereich darf durch Höhe, Badge-Dichte,
Farbe oder Textmenge einen höher priorisierten Bereich dominieren.

# 0C. Component-, Owner- und Reuse-Matrix

  ---------------------------------------------------------------------------------------------------------------------------
  Component     Kanonischer Owner / Template                              Discovery-Zustand   Verbindliche        Zielphase
                                                                                              Behandlung          
  ------------- --------------------------------------------------------- ------------------- ------------------- -----------
  Legacy Status `market_v0.html`                                          redundant,          entfernen oder in   1A
  Rail                                                                    Badge-Wall          Single Safety Rail  
                                                                                              konsolidieren       

  Visual        `partials/market_visual_operator_header_v1.html`          teilweise korrekt   reuse + verdichten  1A
  Operator                                                                                                        
  Header                                                                                                          

  Selected      `partials/market_primary_operator_hero_v1.html`           zu dicht,           strukturell         1A/2
  Instrument                                                              F5-/Gov-Dump        überarbeiten        
  Hero                                                                                                            

  Primary Chart `partials/market_primary_close_chart_v1.html`             reale 120 Bars,     reuse +             1A/3
                                                                          unter Fold          reposition + polish 

  Ranking       `partials/market_governed_top20_primary_v1.html`          real Top20/50,      single canonical    4A--4C
                                                                          sparse columns      component;          
                                                                                              contract-first      

  Decision      `partials/market_decision_funnel_visual_v1.html`          nicht               rewire + activity   5A/5B
  Funnel                                                                  selection-bound;    contract            
                                                                          `ACTIVE`                                

  Economic      `partials/market_economic_observability_visual_v1.html`   teilweise, Kurven   reuse; Scope        7
                                                                          fehlen              sichtbar; honest    
                                                                                              missing             

  Linear        `partials/market_ai_linear_diagnostics_visual_v1.html`    sparse              summary in Level 2, 8
  Diagnostics                                                                                 Details Level 3     

  F5 Compact    `partials/futures_market_compact_v1.html`                 unvollständige      narrow adapter; aus 1A/9
                                                                          Feld-Dumps          Hero entfernen      

  Double-Play   `partials/double_play_market_compact_v1.html`             static fixture,     klar labeln oder    5A/5B
  Compact                                                                 nicht               nicht primär zeigen 
                                                                          selection-bound                         

  Safety        `partials/market_safety_compact_v1.html`                  badge-dense         semantic groups     6
  Compact                                                                                     Risk/Safety         

  Watchlist     `partials/market_watchlist_compact_v1.html`               brauchbar           reuse as navigation 4B
                                                                                              aid                 

  Detail        DP/F5 Detail Partials                                     CDN, doppelt        Governance/Detail   1B/9
  Anchors                                                                                     only; vendorize     
                                                                                              assets              

  Current State `partials/market_current_state_compact_v1.html`           korrekt collapsed   reuse               9

  Diagnostics   `partials/market_diagnostics_drawer_v1.html`              legacy density      consolidate or      8/9
  Drawer                                                                                      retire              
  ---------------------------------------------------------------------------------------------------------------------------

## 0C.1 Reuse Decision Matrix

``` text
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

Neue Komponenten sind nur zulässig, wenn keine kanonische Owner-Struktur
existiert oder ein dokumentierter Contract-Gap dies erfordert.

# 0D. Data Owner und Source Binding Matrix

  -----------------------------------------------------------------------------------------------------------------------------------------
  Datenfeld /   Kanonischer Owner                        Source Class                           Instrument-scoped Status / Regel
  Surface                                                                                                         
  ------------- ---------------------------------------- ------------------------------------ ------------------- -------------------------
  OHLCV /       `market_futures_ohlcv_runtime_v0.py`     `CANONICAL_LOCAL_READ_ONLY_BUNDLE`                    ja reuse, kein
  Volume                                                                                                          Request-Time-Netzwerk

  Ranking       `market_ranking_funnel_runtime_v0.py`    Offline volume-rank bundle                            ja real distinct views; BTC
  Top20/50                                                                                                        ausgeschlossen

  Score         Ranking `display_score`                  deterministic derivation                              ja implemented

  Rank Delta    kein Owner                               ---                                                  --- data-blocked; nicht
                                                                                                                  erfinden

  Regime        Ranking passthrough                      unvollständig                                  teilweise hide/de-emphasize until
                                                                                                                  producer exists

  Momentum /    OHLCV derivation                         deterministic                                         ja partial; Quality sichtbar
  Volatility /                                                                                                    
  Liquidity                                                                                                       

  Bull/Bear     Double-Play display fixture              static in-process fixture                           nein nicht als aktuelle
  Assessment                                                                                                      Instrument-Evidence
                                                                                                                  darstellen

  Decision      `decision_funnel_display_v1.py`          manifest-verified offline evidence        nein, baseline explizit
  Funnel                                                                                                          `NOT_INSTRUMENT_SCOPED`
                                                                                                                  bis Rewire

  Risk / Safety Safety matrix + current state            deterministic / repo snapshot                  teilweise Semantik getrennt
  / Authority                                                                                                     darstellen

  Economic      `economic_observability_display_v1.py`   baseline evidence                         nein, baseline Scope/Compatibility
                                                                                                                  sichtbar

  Linear        `ai_linear_diagnostics_display_v1.py`    evidence bundle                           scope-abhängig Scope sichtbar
  Diagnostics                                                                                                     

  Selection     kein Owner                               ---                                                  --- Pflicht neu einzuführen
  Context ID                                                                                                      

  Snapshot ID   nur Snapshot-Version vorhanden           repo snapshot                                        --- kohärenten UI-Vertrag
                                                                                                                  einführen
  -----------------------------------------------------------------------------------------------------------------------------------------

Browser-CDNs zählen als externe Request-Time-Abhängigkeit des Produkts
und sind nicht durch die Venue-/Credential-Netzwerkfreiheit ausgenommen.

``` text
TAILWIND_CDN_ALLOWED_IN_TARGET_STATE=false
CHART_JS_CDN_ALLOWED_IN_TARGET_STATE=false
VENDORED_OR_BUNDLED_ASSETS_REQUIRED=true
NETWORK_ALLOWLIST_DEFAULT=SELF_ONLY
```

# 0E. Selection Context und Snapshot Identity Contract

Der wichtigste Integritätsvertrag des Dashboards ist eine atomare,
nachvollziehbare Auswahl- und Snapshot-Identität.

``` text
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

``` text
selection_context_id
snapshot_id
instrument_scope
scope_compatibility
source_id
freshness_state
quality_state
```

Zulässige Scope-Kompatibilität:

``` text
MATCHED_SELECTED_INSTRUMENT
FLEET_LEVEL_NOT_INSTRUMENT_SCOPED
PORTFOLIO_LEVEL_NOT_INSTRUMENT_SCOPED
STRATEGY_FAMILY_LEVEL_NOT_INSTRUMENT_SCOPED
INCOMPATIBLE_WITH_SELECTION
UNKNOWN_SCOPE
```

Atomare SSR-Regel:

``` text
ONE_REQUEST_ONE_COMMITTED_SELECTION_CONTEXT=true
ALL_CONTEXT_BUILDERS_COMPLETE_BEFORE_RENDER=true
PARTIAL_SURFACE_COMMIT_FORBIDDEN=true
MISMATCHED_CONTEXT_RENDER_FORBIDDEN=true
```

Eine fleet-level oder baseline-level Surface darf unverändert bleiben,
wenn ein Instrument gewechselt wird, aber nur, wenn sie sichtbar als
nicht instrument-scoped markiert ist. Sie darf nicht den Eindruck
erwecken, zur neu ausgewählten Zeile zu gehören.

# 0F. Discovery Defect Closure Matrix

  --------------------------------------------------------------------------------
  Defect      Befund                      Severity Verbindliche   Closure Evidence
                                                   Zielphase      
  ----------- --------------------- -------------- -------------- ----------------
  D1          Duale                           HIGH 1A             single
              Badge-/Status-Rails                                 header/safety
                                                                  rail
                                                                  screenshot + DOM
                                                                  assertion

  D2          Chart unter 1440×900            HIGH 1A             viewport
              Fold                                                screenshot +
                                                                  bounding-box
                                                                  assertion

  D3          wahrgenommene große             HIGH 1A             screenshot
              Leerregion                                          diff + geometry
                                                                  check

  D4          `unavailable`                   HIGH 4A/4B          column policy
              dominiert Ranking                                   tests +
                                                                  screenshot

  D5          Ranking min-width                MED 4B             DOM overflow
              Overflow-Risiko                                     assertion

  D6          schwache Hierarchie /           HIGH 1A/2           visual review +
              Engineering im Hero                                 content
                                                                  ownership test

  D7          Statusduplikation                MED 1A/6           semantic
              Header/Rail/Safety                                  uniqueness test

  D8          irreführendes grünes             MED 5A             state-contract
              `ACTIVE`                                            tests

  D9          unerwartete                      MED 1B             network
              Browser-CDNs                                        allowlist test;
                                                                  zero external
                                                                  requests

  D10         fragmentiertes Design           HIGH 1B             central token
              System                                              owner + no
                                                                  duplicate inline
                                                                  tokens test
  --------------------------------------------------------------------------------

Kein Defect darf nur kosmetisch als geschlossen markiert werden. Closure
benötigt Code-/Contract-Evidence, fokussierte Tests und
Screenshot-Evidence.

------------------------------------------------------------------------

# 1. Nicht verhandelbare Grenzen

``` text
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

Das Dashboard darf Daten darstellen, erklären, vergleichen und
visualisieren.

Das Dashboard darf niemals:

-   Orders auslösen,
-   Sessions aktivieren,
-   Broker- oder Exchange-Zugriffe starten,
-   Runtime Authority erzeugen,
-   Strategy Authority erzeugen,
-   Positionen verändern,
-   Risk-, Sizing-, Safety- oder Promotion-Gates überschreiben,
-   Daten erfinden,
-   fehlende Daten durch stillschweigende Fallbacks ersetzen.

Diese Grenzen müssen durch statische und browserbasierte Tests belegbar
sein. Insbesondere sind verbotene Imports, Provider-Aufrufe,
Credential-Zugriffe, mutierende Controls und unerwartete
Browser-Netzwerkzugriffe im Dashboard-Pfad als Merge-Blocker zu
behandeln.

------------------------------------------------------------------------

# 2. Produktprinzipien

## 2.1 Operator-first

Die Oberfläche wird nach Nutzerfragen strukturiert, nicht nach internen
Modulen.

Primäre Nutzerfragen:

``` text
WHAT_IS_HAPPENING?
WHY_IS_IT_HAPPENING?
WHAT_DOES_THE_SYSTEM_SEE?
WHAT_IS_BLOCKING_ACTION?
HOW_FRESH_IS_THE_DATA?
WHAT_IS_THE_CURRENT_RISK?
WHAT_IS_THE_ECONOMIC_STATE?
```

Interne Owner, Contracts, Manifest-Digests und Debug-Felder gehören in
sekundäre, einklappbare Bereiche.

## 2.2 Show, do not dump

Erlaubt:

-   Charts,
-   Heatmaps,
-   Sparklines,
-   Score Bars,
-   Funnel,
-   Timelines,
-   Matrices,
-   compact KPIs,
-   visual status rails.

Nicht als primäre Darstellung erlaubt:

-   lange Rohtextblöcke,
-   Status-Badge-Wände,
-   unstrukturierte `missing`-Listen,
-   endlose Kartenstapel,
-   breite Tabellen mit überwiegend `unavailable`,
-   technische Felder ohne visuelle Priorisierung.

## 2.3 Data truth before decoration

``` text
REAL_DATA_FIRST=true
PROVENANCE_VISIBLE=true
FRESHNESS_VISIBLE=true
QUALITY_VISIBLE=true
MISSING_DATA_EXPLICIT=true
```

Schöne Visualisierung ist nur zulässig, wenn Datenherkunft und
Zustandssemantik korrekt bleiben.

## 2.4 Progressive disclosure

Drei Ebenen:

``` text
LEVEL_1=OPERATOR_OVERVIEW
LEVEL_2=ANALYTICAL_DETAIL
LEVEL_3=ENGINEERING_AND_GOVERNANCE_DETAIL
```

Level 1 muss ohne Scroll-Wüste verständlich sein.

Verbindliche Zuordnung:

``` text
LEVEL_1_CONTENT=HEADER,HERO,MARKET_CHART,RANKING,DECISION_SUMMARY
LEVEL_2_CONTENT=DECISION_CHAIN,RISK,ECONOMIC,DIAGNOSTIC_SUMMARY
LEVEL_3_CONTENT=PROVENANCE,CONTRACTS,MANIFESTS,RAW_EVIDENCE,ENGINEERING_DETAILS
```

Level 3 darf umfangreich sein, ist aber standardmäßig eingeklappt.

Zusätzliche Regeln zur visuellen Ruhe:

``` text
MAX_SIMULTANEOUS_ACCENT_COLORS=4
MAX_BADGES_PER_PRIMARY_CARD=3
MAX_PRIMARY_CARDS_ABOVE_FOLD=5
ONE_DOMINANT_VISUAL_PER_SECTION=true
```

------------------------------------------------------------------------

# 3. Verbindliche Informationsarchitektur

## 3.1 Global Header

Der Header muss kompakt bleiben und folgende Informationen enthalten:

-   Peak Trade Logo / Produktname
-   Read-only Status
-   Futures-only Status
-   Daten-Freshness
-   Datenquelle
-   Economic Gate
-   Runtime Authority
-   Orders
-   Live
-   aktueller Snapshot-Zeitpunkt

Verbindliche visuelle Gruppierung:

``` text
HEADER_LEFT=PRODUCT_IDENTITY
HEADER_CENTER=SNAPSHOT_TIME,SOURCE,FRESHNESS
HEADER_RIGHT=READ_ONLY,ECONOMIC_STATE,AUTHORITY_STATE
SAFETY_RAIL=EXECUTION_DISABLED,ORDERS_DISABLED,LIVE_DISABLED,FUTURES_ONLY
```

Orders, Live, Runtime und Futures-only dürfen nicht als vier
konkurrierende Hauptbadges erscheinen. Sie sind als kompakter Safety
Rail zu bündeln. Nur Abweichungen oder Inkonsistenzen erhalten erhöhte
visuelle Priorität.

Nicht erlaubt:

-   mehrere redundante Badge-Reihen,
-   unklare doppelte Statusanzeigen,
-   technische Versionsblöcke im Hauptfokus,
-   mehr als drei prominente Statusbadges im Header,
-   starke visuelle Alarmierung für erwartete sichere Zustände wie
    `LIVE_DISABLED`.

## 3.2 Operator Overview Hero

Der erste sichtbare Inhaltsbereich muss folgende Elemente enthalten:

### A. Selected Instrument

-   Symbol
-   Exchange
-   Contract Type
-   Timeframe
-   Last Price
-   Change
-   High / Low
-   Volume
-   Rank
-   Score

### B. Market Regime

-   Trend
-   Momentum
-   Volatility
-   Liquidity
-   Bull/Bear Balance
-   Confidence / evidence state
-   Freshness

### C. Current Decision State

-   Observe / Candidate / Confirmed / Blocked
-   Long / Short / Neutral
-   Top block reason
-   Current pipeline stage
-   AI activity state
-   data quality state

### D. Critical System State

-   Economic Validity
-   Runtime Authority
-   Orders
-   Live
-   Risk status
-   Safety status

Dieser Bereich muss auf einem normalen Desktop ohne übermäßiges Scrollen
sichtbar sein.

Verbindliche Hierarchie:

``` text
HERO_PRIMARY=SELECTED_INSTRUMENT_AND_DECISION_NARRATIVE
HERO_SECONDARY=MARKET_REGIME
HERO_TERTIARY=CRITICAL_SYSTEM_STATE
HERO_LAYOUT_REFERENCE=8_COLUMNS_PRIMARY,4_COLUMNS_SYSTEM_STATE
```

High, Low, Volume, Rank und Score werden als kompakte Metadatenzeile
dargestellt und nicht als eigenständige KPI-Kachelreihe. Die aktuelle
Entscheidungsaussage besitzt höhere visuelle Priorität als der letzte
Preis.

## 3.3 Market Chart

Pflicht:

-   Candlestick Chart
-   Volume
-   Zeitachse
-   Preisachse
-   Tooltip
-   Instrument
-   Timeframe
-   Bar count
-   Freshness
-   Source
-   O/H/L/C
-   Zoom oder auswählbare Fenster, sofern vorhandene Architektur dies
    unterstützt

Optional später:

-   VWAP
-   volatility bands
-   entry / exit markers
-   regime overlays
-   strategy markers

Leere Chartflächen ohne präzise Erklärung sind verboten.

Zusätzliche Chart-Verträge:

``` text
DEFAULT_VISIBLE_BARS=120
SUPPORTED_CHART_WINDOWS=50,120,250,ALL
GAP_RENDERING_POLICY=EXPLICIT
STALE_DATA_OVERLAY_REQUIRED=true
MISSING_INTERVALS_MARKED=true
TIMEZONE_VISIBLE=true
PRICE_PRECISION_SOURCE_BOUND=true
NO_VISUAL_INTERPOLATION_OF_MISSING_BARS=true
```

Volume bleibt dem Preisbereich visuell untergeordnet. Source, Freshness
und Bar Count werden in einer kompakten Chart-Metazeile geführt.

## 3.4 Ranking Surface

Top 20 und Top 50 müssen echte unterschiedliche Datenansichten sein.

Primär sichtbare Pflichtspalten:

-   Rank
-   Instrument
-   Score
-   Rank change
-   Long/Short balance
-   Regime
-   Momentum
-   Volatility
-   Last / Change
-   Freshness

Sekundäre Detailfelder über Row Expansion, Detail Drawer oder Tooltip:

-   Eligibility
-   Liquidity
-   Bull / Long
-   Bear / Short
-   Data status
-   Source details

Pflichtinteraktion:

-   Instrument anklicken
-   Chart aktualisiert sich
-   AI-/Decision-Bereich aktualisiert sich
-   Risk-/Economic-Kontext aktualisiert sich
-   ausgewählte Zeile bleibt sichtbar markiert

Pflichtvisualisierung:

-   Score Bar
-   Rank delta
-   Momentum indicator
-   Volatility indicator
-   Liquidity indicator
-   Long/Short balance
-   kleine Sparkline, sofern Daten vorhanden

Zusätzliche Ranking-Verträge:

``` text
RANKING_SINGLE_CANONICAL_COMPONENT=true
RANKING_LIMIT_STATE_EXPLICIT=true
RANKING_STABLE_SORT_REQUIRED=true
RANKING_TIE_BREAK_POLICY_REQUIRED=true
SELECTED_ROW_PERSISTS_AFTER_SORT=true
SELECTION_URL_STATE_REQUIRED=true
NO_ROW_SELECTION_WITHOUT_COMPLETE_CONTEXT_UPDATE=true
```

Nicht erlaubt:

-   Top 20 und Top 50 als bloße Labels ohne echte Datenumschaltung,
-   Tabellen, in denen `unavailable` visuell dominiert,
-   horizontale Überläufe,
-   abgeschnittene Spalten,
-   zwei getrennte Ranking-Implementierungen mit divergierender
    Semantik.

## 3.5 AI / Canonical Decision Chain

Das Dashboard muss den AI-/Decision-Layer als tatsächliche
Verarbeitungskette visualisieren.

Pflichtstufen:

``` text
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

``` text
NOT_AVAILABLE
AVAILABLE_NOT_RUN
PROCESSED
BLOCKED
STALE
FAILED
```

`ACTIVE` alleine ist verboten.

Eine Stufe darf nur als `PROCESSED` erscheinen, wenn aktuelle Evidence
tatsächliche Verarbeitung belegt.

Verbindliche Gruppierung:

``` text
INPUT=MARKET_INPUT,MARKET_CONTEXT
ASSESSMENT=BULL_ASSESSMENT,BEAR_ASSESSMENT,STATE_TRANSITION
VALIDATION=SURVIVAL,SUITABILITY,DOUBLE_PLAY
ADMISSIBILITY=ENTRY_PRECONDITIONS,RISK_SIZING,PORTFOLIO_ADMISSIBILITY
OUTCOME=DECISION_OUTCOME
```

Die Gruppen bilden die primäre Visualisierung. Einzelstufen werden
innerhalb der Gruppe oder nach Expansion sichtbar.

Jede Stufe benötigt mindestens:

``` text
state
reason_code
evidence_ref
processed_at
input_snapshot_id
```

Semantische Trennschärfe:

``` text
BLOCKED != FAILED
STALE != NOT_AVAILABLE
AVAILABLE_NOT_RUN != PROCESSED_WITH_NEUTRAL_RESULT
```

### Pflichtvisualisierungen

-   Decision Funnel
-   Bull vs Bear Score
-   Bull/Bear contribution bars
-   Survival subcheck matrix
-   Suitability result
-   Double-Play composition matrix
-   current decision timeline
-   block reason histogram
-   reason-code timeline
-   change since previous snapshot

## 3.6 Risk and Safety

Der Risk-/Safety-Bereich muss kompakt, verständlich und visuell sein.

Pflicht:

-   Risk availability
-   Risk gate
-   Safety guard
-   KillSwitch
-   exposure
-   leverage
-   margin usage
-   liquidation distance
-   funding risk
-   reconciliation state
-   authority state

Risk und Safety werden als getrennte semantische Gruppen dargestellt:

``` text
RISK=EXPOSURE,LEVERAGE,MARGIN_USAGE,LIQUIDATION_DISTANCE,FUNDING_RISK
SAFETY=AUTHORITY,KILLSWITCH,RECONCILIATION,EXECUTION_PERMISSION
```

Fehlende oder nicht anwendbare Werte müssen differenziert werden:

``` text
NOT_APPLICABLE_NO_POSITION
MISSING_EXPECTED_SOURCE
UNAVAILABLE_RUNTIME_DISABLED
STALE
INVALID
```

Fehlende Werte werden als kompakte Hinweise dargestellt, nicht als lange
gelbe Feldlisten im Hauptbereich. Ein erwarteter sicherer Zustand wie
`UNAVAILABLE_RUNTIME_DISABLED` darf nicht wie ein Datenfehler aussehen.

## 3.7 Economic Observability

Wenn Economic Evidence vorhanden ist:

-   Equity curve
-   Drawdown curve
-   Gross / Cost / Net
-   Fees
-   Slippage
-   Funding
-   Profit Factor
-   Expectancy
-   Break-even cost
-   Required gross edge
-   Trade count
-   Turnover
-   Max Drawdown
-   Sharpe / Sortino
-   regime contribution
-   long / short contribution

Negative Evidence wird sichtbar und unverändert dargestellt.

Zero trades werden nicht versteckt.

Keine Profitabilitätsbehauptung ohne manifest-verifizierte Evidence.

Economic Evidence muss immer sichtbar an ihren tatsächlichen
Gültigkeitsbereich gebunden sein:

``` text
ECONOMIC_SCOPE_VISIBLE=true
ECONOMIC_BINDING_ID_VISIBLE=true
ECONOMIC_EVIDENCE_AGE_VISIBLE=true
ECONOMIC_SELECTED_INSTRUMENT_COMPATIBILITY_VISIBLE=true
```

Der Nutzer muss erkennen können, ob Evidence für ein einzelnes
Instrument, eine Strategy Family, ein Portfolio, einen
Offline-Baseline-Run oder ein anderes Zeitfenster gilt.

## 3.8 AI / Linear Diagnostics

Wenn vorhanden:

-   coefficient contribution
-   factor exposure
-   orthogonality matrix
-   correlation matrix
-   residual diagnostics
-   train vs validation error
-   condition number
-   parameter sensitivity
-   rolling drift

Wenn nicht vorhanden:

-   kompakte Empty-State Card
-   fehlender Owner
-   fehlendes Evidence-Artefakt
-   nächster zulässiger Offline-Slice

Keine große leere Fläche.

Im Level-2-Hauptfluss werden nur folgende Diagnostics-Zusammenfassungen
gezeigt:

``` text
MODEL_DIAGNOSTIC_STATE
TOP_CONTRIBUTING_FACTORS
DRIFT_STATE
VALIDATION_STATE
```

Orthogonality Matrix, Correlation Matrix, Residual Diagnostics,
Condition Number und detaillierte Sensitivity-Auswertungen gehören in
Level 3 oder in eine eigene Diagnostics-Detailansicht.

## 3.9 Governance and Engineering Details

Standardmäßig eingeklappt.

Enthält:

-   current state snapshot
-   PR references
-   manifest verification
-   owner paths
-   F1--F5 details
-   provenance
-   debug internals
-   raw reason codes
-   contract fields
-   source metadata
-   test references

Dieser Bereich darf umfangreich sein, aber nicht die Hauptoberfläche
dominieren.

Verbindliche Regeln:

``` text
GOVERNANCE_DEFAULT_COLLAPSED=true
GOVERNANCE_STATE_NOT_PERSISTED_ACROSS_DEMO_SESSION=true
RAW_JSON_NOT_RENDERED_BY_DEFAULT=true
COPY_EVIDENCE_ACTION_ALLOWED=true
```

Ein negativer Gate-Status darf Governance Details nicht automatisch
öffnen.

------------------------------------------------------------------------

# 4. Visual Design System

## 4.1 Gestaltungsziel

``` text
VISUAL_STYLE=PROFESSIONAL_DARK_TRADING_TERMINAL
VISUAL_TONE=CALM,PRECISE,PREMIUM,TECHNICAL
DENSITY=HIGH_BUT_READABLE
```

Die Oberfläche soll modern, hochwertig und glaubwürdig wirken.

Sie darf nicht wirken wie:

-   ein internes Admin-Panel,
-   ein Test Harness,
-   eine HTML-Debug-Ausgabe,
-   ein unvollständiges Dashboard,
-   ein Kartenfriedhof.

## 4.2 Verbindliche Design Tokens

Die konkrete Wertbelegung erfolgt repo-gebunden in Phase 1. Die
Token-Namen und ihre zentrale Eigentümerschaft sind jedoch
verpflichtend:

``` text
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

``` text
NO_GRADIENT_OVERUSE=true
NO_GLOW_OVERUSE=true
NO_GLASSMORPHISM_BY_DEFAULT=true
NO_DUPLICATE_INLINE_DESIGN_TOKENS=true
```

Verbindliche Ausgangsskalen, sofern Phase 1B keine repo-gebundene
begründete Abweichung ratifiziert:

``` text
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

-   12-column responsive grid oder funktional äquivalentes System
-   konsistente Abstände
-   definierte Content Max Width
-   klare vertikale Rhythmik
-   keine überbreiten Textzeilen
-   keine extreme Leerräume
-   keine schmalen Kartenkolonnen neben riesigen Leerflächen
-   keine abgeschnittenen Inhalte
-   keine horizontalen Scrollbalken im Hauptlayout

## 4.4 Card Hierarchy

Drei Kartenebenen:

``` text
PRIMARY_CARD
SECONDARY_CARD
DETAIL_CARD
```

Primary Cards: - Chart - Ranking - Decision Chain - Economic - Risk

Secondary Cards: - regime - contributions - block reasons - selected
instrument details

Detail Cards: - provenance - raw diagnostics - contracts - manifests

## 4.5 Farbsemantik

Farben müssen semantisch konsistent sein:

-   Grün: positive / pass / fresh / processed
-   Rot: fail / blocked / negative
-   Gelb: warning / partial / stale risk
-   Blau: informational / neutral
-   Violett: ranking / model / AI
-   Grau: unavailable / inactive / not run

Farben dürfen nie alleinige Informationsträger sein. Text oder Icons
sind zusätzlich erforderlich.

## 4.6 Typografie

Pflicht:

-   klare Hierarchie
-   Zahlen monospaced, wo sinnvoll
-   Labels kleiner als Werte
-   keine unlesbaren Mini-Texte
-   keine übermäßig dichten Statuszeilen
-   konsistente Groß-/Kleinschreibung

## 4.7 Charts

Pflicht:

-   gut lesbare Achsen
-   Tooltips
-   Legenden nur, wenn hilfreich
-   ausreichender Kontrast
-   kein dekorativer Chart ohne Aussage
-   keine Chart-Fläche ohne Daten
-   keine falsche Präzision

------------------------------------------------------------------------

# 5. Verbindlicher Interaktionsfluss

Ein Nutzer klickt ein Instrument im Ranking an.

Danach müssen synchron aktualisiert werden:

``` text
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

Der Nutzer darf nicht das Gefühl haben, dass verschiedene
Dashboard-Bereiche voneinander unabhängig oder nur dekorativ sind.

Verbindlicher Selection-Context-Vertrag:

``` text
SELECTION_CONTEXT_ID_REQUIRED=true
ALL_SURFACES_SHARE_SELECTION_CONTEXT=true
PARTIAL_CONTEXT_COMMIT_FORBIDDEN=true
STALE_SELECTION_RESPONSE_DISCARDED=true
URL_DEEP_LINK_REQUIRED=true
BROWSER_BACK_FORWARD_SUPPORTED=true
```

Chart, Regime, Decision Chain, Risk, Economic, Freshness und Provenance
dürfen zu keinem Zeitpunkt unterschiedliche Instrumente oder
Snapshot-Identitäten als gemeinsamen aktuellen Zustand präsentieren.

------------------------------------------------------------------------

# 6. Daten- und Provenance-Vertrag

Jeder dargestellte Datenblock benötigt:

``` text
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

``` text
FRESH
AGING
STALE
UNKNOWN
```

Zulässige Quality States:

``` text
READY
PARTIAL
INCOMPLETE
INVALID
MISSING
```

Dashboard-Daten dürfen nur aus folgenden Klassen stammen:

``` text
MANIFEST_VERIFIED_OFFLINE_EVIDENCE
CANONICAL_REPO_SNAPSHOT
CANONICAL_LOCAL_READ_ONLY_BUNDLE
DETERMINISTIC_DERIVATION_FROM_CANONICAL_SOURCE
```

Zeitsemantik:

``` text
evidence_generated_at=ZEITPUNKT_DER_FACHLICHEN_EVIDENCE
bundle_created_at=ZEITPUNKT_DER_READ_ONLY_BUNDLE_ERZEUGUNG
dashboard_rendered_at=ZEITPUNKT_DER_UI_DARSTELLUNG
```

Diese Zeitpunkte dürfen nicht stillschweigend gleichgesetzt werden.

Nicht zulässig:

``` text
UNLABELED_FIXTURE
RANDOM_DATA
SYNTHETIC_MARKET_SERIES
SPOT_FALLBACK
UNVERIFIED_EXTERNAL_JSON
REQUEST_TIME_PROVIDER_CALL
```

------------------------------------------------------------------------

# 6A. Browser Verification Policy

Diese Policy ist für alle visuellen Dashboard-Slices verbindlich.

``` text
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
WEBKIT_IS_NOT_REAL_SAFARI=true

REAL_SAFARI_VERIFICATION=SECONDARY
SAFARI_REQUIRED_FOR_NORMAL_SLICE_MERGE=false
SAFARI_FAILURE_BLOCKS_NORMAL_SLICE=false

POST_SLICE_INTERACTIVE_OPEN=REAL_CHROME
```

Verbindliche Regeln:

1.  Google Chrome über Playwright ist der primäre Browser für
    Entwicklung, visuelle Abnahme, Screenshots, DOM-, Console-, Network-
    und Interaktionsprüfungen.
2.  Playwright verwendet nach Möglichkeit den lokal installierten
    Google-Chrome-Channel `chrome`.
3.  Falls echter Google Chrome technisch nicht verfügbar ist, darf
    Playwright Chromium als Fallback verwendet werden.
4.  Ein Chromium-Fallback muss ausdrücklich berichtet werden und darf
    niemals als echter Google-Chrome-Nachweis bezeichnet werden.
5.  WebKit ist ausschließlich ein sekundärer
    Engine-Kompatibilitätscheck.
6.  WebKit darf nicht als echter Safari-Nachweis bezeichnet werden.
7.  Echter Safari ist ein optionaler sekundärer Kompatibilitätscheck.
8.  Safari oder WebKit sind für normale Dashboard-Slices keine
    allgemeinen Merge-Blocker.
9.  Safari wird nur dann zum Blocker, wenn ein konkreter späterer
    Release-Gate dies ausdrücklich verlangt.
10. Nach erfolgreichem Slice soll das Dashboard für die Operator-Prüfung
    sichtbar in realem Google Chrome geöffnet werden.
11. Browser-Evidence muss den tatsächlich verwendeten Browser eindeutig
    ausweisen.
12. Die bestehende Self-only-Netzwerk- und Read-only-Policy bleibt
    unverändert.

------------------------------------------------------------------------

# 7. Umsetzung in Phasen

## 7.0 Verbindliche Slice- und PR-Bindings

Jede Phase ist ein Bauabschnitt mit eigener Owner-, Datei-, Test-,
Screenshot- und Stop-Grenze. Die folgende Matrix ist verbindlich;
konkrete Dateilisten dürfen nach aktueller Repo-Prüfung enger, aber
nicht stillschweigend breiter werden.

  --------------------------------------------------------------------------------------------------------------------
  Slice   Ziel            Kandidaten-Owner /      Pflicht-Tests       Pflicht-Screenshots         Verboten
                          Dateien                                                                 
  ------- --------------- ----------------------- ------------------- --------------------------- --------------------
  Phase   Discovery       Discovery docs/evidence traceability        baseline viewports          produktive Mutation
  -1      aktualisieren   only                    completeness                                    

  Phase 0 Inventar        evidence/docs + test    artifact            current full page           UI-Semantik ändern
          durabel binden  fixtures                schema/digest                                   

  Phase   Compact         `market_v0.html`,       geometry, duplicate 1440×900 header/hero/chart  Datenproducer ändern
  1A      Header + Chart  operator header, hero,  status, no semantic                             
          above fold      chart partial           changes                                         

  Phase   Tokens, Grid,   central CSS/token       token uniqueness,   desktop/narrow/wide         neue Produktfeatures
  1B      vendorized      owner, `base.html`,     network allowlist,                              
          assets          asset bundle            responsive grid                                 

  Phase 2 Operator        hero/context display    decision sentence,  overview states             Interpretation
          Overview        adapters                priority/content                                erfinden
                                                  tests                                           

  Phase 3 Chart Polish    primary chart partial + real-data, gaps,    chart fresh/stale/missing   synthetische Bars
                          narrow context adapter  tooltip metadata,                               
                                                  stale overlay                                   

  Phase   Ranking Data    ranking                 stable sort,        data-state samples          fehlende Felder
  4A      Contract        runtime/readmodel       tie-break,                                      erfinden
                                                  sparse-field policy                             

  Phase   Ranking Visual  canonical ranking       overflow, Top20/50, Top20/Top50/narrow          zweite
  4B      Surface         partial                 selection marker                                Ranking-Komponente

  Phase   Selection       `market_surface.py`,    atomic context, URL symbol switch               partial update
  4C      Context Binding display contexts        state, back/forward                             

  Phase   Activity State  decision display        no bare ACTIVE,     all states                  counts/stages
  5A      Contract        contracts               evidence-required                               fabrizieren
                                                  PROCESSED                                       

  Phase   Funnel Visual   funnel partial/context  canonical stage     funnel/block states         Instrument-Scope
  5B      Alignment                               order, scope                                    vortäuschen
                                                  markers                                         

  Phase 6 Risk/Safety     safety context +        state taxonomy,     no-position/missing/stale   Authority verändern
          Compact         partial                 authority ambiguity                             

  Phase 7 Economic        economic display +      scope               fail/zero/missing curves    Profitabilität
          Visuals         partial                 compatibility,                                  behaupten
                                                  negative/zero                                   
                                                  preservation                                    

  Phase 8 Linear          diagnostics display +   summary/detail      summary + expanded details  große leere Karten
          Diagnostics     partial                 separation                                      

  Phase 9 Governance      current                 collapsed default,  collapsed/expanded          Hauptfluss
          Consolidation   state/details/drawers   no raw JSON default                             dominieren

  Phase   Demo Readiness  browser test            Chrome/Playwright   complete matrix in Chrome   Merge bei offenen
  10                      infra/evidence          visual regression,                              Blockern
                                                  console, network,                               
                                                  accessibility;                                  
                                                  Safari/WebKit                                   
                                                  optional secondary                              
  --------------------------------------------------------------------------------------------------------------------

Jeder Slice endet mit:

``` text
STATUS=<PASS|FAIL>
VERDICT=<SLICE_SPECIFIC_VERDICT>
GO_TOKEN=<SLICE_SPECIFIC_GO_TOKEN>
HEAD_BEFORE=<sha>
HEAD_AFTER=<sha>
ORIGIN_MAIN=<sha>
WORKTREE_CLEAN=true
FOCUSED_TESTS_PASS=true
BROWSER_EVIDENCE_COMPLETE=true
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_AUTOMATION=PLAYWRIGHT
VISUAL_EVIDENCE_COMPLETE=true
SOURCE_PROVENANCE_VERIFIED=true
TRADING_SEMANTICS_EFFECT=NONE
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
STOP_BEFORE_MERGE=true
```

## PHASE -1 --- Implementation Discovery and Feasibility Binding

Ziel:

-   reale Dashboard-Route und Render Chain identifizieren,
-   Templates, CSS, JavaScript und Komponenten-Owner erfassen,
-   verfügbare Datenowner und Evidence-Verträge bestimmen,
-   Browser-, Screenshot- und Test-Infrastruktur prüfen,
-   jede Runbook-Anforderung auf konkrete Pfade, Symbole, Tests und
    PR-Grenzen abbilden.

Pflichtartefakte:

``` text
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

``` text
CANONICAL_RENDER_CHAIN_IDENTIFIED=true
ALL_PRIMARY_OWNERS_IDENTIFIED=true
ALL_REQUIREMENTS_TRACEABLE=true
PHASE_FILE_BINDINGS_DEFINED=true
PHASE_TEST_BINDINGS_DEFINED=true
IMPLEMENTATION_READY_OR_EXPLICITLY_BLOCKED=true
```

Keine produktive UI-Mutation ist in Phase -1 zulässig.

## PHASE 0 --- Baseline Audit

Ziel:

-   aktuellen Stand vollständig inventarisieren,
-   Layout-Defekte dokumentieren,
-   Datenquellen und leere Flächen auflösen,
-   bestehende Komponenten bewerten.

Pflichtartefakte:

``` text
dashboard_component_inventory.json
data_owner_inventory.json
layout_defect_inventory.json
visual_gap_assessment.md
source_binding_matrix.json
```

Exit-Kriterium:

``` text
ALL_PRIMARY_SURFACES_CLASSIFIED=true
ALL_DATA_OWNERS_CLASSIFIED=true
ALL_LAYOUT_DEFECTS_DOCUMENTED=true
```

## PHASE 1 --- Design System and Layout Foundation

Ziel:

-   stabiles Grid,
-   responsive container,
-   Card Hierarchy,
-   typography,
-   color semantics,
-   spacing,
-   empty states,
-   loading states,
-   error states.

Keine neuen Produktfeatures vor stabilem Layout.

Exit-Kriterium:

``` text
NO_MAJOR_LAYOUT_BREAKS=true
NO_LARGE_UNEXPLAINED_EMPTY_SPACE=true
NO_HORIZONTAL_OVERFLOW=true
PRIMARY_CARD_SYSTEM_BOUND=true
```

## PHASE 2 --- Operator Overview

Ziel:

-   Hero Area,
-   selected instrument,
-   market regime,
-   current decision,
-   critical system state.

Exit-Kriterium:

``` text
FIVE_SECOND_OPERATOR_SUMMARY_PASS=true
```

## PHASE 3 --- Market Chart

Ziel:

-   echte Candles,
-   volume,
-   tooltip,
-   source,
-   freshness,
-   selected instrument binding.

Exit-Kriterium:

``` text
CANDLE_CHART_REAL_DATA=true
CHART_SELECTED_INSTRUMENT_SYNC=true
NO_EMPTY_CHART_WHEN_DATA_EXISTS=true
```

## PHASE 4 --- Ranking

Ziel:

-   Top 20,
-   Top 50,
-   sorting,
-   filtering,
-   instrument selection,
-   visual score indicators.

Exit-Kriterium:

``` text
TOP20_REAL=true
TOP50_REAL=true
TOP20_TOP50_DISTINCT=true
RANKING_INTERACTION_PASS=true
```

## PHASE 5 --- AI / Decision Chain

Ziel:

-   funnel,
-   bull/bear,
-   survival,
-   suitability,
-   double play,
-   block reasons,
-   activity states.

Exit-Kriterium:

``` text
AI_ACTIVE_LABEL_REMOVED_OR_REPLACED=true
ACTIVITY_STATE_CONTRACT_BOUND=true
DECISION_CHAIN_VISUAL_COMPLETE=true
```

## PHASE 6 --- Risk / Safety

Ziel:

-   verständliche risk surface,
-   kompakte missing states,
-   no authority ambiguity.

Exit-Kriterium:

``` text
RISK_SURFACE_OPERATOR_READABLE=true
SAFETY_STATUS_UNAMBIGUOUS=true
```

## PHASE 7 --- Economic Observability

Ziel:

-   metrics,
-   curves,
-   cost attribution,
-   negative evidence visibility.

Exit-Kriterium:

``` text
ECONOMIC_EVIDENCE_VISUALIZED=true
NO_PROFITABILITY_OVERCLAIM=true
```

## PHASE 8 --- AI / Linear Diagnostics

Ziel:

-   Contributions,
-   factor exposure,
-   drift,
-   sensitivity,
-   orthogonality.

Exit-Kriterium:

``` text
AI_DIAGNOSTIC_VISUALS_BOUND_OR_EXPLICITLY_MISSING=true
```

## PHASE 9 --- Governance Consolidation

Ziel:

-   alle technischen Details standardmäßig einklappen,
-   keine Governance-Dominanz im Hauptfluss.

Exit-Kriterium:

``` text
PRIMARY_VIEW_OPERATOR_FIRST=true
ENGINEERING_DETAILS_SECONDARY=true
```

## PHASE 10 --- Final UX and Demo Readiness

Ziel:

-   Google Chrome via Playwright,
-   optionaler sekundärer Safari-/WebKit-Kompatibilitätscheck,
-   responsive,
-   no console errors,
-   no clipped content,
-   no empty areas,
-   no embarrassing unfinished surfaces.

Exit-Kriterium:

``` text
DEMO_READY=true
EXTERNAL_VIEWER_READY=true
```

------------------------------------------------------------------------

# 8. Pflicht-Testmatrix

## 8.1 Data Truth

-   real OHLCV only
-   no fake bars
-   no spot fallback
-   no synthetic fallback
-   Bitcoin excluded
-   freshness correct
-   provenance correct
-   stale state correct
-   missing source correct

## 8.2 Layout

-   desktop Google Chrome via Playwright
-   real Chrome verification where locally available
-   optional secondary Safari compatibility check
-   common laptop width
-   wide desktop
-   no horizontal overflow
-   no clipped cards
-   no giant empty regions
-   no broken two-column grids
-   no cards narrower than minimum readable width

## 8.3 Ranking

-   Top 20 count
-   Top 50 count
-   distinct views
-   selected instrument binding
-   sorting
-   filtering
-   rank delta
-   score visualization

## 8.4 Decision Chain

-   every stage has valid state
-   `PROCESSED` requires evidence
-   `AVAILABLE_NOT_RUN` distinct
-   `BLOCKED` reason visible
-   funnel stage counts consistent
-   bull/bear values consistent
-   decision state consistent

## 8.5 Economic

-   negative values remain negative
-   zero trades remain zero
-   costs not hidden
-   gross/net distinction correct
-   no positive claim from missing evidence

## 8.6 Safety

-   no live
-   no orders
-   no authority
-   no runtime start
-   no scheduler
-   no credentials
-   no network calls
-   no action controls

## 8.7 Browser, DOM and Visual Regression

-   visual regression baseline in Google Chrome via Playwright
-   DOM overflow assertions in Chrome
-   console error assertions in Chrome
-   failed asset assertions in Chrome
-   unexpected network request assertions in Chrome
-   selection-context consistency assertions in Chrome
-   stale response discard assertions in Chrome
-   real Google Chrome verification where locally available
-   Playwright Chromium fallback explicitly reported when used
-   Playwright Chromium result not presented as equivalent to real
    Google Chrome
-   WebKit verification optional and secondary
-   real Safari verification optional and secondary
-   WebKit result not presented as equivalent to real Safari
-   Safari/WebKit failures do not block normal dashboard slices unless
    explicitly required by a later release gate

## 8.8 Accessibility

-   keyboard focus
-   meaningful labels
-   sufficient contrast
-   color not sole carrier
-   readable font sizes
-   tooltips or accessible alternatives

------------------------------------------------------------------------

# 9. Visual Acceptance Criteria

Ein Slice darf nur als visuell erfolgreich gelten, wenn:

``` text
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

``` text
PRIMARY_QUESTIONS_ANSWERED_WITHIN_5_SECONDS=true
SELECTED_INSTRUMENT_FLOW_COHERENT=true
AI_PROCESSING_VISUALLY_EXPLAINED=true
BLOCK_REASON_VISIBLE=true
RISK_VISIBLE=true
ECONOMIC_STATE_VISIBLE=true
FRESHNESS_VISIBLE=true
```

------------------------------------------------------------------------

# 9A. Fünf-Sekunden-Demo-Test

Der Demo-Test wird von mindestens einer Person durchgeführt, die die
konkrete Implementierung nicht erstellt hat. Nach fünf Sekunden
Betrachtung des 1440×900 Operator Overview muss sie ohne technische
Detailansicht beantworten können:

  ---------------------------------------------------------------------
  Frage                              Muss erkennbar sein
  ---------------------------------- ----------------------------------
  Welches Instrument ist ausgewählt? Symbol + Markt-/Contract-Kontext

  Was macht der Markt?               Chart + kompakter Regime-Zustand

  Was sieht das System?              Decision State + Bull/Bear/Context

  Was blockiert?                     primärer Blocker + Pipeline-Gruppe

  Wie frisch sind die Daten?         Freshness + Snapshot-Zeit

  Wie steht Risk/Safety?             kompakter, eindeutiger Zustand

  Wie steht Economic Validity?       Gate + Scope + Evidence-Zustand

  Darf gehandelt werden?             klar: nein; keine
                                     Authority/Orders/Live
  ---------------------------------------------------------------------

``` text
FIVE_SECOND_DEMO_TEST_PASS=true
TECHNICAL_EXPLANATION_REQUIRED_FOR_BASIC_STATE=false
AMBIGUOUS_SCOPE_COUNT=0
MISLEADING_STATUS_COUNT=0
```

# 10. Screenshot-basierte Abnahme

Jeder PR mit visuellen Änderungen muss primär in Google Chrome via
Playwright Screenshots erzeugen:

1.  Full page desktop.
2.  Header + operator overview.
3.  Chart.
4.  Top 20.
5.  Top 50.
6.  Selected instrument interaction.
7.  Decision funnel.
8.  Bull/Bear view.
9.  Risk/Safety.
10. Economic view.
11. AI diagnostics.
12. Governance collapsed.
13. Governance expanded.
14. Missing-source state.
15. Stale-data state.
16. narrow desktop viewport.

Screenshots sind Bestandteil der PR-Evidence.

Browser-Abnahme muss unterscheiden:

``` text
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_AUTOMATION=PLAYWRIGHT
PRIMARY_PLAYWRIGHT_CHANNEL=chrome
REAL_CHROME_VERIFIED=<true|false>
PLAYWRIGHT_CHROMIUM_FALLBACK_USED=<true|false>
WEBKIT_AUTOMATION_VERIFIED=<true|false|NOT_RUN>
REAL_SAFARI_VERIFIED=<true|false|NOT_RUN>
```

Ein Playwright-Chromium-Lauf darf nicht als vollständiger realer
Google-Chrome-Nachweis bezeichnet werden.

Ein bestandener WebKit-Lauf darf nicht als vollständiger realer
Safari-Nachweis bezeichnet werden.

Safari und WebKit sind sekundäre Kompatibilitätschecks und keine
allgemeinen Merge-Blocker für normale Dashboard-Slices.

------------------------------------------------------------------------

# 11. PR- und Merge-Regeln

Jeder Slice:

``` text
ONE_BOUNDED_PR=true
STOP_BEFORE_MERGE=true
FOCUSED_TESTS_REQUIRED=true
VISUAL_SCREENSHOTS_REQUIRED=true
SOURCE_MANIFEST_VERIFY_REQUIRED=true
IMPLEMENTATION_MANIFEST_REQUIRED=true
```

Kein Merge bei:

``` text
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
PRIMARY_CHROME_EVIDENCE_MISSING
UNBOUND_DESIGN_TOKEN_DUPLICATION
```

------------------------------------------------------------------------

# 12. Definition of Done

Das Produkt ist abgeschlossen, wenn:

``` text
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
CONSOLE_CLEAN=true
SCREENSHOT_REVIEW_PASS=true
VISUAL_REGRESSION_PASS=true
DOM_OVERFLOW_ASSERTIONS_PASS=true
SELECTION_CONTEXT_ATOMIC=true
SNAPSHOT_IDENTITY_COHERENT=true
UNEXPECTED_NETWORK_REQUESTS_ZERO=true
CHROME_PLAYWRIGHT_VERIFIED=true
REAL_CHROME_VERIFIED_OR_CHROMIUM_FALLBACK_EXPLICIT=true
WEBKIT_VERIFIED_OR_NOT_REQUIRED=true
REAL_SAFARI_VERIFIED_OR_NOT_REQUIRED=true
DEMO_READY=true
```

Zusätzlich:

``` text
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

------------------------------------------------------------------------

# 13. Cursor Master Instruction

``` text
GO_PEAK_TRADE_VISUAL_OPERATOR_DASHBOARD_PRODUCT_V1_2

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
   - Browser Render Verification,
   - Chrome Screenshots via Playwright,
   - Safari Screenshots nur bei explizitem sekundärem Kompatibilitätscheck,
   - Layout Checks,
   - Console Error Check,
   - Source Provenance Proof,
   - MANIFEST.sha256.
9. Stoppe vor jedem Merge.
10. Kein PR gilt als erfolgreich, wenn nur zusätzliche Karten, Badges oder Rohtext ergänzt wurden.
11. Primärziel ist visuelle Verdichtung und Operator-Verständlichkeit.
12. Engineering- und Governance-Details bleiben sekundär und einklappbar.
13. Ein grünes ACTIVE ist ohne Processing Evidence verboten.
14. Große Leerflächen, gebrochene Grids, abgeschnittene Karten und horizontale Überläufe sind Merge-Blocker.
15. Nach jeder Phase Screenshot-Abnahme gegen dieses Runbook.
16. Phase -1 ist vor jeder produktiven Dashboard-Mutation verpflichtend.
17. Jede Phase benötigt konkrete Owner-, Datei-, Test- und Screenshot-Bindings.
18. Selection Context und Snapshot Identity müssen über alle synchronen Oberflächen atomar konsistent sein.
19. Google Chrome ist der Primärbrowser. Playwright Chromium darf nur als explizit berichteter Fallback verwendet werden; WebKit und echter Safari sind sekundär und getrennt zu berichten.
20. Unerwartete Browser-Netzwerkzugriffe sind Merge-Blocker.
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

------------------------------------------------------------------------

# 14. Abschlussgrundsatz

Das Peak Trade Dashboard ist kein Repository-Statusbericht im Browser.

Es ist die visuelle Operator-Schnittstelle des Systems.

Es muss zeigen:

``` text
what the market is doing
what the system sees
why the system sees it
what is blocking action
how trustworthy the data is
how risk and economic validity currently stand
```

Alles andere ist sekundär.

------------------------------------------------------------------------

# 15. Design Review Gate (Ergänzung)

> **Hinweis:** Diese Ergänzung erweitert das Runbook inhaltlich, ohne
> die Versionsbezeichnung **v1.3** zu ändern. Sie dient als zusätzliche
> Governance-Regel für die Umsetzung.

## 15.1 Zweck

Nach Abschluss der grundlegenden visuellen Basis (Design-System und
Operator Overview) wird ein verpflichtender UX-/Produkt-Review
durchgeführt, bevor weitere größere Dashboard-Surfaces umgesetzt werden.

Ziel ist es, Informationshierarchie, visuelle Prioritäten und
Bedienbarkeit früh zu validieren und spätere großflächige UI-Umbauten zu
vermeiden.

## 15.2 Verpflichtender Review-Zeitpunkt

``` text
DESIGN_REVIEW_GATE_AFTER_PHASE_2=true
AUTO_CONTINUE_AFTER_PHASE_2=false
```

Der Review findet nach Abschluss von:

-   Phase 1B (Design System Foundation)
-   Phase 2 (Operator Overview)

statt.

## 15.3 Review-Inhalte

Mindestens zu bewerten:

-   Above-the-fold-Wirkung
-   Informationshierarchie
-   Hero-Struktur
-   Chart-Priorität
-   Badge-Dichte
-   Operator-Verständlichkeit
-   5-Sekunden-Test
-   Premium-Eindruck
-   Konsistenz mit den Produktzielen

## 15.4 Benchmark

Die Bewertung orientiert sich an modernen Trading-Oberflächen (z. B.
Kraken, Binance, TradingView) hinsichtlich:

-   Klarheit
-   visueller Hierarchie
-   Fokus auf Markt und Entscheidung
-   Reduktion technischer Ablenkung

Dies ist ausdrücklich **kein** Auftrag zur Übernahme fremder Designs,
sondern dient ausschließlich als UX-Referenz.

## 15.5 Ergebnis

Der Review endet mit genau einem der folgenden Zustände:

``` text
DESIGN_GATE=PASS
```

oder

``` text
DESIGN_GATE=REWORK_REQUIRED
```

Bei `REWORK_REQUIRED` werden ausschließlich die bereits vorhandenen
Oberflächen (Header, Hero, Chart, Layout) verbessert. Es werden keine
neuen funktionalen Dashboard-Bereiche begonnen, bis die grundlegende
Informationsarchitektur den Produktzielen entspricht.

## 15.6 Nicht-Ziel

Der Design Review Gate verändert keine fachliche Logik.

``` text
TRADING_SEMANTICS_EFFECT=NONE
RISK_SEMANTICS_EFFECT=NONE
DECISION_SEMANTICS_EFFECT=NONE
AUTHORITY_EFFECT=NONE
DATA_PRODUCER_EFFECT=NONE
```

------------------------------------------------------------------------

# 16. Visual Composition Contract (Ergänzung)

Diese Ergänzung präzisiert die bereits vorhandenen Designregeln. Ziel
ist nicht die Einführung neuer Dashboard-Funktionen, sondern die
verbindliche Steuerung der visuellen Hierarchie.

## 16.1 Produktprinzip

``` text
VISUAL_REFACTOR_ALLOWED=true
VISUAL_REFACTOR_PREFERRED_OVER_NEW_SURFACES=true
NO_SECOND_RUNBOOK=true
NO_SECOND_VISUAL_TRUTH=true
```

Vor jeder neuen Dashboard-Surface ist zu prüfen, ob bestehende Bereiche
(Header, Hero, Chart, Ranking) zunächst verbessert werden müssen.

## 16.2 Visual Hierarchy Contract

``` text
ONE_PRIMARY_FOCUS_PER_VIEW=true
NO_INFORMATION_COMPETITION=true
ONE_VISUAL_STORY_PER_VIEW=true
PRIMARY_ACTION_VISIBLE_WITHIN_3_SECONDS=true
EXCHANGE_GRADE_INFORMATION_HIERARCHY_REQUIRED=true
```

## 16.3 Above-the-fold Composition

``` text
HEADER_MAX_HEIGHT_PX=64
HERO_DOMINANT=true
PRIMARY_CHART_VISUAL_SHARE_MIN=40_PERCENT
RANKING_STARTS_BELOW_PRIMARY_CHART=true
NO_BADGE_WALL_ALLOWED=true
NO_DEBUG_PANEL_APPEARANCE=true
```

Der Marktchart und die Entscheidung bilden gemeinsam den visuellen
Schwerpunkt. Engineering-, Provenance- und Governance-Informationen
dürfen oberhalb des Folds niemals dominieren.

## 16.4 Premium UX Gate

``` text
PREMIUM_PRODUCT_FEEL_REQUIRED=true
FIRST_IMPRESSION_REVIEW_REQUIRED=true
VISUAL_INFORMATION_HIERARCHY_REQUIRED=true
PRODUCT_DEMO_READY_REQUIRED=true
```

Ein Slice gilt nur dann als bestanden, wenn sowohl die technische als
auch die visuelle Abnahme erfolgreich sind.

## 16.5 Refactor Policy

Bereits vorhandene Komponenten dürfen beliebig oft reorganisiert,
verdichtet oder visuell verbessert werden.

Neue Komponenten sind erst zulässig, wenn: - bestehende Primärflächen
die Informationshierarchie erfüllen, - Above-the-fold keine
Debug-Anmutung besitzt, - Header, Hero und Chart als zusammenhängende
Operator-Story funktionieren.

------------------------------------------------------------------------

# 17. Composition-first Design Philosophy (Ergänzung)

> Diese Ergänzung erweitert das Runbook inhaltlich, ohne die
> Versionsbezeichnung **v1.3** zu ändern.

## 17.1 Grundprinzip

Das Dashboard wird nicht mehr als Sammlung einzelner Karten entworfen,
sondern als **eine zusammenhängende visuelle Komposition**.

``` text
COMPOSITION_FIRST=true
CARD_FIRST=false
ONE_VISUAL_CANVAS=true
ONE_OPERATOR_STORY=true
```

Die Frage lautet nicht mehr:

> "Welche Card kommt als Nächstes?"

Sondern:

> "Welche Information muss der Operator als Nächstes wahrnehmen?"

## 17.2 Komposition statt Card-Wall

Nicht zulässig:

``` text
CARD
CARD
CARD
CARD
CARD
```

Zielbild:

``` text
HEADER
↓
HERO
↓
PRIMARY MARKET CHART
↓
RANKING
↓
DECISION FLOW
↓
SECONDARY DETAILS
```

Alle Bereiche bilden eine gemeinsame visuelle Geschichte.

## 17.3 Panel statt Card

Primäre Bereiche sind als Panels einer Gesamtkomposition zu behandeln.

``` text
PANELS_OVER_CARDS=true
MINIMIZE_VISIBLE_BORDERS=true
WHITESPACE_IS_LAYOUT=true
ALIGNMENT_OVER_CONTAINERS=true
```

Container dienen ausschließlich der Orientierung und dürfen niemals die
visuelle Hauptstruktur bestimmen.

## 17.4 Visual Story Contract

Der Blick des Operators soll in genau dieser Reihenfolge geführt werden:

``` text
MARKET
→ DECISION
→ BLOCKER
→ CHART
→ RANKING
→ DETAIL
```

Jeder neue Bereich muss diese Blickführung unterstützen.

## 17.5 Anti-Patterns

Merge-Blocker für neue UI-Slices:

``` text
CARD_WALL=true
DEBUG_PANEL_LOOK=true
BADGE_WALL=true
COMPETING_PRIMARY_SURFACES=true
EXCESSIVE_BORDERS=true
TECHNICAL_METADATA_DOMINATES=true
```

## 17.6 Refactor Priority

Vor jeder funktionalen Erweiterung gilt:

``` text
LAYOUT_REFACTOR_BEFORE_NEW_FEATURES=true
VISUAL_COMPOSITION_HAS_PRIORITY=true
REMOVE_CARD_APPEARANCE_WHEN_POSSIBLE=true
```

Das Ziel ist ein Dashboard, das wie ein professionelles Trading-Terminal
als zusammenhängende Oberfläche wirkt -- nicht wie eine
Aneinanderreihung einzelner Widgets oder Karten.

------------------------------------------------------------------------

# 18. Composition Refactor Priority (Ergänzung)

> Diese Ergänzung erweitert das Runbook inhaltlich, ohne die
> Versionsbezeichnung **v1.3** zu ändern.

## 18.1 Strategische Priorität

Ab diesem Stand besitzt die visuelle Komposition Vorrang vor der
Implementierung weiterer Dashboard-Surfaces.

``` text
VISUAL_COMPOSITION_REFACTOR_PRIORITY=HIGHEST
PHASE3_DEFERRED_UNTIL_COMPOSITION_APPROVED=true
NEW_SURFACES_BLOCKED_UNTIL_COMPOSITION_PASS=true
```

## 18.2 Architekturprinzip

Das Dashboard ist als **eine zusammenhängende Operator-Oberfläche** zu
gestalten.

Nicht zulässig:

-   Widget-Sammlung
-   Card-Wall
-   Dashboard-Chrome als dominantes Gestaltungselement

Ziel:

-   eine ruhige Premium-Komposition
-   Hero und Decision als gemeinsame Fläche
-   Chart als dominante Bühne
-   Ranking und Detailflächen eindeutig sekundär

## 18.3 Composition Review Gate

Vor jeder neuen funktionalen Surface muss bestätigt sein:

``` text
COMPOSITION_REVIEW_PASS=true
VISUAL_PREMIUM_FEEL_CONFIRMED=true
CARD_WALL_ELIMINATED=true
OPERATOR_STORY_CONTINUOUS=true
```

Erst danach dürfen weitere Visual-Slices (Ranking, Decision Flow,
Economic usw.) erweitert werden.

## 18.4 Erfolgsmaßstab

Die Oberfläche soll nicht als internes Dashboard wahrgenommen werden,
sondern als professionelles Trading-Terminal mit klarer visueller
Hierarchie und einer durchgängigen Blickführung.


----------------------------------------------------------------------------

# 19. Landmark Architecture (Ergänzung)

> Diese Ergänzung erweitert das Runbook inhaltlich, ohne die Versionsbezeichnung **v1.3** zu ändern.

## 19.1 Composition-first ist verpflichtend

```text
LANDMARK_FIRST=true
SECTION_FIRST=false
CARD_FIRST=false
ONE_CONTINUOUS_OPERATOR_SURFACE=true
EVERY_VISIBLE_SECTION_MUST_JUSTIFY_EXISTENCE=true
```

Das Dashboard wird als eine einzige Operator-Oberfläche verstanden. Komponenten sind Bausteine einer Komposition und keine eigenständigen Produkte.

## 19.2 Verbindliche Landmark-Struktur

```text
GLOBAL_HEADER
↓
PRIMARY_MARKET_SURFACE
↓
DECISION_SURFACE
↓
OBSERVABILITY_SURFACE
↓
ENGINEERING_DRAWER
```

Alle sichtbaren Bereiche müssen genau einer Landmark zugeordnet sein.

## 19.3 Zulässige Inhalte

### GLOBAL_HEADER
- Produktidentität
- Snapshot
- Freshness
- Read-only Safety Rail

### PRIMARY_MARKET_SURFACE
- Hero
- Decision Narrative
- Primary Candlestick Chart
- kompakte Marktmetadaten

### DECISION_SURFACE
- Ranking
- Decision Flow
- Blocker
- Risk/Safety

### OBSERVABILITY_SURFACE
- Economic
- AI Diagnostics
- Watchlist
- Trend-/Regime-Zusammenfassung

### ENGINEERING_DRAWER (standardmäßig geschlossen)
- Governance
- Provenance
- F1–F5
- Contracts
- Raw Metadata
- Debug
- Internals
- Current State
- Source Dumps

## 19.4 Progressive Disclosure

```text
LEVEL1=PRIMARY_MARKET_SURFACE
LEVEL2=DECISION_SURFACE
LEVEL3=OBSERVABILITY_SURFACE
LEVEL4=ENGINEERING_DRAWER
```

Kein Level-4-Inhalt darf ohne explizite Benutzeraktion sichtbar sein.

## 19.5 Visual Weight Contract

```text
PRIMARY_MARKET_SURFACE≈40%
DECISION_SURFACE≈30%
OBSERVABILITY_SURFACE≈20%
ENGINEERING_DRAWER≈10%
```

Engineering darf niemals den Markt dominieren.

## 19.6 Elimination Contract

Vor jeder neuen Oberfläche ist zu prüfen:

```text
CAN_EXISTING_SECTION_BE_REMOVED=true
CAN_EXISTING_SECTIONS_BE_MERGED=true
CAN_INFORMATION_BE_MOVED_TO_DRAWER=true
REMOVE_DUPLICATE_SURFACES_FIRST=true
```

## 19.7 Merge-Blocker

```text
LANDMARK_ARCHITECTURE_BROKEN=true
ENGINEERING_DOMINATES_PRIMARY_FLOW=true
DUPLICATE_INFORMATION_VISIBLE=true
MULTIPLE_PRIMARY_FOCAL_POINTS=true
PAGE_READS_AS_DEBUG_PANEL=true
```

Neue Features sind blockiert, bis diese Verstöße beseitigt sind.

## 19.8 Full-page Composition Review

Jeder größere Slice bewertet die komplette Seite und nicht nur den geänderten Bereich.

```text
FULL_PAGE_COMPOSITION_REVIEW_REQUIRED=true
LANDMARK_INTEGRITY_REQUIRED=true
VISUAL_FLOW_REQUIRED=true
PRIMARY_OPERATOR_STORY_REQUIRED=true
```

Kein Slice gilt als abgeschlossen, wenn zwar der geänderte Bereich verbessert wurde, die Gesamtkomposition jedoch verschlechtert oder fragmentiert wurde.
----------------------------------------------------------------------------

# 20. UX Acceptance, Visual Flow und Quality Contracts (Ergänzung)

> Diese Ergänzung erweitert das Runbook inhaltlich, ohne die Versionsbezeichnung **v1.3** zu ändern. Sie operationalisiert die bereits definierten Composition-, Landmark- und Premium-Ziele mit messbaren UX-, Flow- und Qualitätsverträgen.

## 20.1 UX Acceptance Contract

Visuelle Aussagen wie `premium`, `professionell`, `ruhig` oder `Trading-Terminal` sind nur dann abnahmefähig, wenn sie durch konkrete, prüfbare Kriterien unterlegt sind.

```text
UX_ACCEPTANCE_CONTRACT=true
PRIMARY_VISUAL_DOMINANCE=MARKET
MAX_PRIMARY_FOCAL_POINTS=2
MAX_VISIBLE_PRIMARY_ACTIONS=1
MAX_VISIBLE_STATUS_BADGES=8
MAX_CONCURRENT_INFORMATION_GROUPS_ABOVE_FOLD=5
MAX_PROMINENT_STATUS_BADGES_IN_HEADER=3
ONE_PRIMARY_MESSAGE_PER_PANEL=true
NO_PARAGRAPHS_ABOVE_FOLD=true
NO_TABLES_ABOVE_FOLD=true
NO_MULTI_COLUMN_STATUS_LISTS_ABOVE_FOLD=true
```

Ein Primary Focal Point ist eine visuell dominante Fläche, die durch Größe, Kontrast, Farbe, Bewegung, Typografie oder Position Aufmerksamkeit beansprucht. Im Referenzviewport dürfen maximal zwei solcher Fokuspunkte konkurrieren: der Marktchart sowie die aktuelle Decision Narrative einschließlich primärem Blocker.

Das UX Gate gilt nur als bestanden, wenn ein fachfremder Reviewer die primäre Operator Story ohne Engineering-Erklärung nachvollziehen kann.

## 20.2 Landmark Ownership Contract

Jede Landmark besitzt genau einen kanonischen Template-, Context- und Test-Owner. Partials dürfen innerhalb einer Landmark wiederverwendet werden, aber keine zweite Landmark-Identität oder parallele Surface-Hierarchie erzeugen.

```text
LANDMARK_OWNER_REQUIRED=true
ONE_CANONICAL_OWNER_PER_LANDMARK=true
SECOND_LANDMARK_IMPLEMENTATION_FORBIDDEN=true
LANDMARK_CONTEXT_OWNER_REQUIRED=true
LANDMARK_TEMPLATE_OWNER_REQUIRED=true
LANDMARK_TEST_OWNER_REQUIRED=true
```

Verbindliche Owner-Bindings müssen durch Discovery und Traceability konkretisiert werden:

```text
GLOBAL_HEADER_OWNER=<repo-bound-owner>
PRIMARY_MARKET_SURFACE_OWNER=<repo-bound-owner>
DECISION_SURFACE_OWNER=<repo-bound-owner>
OBSERVABILITY_SURFACE_OWNER=<repo-bound-owner>
ENGINEERING_DRAWER_OWNER=<repo-bound-owner>
```

Owner-Felder mit Platzhaltern sind kein Dauerzustand. Vor Mutation der jeweiligen Landmark müssen konkrete Repo-Pfade, Symbole und Tests gebunden sein.

Nicht zulässig:

- zweiter Hero-Owner,
- zweiter Decision-Summary-Owner,
- paralleler Safety-Rail-Owner,
- duplizierte Ranking-Surface,
- Engineering-Drawer-Inhalte außerhalb des kanonischen Drawers.

## 20.3 Visual Flow before Grid

Grid, Rows, Columns und Cards sind Implementierungsdetails. Die fachliche und visuelle Reihenfolge wird durch die Operator Story bestimmt.

```text
LAYOUT_DRIVEN_BY_VISUAL_FLOW=true
GRID_IS_IMPLEMENTATION_DETAIL=true
ROW_COUNT_IS_NOT_A_PRODUCT_REQUIREMENT=true
COLUMN_COUNT_IS_NOT_A_PRODUCT_REQUIREMENT=true
LANDMARK_ORDER_IS_PRODUCT_REQUIREMENT=true
```

Ein Grid darf angepasst, aufgelöst oder asymmetrisch eingesetzt werden, wenn dadurch Blickführung, Lesbarkeit und Priorität verbessert werden. Ein formal korrektes 12-Spalten-Layout ist kein Ersatz für eine kohärente Komposition.

Lokale Layout-Optimierung ist unzulässig, wenn sie die Gesamtseite verschlechtert.

## 20.4 Eye-Path und Operator Story Contract

Die Blickführung folgt der natürlichen Wahrnehmungsreihenfolge eines professionellen Trading-Terminals:

```text
EXPECTED_EYE_PATH=
GLOBAL_HEADER
→ SELECTED_INSTRUMENT_AND_MARKET_CONTEXT
→ PRIMARY_MARKET_CHART
→ DECISION_NARRATIVE_AND_PRIMARY_BLOCKER
→ RANKING_AND_MARKET_SELECTION
→ DECISION_CHAIN_AND_RISK
→ ECONOMIC_AND_DIAGNOSTIC_OBSERVABILITY
→ ENGINEERING_DRAWER
```

Zusätzliche Regeln:

```text
VISUAL_FLOW_TOP_TO_BOTTOM=true
VISUAL_FLOW_LEFT_TO_RIGHT_WITHIN_LANDMARK=true
NO_UNNECESSARY_EYE_BACKTRACKING=true
NO_CROSS_PAGE_DEPENDENCY_FOR_PRIMARY_STATE=true
PRIMARY_BLOCKER_VISIBLE_WITHOUT_SEARCH=true
CHART_CONTEXT_VISIBLE_WITHOUT_SCROLL_BACK=true
```

Die Decision Narrative darf im Hero präsent sein, aber der Chart bleibt die dominante visuelle Bühne. Decision und Blocker müssen anschließend unmittelbar lesbar sein, ohne dass der Nutzer zu einem weit entfernten Bereich zurückspringen muss.

Die bisherige Kurzform der Operator Story wird daher verbindlich präzisiert:

```text
MARKET
→ CHART
→ DECISION
→ BLOCKER
→ RANKING
→ RISK_AND_OBSERVABILITY
→ ENGINEERING
```

## 20.5 Information Density Contract

Hohe Datendichte ist nur zulässig, wenn sie scannbar, gruppiert und semantisch priorisiert bleibt.

```text
INFORMATION_DENSITY_CONTRACT=true
DENSITY_HIGH_BUT_SCANNABLE=true
ONE_PRIMARY_MESSAGE_PER_PANEL=true
MAX_PRIMARY_TEXT_LINES_PER_PANEL=4
MAX_VISIBLE_METADATA_ITEMS_PER_PRIMARY_PANEL=8
MAX_SIMULTANEOUS_STATUS_GROUPS=3
RAW_FIELD_LISTS_ABOVE_FOLD_FORBIDDEN=true
UNSTRUCTURED_LABEL_VALUE_WALL_FORBIDDEN=true
```

Zusätzliche Regeln:

- Sekundärinformationen werden über Tooltips, Row Expansion, Detail Drawer oder kompakte Metazeilen bereitgestellt.
- Sichtbare Metadaten müssen eine direkte Operator-Frage beantworten.
- Nicht entscheidungsrelevante Felder werden entfernt, zusammengeführt oder in Level 4 verschoben.
- Mehr Information ist kein Qualitätsmerkmal, wenn die Wahrnehmungszeit steigt.

## 20.6 Whitespace Contract

Whitespace ist aktiver Bestandteil der Informationsarchitektur und kein Restbereich.

```text
WHITESPACE_IS_INFORMATION=true
NEGATIVE_SPACE_IS_LAYOUT=true
NO_FILLER_COMPONENTS_ALLOWED=true
EMPTY_SPACE_WITHOUT_PURPOSE_FORBIDDEN=true
UNEXPLAINED_VERTICAL_GAPS_FORBIDDEN=true
UNEXPLAINED_HORIZONTAL_GAPS_FORBIDDEN=true
```

Zulässiger Whitespace:

- Trennung zwischen Landmark-Gruppen,
- Hervorhebung einer dominanten Fläche,
- Entlastung dichter Tabellen oder Charts,
- Orientierung innerhalb einer visuellen Story.

Unzulässiger Whitespace:

- durch gebrochene Grid-Spalten,
- durch feste Mindesthöhen ohne Inhalt,
- durch unsichtbare oder leere Komponenten,
- durch duplizierte Wrapper,
- durch unterbrochene Landmark-Ausrichtung.

Whitespace darf nicht durch zusätzliche Cards oder Füllkomponenten kaschiert werden.

## 20.7 Motion und Animation Policy

Animationen dienen ausschließlich der Zustandsorientierung. Dekorative Bewegung ist unzulässig.

```text
NO_DECORATIVE_ANIMATIONS=true
NO_PULSING_STATUS_BADGES=true
NO_INFINITE_LOADING_ANIMATIONS=true
TRANSITION_DURATION_MAX_MS=200
CHART_ANIMATION_OPTIONAL=true
CHART_ANIMATION_MUST_NOT_DELAY_READABILITY=true
REDUCED_MOTION_SUPPORTED=true
```

Loading-Verhalten:

```text
LOADING_INDICATOR_DELAY_MS=150
LOADING_SPINNER_MAX_VISIBLE_MS=500
LONGER_LOADING_REQUIRES_EXPLICIT_STATUS_TEXT=true
SSR_PRIMARY_CONTENT_MUST_NOT_REQUIRE_LOADING_ANIMATION=true
```

Da die Primäransicht SSR-basiert ist, dürfen Header, Hero, Chart-Rahmen und zentrale Zustände nicht erst durch eine rein dekorative Client-Animation verständlich werden.

## 20.8 Viewport und Device Policy

Das Produkt bleibt Desktop-first. Kleinere Viewports dürfen Funktionen reduzieren, aber keine irreführende oder gebrochene Darstellung erzeugen.

```text
PRIMARY_TARGET=DESKTOP
DESKTOP_FIRST=true
REFERENCE_VIEWPORT=1440x900
NARROW_DESKTOP_SUPPORTED=true
WIDE_DESKTOP_SUPPORTED=true
TABLET_SUPPORTED=true
PHONE_READ_ONLY_OPTIONAL=true
PHONE_FEATURE_PARITY_REQUIRED=false
```

Verbindliche Mindestprüfungen:

```text
NARROW_DESKTOP_VIEWPORT=1280x800
REFERENCE_DESKTOP_VIEWPORT=1440x900
WIDE_DESKTOP_VIEWPORT=1728x1117
TABLET_LANDSCAPE_VIEWPORT=1024x768
```

Für Tablet gilt:

- keine horizontalen Hauptscrollbars,
- keine abgeschnittenen Primärzustände,
- Landmark-Reihenfolge bleibt erhalten,
- Ranking darf kontrolliert verdichtet werden,
- Engineering Drawer bleibt nutzbar.

Für Phone gilt, solange keine vollständige Phone-Surface beschlossen ist:

```text
PHONE_ROUTE_MAY_SHOW_EXPLICIT_DESKTOP_RECOMMENDATION=true
PHONE_MUST_NOT_SHOW_BROKEN_DESKTOP_LAYOUT=true
PHONE_MUST_REMAIN_READ_ONLY=true
```

## 20.9 Visual Debt Contract

Provisorische UI-Zustände sind nicht als Abschluss eines Slices zulässig.

```text
VISUAL_DEBT_FORBIDDEN=true
TEMPORARY_UI_NOT_ALLOWED=true
TODO_UI_FORBIDDEN=true
PLACEHOLDER_COMPONENTS_FORBIDDEN=true
PLACEHOLDER_COPY_FORBIDDEN=true
UNOWNED_VISUAL_HACKS_FORBIDDEN=true
```

Zulässig sind ausdrücklich markierte, ehrliche Empty States für fachlich fehlende Daten. Diese sind kein Visual Debt, sofern Owner, Ursache, Scope und nächster zulässiger Slice klar benannt sind.

Ein Slice darf nicht mit dem Argument abgeschlossen werden, dass ein sichtbarer UI-Mangel „später“ bereinigt werde. Entweder wird er im Slice geschlossen oder als expliziter Blocker gemeldet.

## 20.10 Screenshot Quality Contract

Screenshot-Evidence ist ein Qualitätsartefakt und muss den tatsächlich abgenommenen Produktzustand zeigen.

```text
SCREENSHOT_QUALITY_CONTRACT=true
SCREENSHOT_MUST_SHOW_COMPLETE_VIEW=true
NO_BROWSER_DEVTOOLS_VISIBLE=true
NO_SCROLLBAR_ARTIFACTS=true
NO_CLIPPED_CONTENT=true
NO_LOADING_STATE_CAPTURE=true
NO_PARTIAL_RENDER_CAPTURE=true
NO_TRANSIENT_TOOLTIP_CAPTURE_UNLESS_REQUIRED=true
NO_CURSOR_OBSCURING_PRIMARY_CONTENT=true
CONSISTENT_DEVICE_SCALE_FACTOR_REQUIRED=true
CONSISTENT_VIEWPORT_REQUIRED=true
```

Jeder Screenshot benötigt mindestens folgende Metadaten in Evidence oder Manifest:

```text
browser
browser_channel
browser_version
viewport
device_scale_factor
route
selected_symbol
ranking_limit
selection_context_id
snapshot_id
captured_at
```

Full-page Screenshots müssen zusätzlich die Landmark-Reihenfolge und den Zustand des Engineering Drawers eindeutig erkennen lassen.

## 20.11 Design Drift und Full-page Regression Contract

Jeder visuelle PR wird als Änderung der gesamten Komposition bewertet.

```text
EVERY_VISUAL_PR_REEVALUATES_FULL_PAGE=true
NO_LOCAL_OPTIMIZATION_ALLOWED=true
NO_VISUAL_DRIFT_ALLOWED=true
FULL_PAGE_REGRESSION_REVIEW_REQUIRED=true
LANDMARK_WEIGHT_REGRESSION_FORBIDDEN=true
PRIMARY_FOCUS_REGRESSION_FORBIDDEN=true
```

Die Abnahme vergleicht mindestens:

- Landmark-Reihenfolge,
- visuelles Gewicht,
- Chart-Dominanz,
- Badge-Dichte,
- sichtbare Border-Dichte,
- Informationsdichte,
- Whitespace,
- Engineering-Anteil,
- Eye Path,
- Five-Second-Test.

Ein lokaler Screenshot reicht nicht aus, wenn die Änderung die Gesamtkomposition beeinflussen kann.

## 20.12 UX Geometry Assertions

Subjektive Reviews werden durch messbare Geometrie-Prüfungen ergänzt.

```text
UX_GEOMETRY_ASSERTIONS_REQUIRED=true
PRIMARY_CHART_BOUNDING_BOX_REQUIRED=true
HEADER_BOUNDING_BOX_REQUIRED=true
HERO_BOUNDING_BOX_REQUIRED=true
ENGINEERING_DRAWER_DEFAULT_HIDDEN_ASSERTION=true
LANDMARK_ORDER_DOM_ASSERTION=true
```

Mindestens zu prüfen:

```text
HEADER_HEIGHT_PX<=64
PRIMARY_CHART_TOP_Y<900
PRIMARY_CHART_VISIBLE_HEIGHT_PX>=280
HORIZONTAL_OVERFLOW_PX=0
PRIMARY_FOCAL_POINT_COUNT<=2
PROMINENT_HEADER_BADGE_COUNT<=3
VISIBLE_STATUS_BADGE_COUNT<=8
LEVEL4_VISIBLE_ELEMENT_COUNT=0
```

Abweichungen sind nur zulässig, wenn sie im PR explizit begründet, screenshot-basiert reviewed und im Runbook ratifiziert werden.

## 20.13 Erweiterte Merge-Blocker

Zusätzlich zu den bestehenden Merge-Regeln gelten:

```text
UNOWNED_LANDMARK
DUPLICATE_LANDMARK_OWNER
PRIMARY_FOCAL_POINT_COUNT_EXCEEDED
EYE_PATH_BROKEN
UNJUSTIFIED_EMPTY_SPACE
FILLER_COMPONENT_PRESENT
RAW_FIELD_WALL_ABOVE_FOLD
PLACEHOLDER_UI_PRESENT
SCREENSHOT_QUALITY_INCOMPLETE
FULL_PAGE_REVIEW_MISSING
DESIGN_DRIFT_DETECTED
BROKEN_TABLET_LAYOUT
DECORATIVE_ANIMATION_DOMINATES
```

## 20.14 Erweiterte Definition of Done

Die Definition of Done wird um folgende Bedingungen erweitert:

```text
UX_ACCEPTANCE_CONTRACT_PASS=true
LANDMARK_OWNERS_BOUND=true
VISUAL_FLOW_CONTRACT_PASS=true
EYE_PATH_CONTRACT_PASS=true
INFORMATION_DENSITY_CONTRACT_PASS=true
WHITESPACE_CONTRACT_PASS=true
MOTION_POLICY_PASS=true
VIEWPORT_POLICY_PASS=true
VISUAL_DEBT_ZERO=true
SCREENSHOT_QUALITY_PASS=true
FULL_PAGE_DESIGN_DRIFT_REVIEW_PASS=true
UX_GEOMETRY_ASSERTIONS_PASS=true
```

## 20.15 Ergänzung der Cursor Master Instruction

Die Cursor Master Instruction wird inhaltlich um folgende verbindliche Arbeitsregeln erweitert:

```text
36. Grid, Rows, Columns und Cards sind Implementierungsdetails; die Operator Story und Landmark-Reihenfolge sind Produktanforderungen.
37. Jede Landmark benötigt vor Mutation einen kanonischen Template-, Context- und Test-Owner.
38. Die verbindliche Blickführung lautet MARKET → CHART → DECISION → BLOCKER → RANKING → RISK/OBSERVABILITY → ENGINEERING.
39. Oberhalb des Folds sind Paragraphen, Tabellen, Rohfeldwände und mehr als fünf konkurrierende Informationsgruppen unzulässig.
40. Whitespace darf nur eine erkennbare Layout- oder Priorisierungsfunktion besitzen; Füllkomponenten sind verboten.
41. Dekorative, pulsierende oder unendliche Animationen sind unzulässig; Reduced Motion muss unterstützt werden.
42. Desktop ist primär; Narrow Desktop, Wide Desktop und Tablet Landscape sind verpflichtend zu prüfen.
43. Provisorische UI, TODO-UI, Platzhaltertexte und unowned Visual Hacks dürfen keinen Slice abschließen.
44. Screenshot-Evidence muss vollständige, stabile Renderzustände ohne DevTools, Clipping, Loading-Artefakte oder Scrollbar-Artefakte zeigen.
45. Jeder visuelle PR benötigt einen Full-page Composition Review; lokale Verbesserung bei globaler Verschlechterung ist FAIL.
46. UX-Geometrie, Landmark-Reihenfolge, Chart-Sichtbarkeit, Badge-Anzahl und Level-4-Unsichtbarkeit sind automatisiert zu prüfen.
47. Kein Slice darf mehr als zwei primäre visuelle Fokuspunkte erzeugen.
48. Änderungen an der visuellen Story dürfen erst nach Runbook-Ratifizierung erfolgen.
```

----------------------------------------------------------------------------

# 21. Konsolidierter UX- und Composition-Gate

Vor der Fortsetzung funktionaler Dashboard-Slices müssen die technische, visuelle und kompositorische Abnahme gemeinsam PASS sein.

```text
TECHNICAL_GATE_PASS=true
DATA_TRUTH_GATE_PASS=true
SAFETY_GATE_PASS=true
COMPOSITION_GATE_PASS=true
LANDMARK_GATE_PASS=true
UX_ACCEPTANCE_GATE_PASS=true
FULL_PAGE_REVIEW_PASS=true
```

Ein grüner technischer Testlauf ist nicht ausreichend, wenn die Seite weiterhin als Card-Wall, Debug-Panel, fragmentierte Widget-Sammlung oder visuell ungeführte Statusfläche wahrgenommen wird.

Der finale Gate-Zustand lautet genau:

```text
DESIGN_GATE=PASS
```

oder:

```text
DESIGN_GATE=REWORK_REQUIRED
```

Bei `REWORK_REQUIRED` bleiben neue funktionale Surfaces blockiert. Der Rework bewertet und verbessert die gesamte Seite, nicht nur den zuletzt veränderten Ausschnitt.


----------------------------------------------------------------------------

# 22. Canonical Single Source of Truth Contract (Ergänzung)

> Diese Ergänzung erweitert das Runbook inhaltlich, ohne die Versionsbezeichnung **v1.3** zu ändern.

## 22.1 SSOT

```text
CANONICAL_SINGLE_SOURCE_OF_TRUTH=MASTER_V2_AND_DOUBLE_PLAY
NO_SECOND_SSOT_ALLOWED=true
NO_SECOND_CANONICAL_MODEL_ALLOWED=true
NO_DASHBOARD_DOMAIN_MODEL_ALLOWED=true
NO_UI_SIDE_BUSINESS_STATE_ALLOWED=true
IF_CANONICAL_OWNER_EXISTS_THEN_CONSUME_OWNER_OUTPUT=true
```

## 22.2 Dashboard Consumer Contract

```text
DASHBOARD_MAY_ONLY_RENDER_CANONICAL_OUTPUT=true
NO_DOMAIN_LOGIC_IN_DASHBOARD=true
NO_DECISION_ENGINE_IN_DASHBOARD=true
NO_RISK_ENGINE_IN_DASHBOARD=true
NO_DOUBLE_PLAY_IMPLEMENTATION_IN_DASHBOARD=true
NO_MASTER_V2_IMPLEMENTATION_IN_DASHBOARD=true
NO_CANONICAL_STATE_RECONSTRUCTION_ALLOWED=true
NO_SECOND_DECISION_PIPELINE_ALLOWED=true
```

## 22.3 Adapter Contract

```text
ADAPTERS_ARE_PRESENTATION_ONLY=true
ADAPTERS_MUST_BE_LOSSLESS=true
ADAPTERS_MAY_NOT_CREATE_NEW_SEMANTICS=true
ADAPTERS_MAY_NOT_CHANGE_CANONICAL_STATE=true
ADAPTERS_MAY_NOT_INFER_NEW_TRADING_STATE=true
ADAPTERS_MAY_NOT_CACHE_COMPETING_STATE=true
```

## 22.4 Cursor-Ergänzung

Die Cursor Master Instruction wird um folgende verbindliche Regeln ergänzt:

```text
49. Das Dashboard besitzt niemals eine eigene fachliche Wahrheit.
50. Master V2 einschließlich Double Play ist die einzige fachliche Wahrheit.
51. Dashboard-Code konsumiert ausschließlich kanonische Core-Outputs.
52. Existiert kein passender Core-Owner, wird zuerst der Core erweitert – niemals das Dashboard.
```
