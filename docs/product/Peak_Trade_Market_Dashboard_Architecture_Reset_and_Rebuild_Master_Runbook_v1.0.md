# Peak_Trade Market Dashboard Architecture Reset & Rebuild Master Runbook v1.0

## 0. Zweck, Status und Einsatzgrenze

Dieses Runbook ersetzt additive Reparaturversuche am bestehenden Market Dashboard durch einen kontrollierten Architektur-Reset mit anschließendem kanonischem Neuaufbau.

Der Reset betrifft ausschließlich die WebUI-/Dashboard-Schicht unter `src/webui/` sowie die unmittelbar zugehörigen Templates, Presenter, Display-Builder, ViewModels, ReadModel-Adapter, Dashboard-Routen und Dashboard-spezifischen Tests.

Der Trading Core bleibt unverändert.

```text
LIVE_AUTHORIZED=false
ORDERS=false
SHADOW=false
PAPER=false
TESTNET=false
SCHEDULER=false
CAPITAL_CHANGE=false
```

Dieses Runbook autorisiert weder Runtime-Aktivierung noch Orders, Testnet, Scheduler, Kapitalbewegung, Promotion oder Live-Trading.

---

## 1. Kanonisches Architekturprinzip

Das Market Dashboard ist kein Decision-System, kein Governance-Owner und keine fachliche Wahrheit.

Es ist ausschließlich ein read-only Consumer kanonischer Systemzustände.

```text
Strategy Layer
        │
        ▼
Master V2 / Canonical Market Context
        │
        ▼
Bull & Bear Double Play
        │
        ▼
Canonical Trading Decision Evidence
        │
        ▼
Risk / Sizing / Order Intent / Execution Status
Authority / Kill Switch / Reconciliation / Promotion
Economic Evaluation / Observability / Diagnostics
        │
        ▼
Canonical Read Models / Immutable Snapshots
        │
        ▼
Dashboard Presenter / ViewModels
        │
        ▼
Market Dashboard UI
```

### 1.1 Unverhandelbare Regeln

1. `src/trading/master_v2/` bleibt fachlicher Decision Owner.
2. `double_play_composition_matrix_v1.py` bleibt kanonische Double-Play-Authority.
3. `integrated_offline_trading_logic_replay_v1.py` bleibt der kanonische Offline-Orchestrator.
4. Das Dashboard berechnet, verändert oder überschreibt keine Trading-, Risk-, Authority-, Execution- oder Promotion-Entscheidung.
5. Presenter dürfen nur validieren, selektieren, aggregieren, formatieren und visualisieren.
6. Jede sichtbare fachliche Aussage benötigt einen benannten Producer und ein kanonisches ReadModel/Snapshot.
7. Fehlt ein kanonischer Producer, zeigt die UI `UNAVAILABLE`, `NOT_BOUND` oder `MISSING_SOURCE` — niemals eine erfundene Ersatzwahrheit.
8. Hardcoded fachliche Zustände, statische Decision-Fixtures und implizite Dummy-Fallbacks sind auf der produktiven `/market`-Route verboten.
9. Der Reset darf keine Trading-Core-Semantik verändern.
10. Ein technischer PASS ist kein Produkt-PASS. Produktfreigabe erfolgt nur nach explizitem Operator Review in Chrome.

---

## 2. Verifizierter Ist-Zustand

### 2.1 Aktuelle Route und Surface

```text
GET /market
  -> src/webui/market_surface.py
  -> build_market_v0_page_template_context(...)
  -> templates/peak_trade_dashboard/market_v0.html
  -> landmark partials
```

`src/webui/market_surface.py` ist derzeit als `CANONICAL_MARKET_VIEWMODEL_OWNER` markiert, obwohl die Route fachliche Aussagen aus mehreren teilweise statischen, hardcodierten oder nicht kanonisch gebundenen Quellen zusammensetzt.

### 2.2 Verifizierte Architekturbrüche

| ID | Befund | Risiko | Zielzustand |
|---|---|---|---|
| GAP-01 | Dashboard Double Play nutzt `build_static_dashboard_display_dict` statt kanonischer `composition_matrix_v1`-Evidence | Doppelte Decision-Wahrheit | Nur kanonisches DP-Evidence-ReadModel konsumieren |
| GAP-02 | `market_dashboard_current_state_snapshot_v0.py` enthält hardcodierte Zustände | UI kann veralteten Governance-Stand behaupten | Snapshot entfernen oder an kanonischen Producer binden |
| GAP-03 | Decision Sentence wird im Presentation Layer aus gemischten ViewModels komponiert | UI-Business-Logic | Satz nur aus kanonischem Decision Summary ReadModel |
| GAP-04 | Safety-/Authority-Flags sind teilweise hardcodiert | Falsche Operator-Sicherheit | Kanonisches Safety/Authority Snapshot erforderlich |
| GAP-05 | `source=kraken` / `source=dummy` und implizite Legacy-Fallbacks | Nicht nachvollziehbare Datenherkunft | Explizite Source-Provenance, fail-closed |
| GAP-06 | Integrated Replay / DecisionPacket besitzt keinen `/market`-Consumer | Kernentscheidung fehlt im Dashboard | Neues read-only Decision Evidence ReadModel |
| GAP-07 | Economic Status erscheint mehrfach aus verschiedenen Quellen | Inkonsistente Operator-Aussage | Ein Economic Summary Owner, mehrere reine Projektionen zulässig |
| GAP-08 | Price, Rank, Freshness und Blocker werden mehrfach erzeugt | Doppelter Presenter-Owner | Je Datenklasse genau ein Page-Context Owner |
| GAP-09 | Funnel-Zwischenstufen und Equity/Drawdown fehlen | Unvollständige Surface | Ehrliche Missing-Source-Zustände oder neue kanonische ReadModels |
| GAP-10 | Bestehendes Design ist stark aus Governance-/Statusboxen aufgebaut | Produktziel verfehlt | Trading-Plattform-artige Informationshierarchie |

### 2.3 Bestehende brauchbare ReadModels

Diese Komponenten sind Kandidaten zur Wiederverwendung, aber nicht automatisch freigegeben:

- `market_ranking_funnel_readmodel.v0`
- `market_futures_ohlcv_readmodel.v0`
- `market_depth_readmodel.v0`
- `market_tape_readmodel.v0`
- `futures_read_only_market_dashboard_v0`
- `universe_selection_readmodel.v1`
- `workflow_dashboard_readmodel.v1`
- `last_paper_run_panel_readmodel.v0`
- Economic evidence JSONs
- Linear diagnostics JSONs

Folgende Quellen sind für die neue produktive Surface bis zur Neubindung gesperrt:

- `DoublePlayDashboardDisplaySnapshot` aus statischer Fixture-Erzeugung
- `market_dashboard_current_state_snapshot_v0` mit hardcodierten Konstanten
- nicht gekennzeichnete `dummy`-Payloads
- UI-seitig erzeugte Decision-/Safety-/Authority-Aussagen

---

## 3. Zielarchitektur

### 3.1 Layer Contract

```text
LAYER A — DOMAIN / DECISION OWNERS
  strategies/
  trading/master_v2/
  governance/
  risk_layer/
  execution/
  backtest/economic_viability_*
  observability/
  research/linear_evidence/

LAYER B — CANONICAL DASHBOARD READ MODELS
  immutable, versioned, provenance-bearing, read-only
  no UI formatting
  no Jinja knowledge
  no business decisions

LAYER C — PRESENTERS / PAGE COMPOSITION
  validate + map + format + sort + group
  no authority
  no decision synthesis
  no silent fallback

LAYER D — UI
  SSR templates and minimal interaction
  no domain logic
  no state ownership
  no order/runtime action
```

### 3.2 Kanonische Dashboard Contracts

Der Neuaufbau soll mindestens folgende Contracts besitzen. Bereits vorhandene Contracts dürfen wiederverwendet werden, wenn sie die Anforderungen erfüllen.

| Contract | Fachlicher Owner | Mindestinhalt |
|---|---|---|
| `MarketInstrumentSnapshotV1` | Futures market data | instrument, venue, timestamp, OHLCV, mark/last, change, freshness, provenance |
| `MarketRankingSnapshotV1` | Ranking/Universe | rank, score, eligibility, reasons, selected instrument, timestamp |
| `CanonicalDecisionSummaryV1` | Master V2 integrated replay | decision, direction, confidence/status, reason codes, evidence digest, event time |
| `DoublePlayDecisionSnapshotV1` | `composition_matrix_v1` | bull assessment, bear assessment, composition result, arbitration, blockers, provenance |
| `SafetyAuthoritySnapshotV1` | Authority + Kill Switch + Risk | authority class, kill-switch state, risk gate, execution permission, fail-closed reasons |
| `ExecutionStateSnapshotV1` | Execution/Reconciliation | mode, intent state, fill state, recon state, unknown outcome, timestamp |
| `EconomicSummarySnapshotV1` | Economic Evaluation | gate status, PF, return, drawdown, cost drag, expectancy, sample size, evidence path/digest |
| `DiagnosticsSummarySnapshotV1` | Diagnostics | diagnostic statuses only, non-authoritative marker, bundle digest |
| `DashboardFreshnessSnapshotV1` | Composition runtime | per-source age, stale/missing flags, page generated time |

### 3.3 Provenance-Anforderungen

Jeder Contract muss mindestens folgende Metadaten tragen:

```text
schema_id
schema_version
producer_module
producer_version or git_sha where available
generated_at
effective_at
source_kind
source_reference or evidence_digest
freshness_state
```

Kein Presenter darf fehlende Provenance stillschweigend ergänzen.

---

## 4. Reset-Strategie

Der Reset erfolgt nicht als unkontrolliertes Löschen. Er erfolgt in einer isolierten Branch, mit Inventar, Allowlist, Quarantäne und reversiblen Commits.

### 4.1 Grundsatz

```text
REMOVE OR QUARANTINE PRESENTATION COMPLEXITY
PRESERVE DOMAIN OWNERS
PRESERVE VALID READMODEL PRODUCERS
REBUILD CONSUMER BOUNDARIES
```

### 4.2 Erlaubter Scope

Primär erlaubt:

```text
src/webui/**
templates/peak_trade_dashboard/**
tests/webui/**
tests/**market_dashboard**
docs/**market_dashboard**
scripts/webui/**
```

Sekundär erlaubt, nur für neue read-only Adapter/Contracts:

```text
src/observability/**dashboard**
src/trading/master_v2/**display**
src/trading/master_v2/**snapshot**
```

### 4.3 Verbotener Scope

Ohne separate Discovery und explizite Begründung nicht ändern:

```text
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py
src/trading/master_v2/double_play_composition_matrix_v1.py
src/trading/master_v2/canonical_market_context_v1.py
src/governance/capital_risk_sizing_v1.py
src/governance/canonical_order_intent_v1.py
src/execution/pipeline.py
src/risk_layer/**
src/governance/promotion_loop/**
src/backtest/engine.py
strategy semantics under src/strategies/**
```

Import-only oder typed adapter usage ist zulässig; Semantikänderungen sind verboten.

---

## 5. Ausführungsphasen

## PHASE 0 — Preflight und Baseline Freeze

### Ziel

Exakte Ausgangslage sichern, bevor Dateien entfernt oder umgebaut werden.

### Schritte

1. Prüfe Branch, HEAD, Origin, Worktree und laufende Prozesse.
2. Erzeuge vollständiges Dashboard-Dateiinventar.
3. Erzeuge Route-/Import-/Template-Abhängigkeitsinventar.
4. Sichere Baseline-Screenshots in echtem Chrome über Playwright bei festgelegten Viewports.
5. Exportiere aktuelle `/market`-SSR-HTML-Ausgabe und Page-Context-Keyliste.
6. Führe relevante Tests aus und dokumentiere bereits vorhandene Fehler separat.
7. Erzeuge einen Baseline-Manifest-Digest.

### Mandatory Evidence

```text
evidence/market_dashboard_reset/baseline/
  git_state.txt
  file_inventory.txt
  route_inventory.txt
  import_inventory.txt
  template_inventory.txt
  context_keys.json
  market_page.html
  chrome_1512x982.png
  chrome_1920x1080.png
  test_results.txt
  manifest.sha256
```

### Gate

```text
PHASE_0_PASS=true only if:
- worktree state is known
- baseline commit SHA recorded
- all dashboard-owned files inventoried
- screenshots and HTML captured
- pre-existing failures classified
```

HARD STOP bei unbekannten lokalen Änderungen oder unklarer Branch-Herkunft.

---

## PHASE 1 — Ownership Guard und Delete-Allowlist

### Ziel

Verhindern, dass der Reset Trading-Core- oder fachliche Owner beschädigt.

### Schritte

1. Klassifiziere jede Dashboard-abhängige Datei als:
   - `DOMAIN_OWNER`
   - `CANONICAL_READMODEL`
   - `PRESENTER`
   - `TEMPLATE`
   - `ROUTE`
   - `FIXTURE`
   - `LEGACY_FALLBACK`
   - `TEST`
2. Erzeuge eine explizite Delete-/Quarantine-Allowlist.
3. Erzeuge eine Preserve-Liste für alle Domain Owner und brauchbaren Producer.
4. Prüfe alle Imports aus WebUI in Trading Core und umgekehrt.
5. Verbiete zyklische Abhängigkeiten: Domain/ReadModel darf niemals Template oder WebUI importieren.

### Gate

```text
DELETE_ALLOWLIST_APPROVED_BY_CONTRACT=true
DOMAIN_OWNER_DELETE_COUNT=0
FORBIDDEN_SCOPE_CHANGE_COUNT=0
```

Kein Löschen vor bestandenem Gate.

---

## PHASE 2 — Legacy Dashboard Quarantine

### Ziel

Die bestehende Surface aus der produktiven Route entfernen, ohne die Core-Systeme anzutasten.

### Vorgehen

1. Erstelle einen bounded Reset-Commit.
2. Entferne die alte `/market`-Komposition aus dem aktiven Routing.
3. Verschiebe nicht mehr benötigte Presenter/Templates zunächst nach einer klar markierten Quarantäne oder lösche sie, wenn Git-Historie und Abhängigkeitsprüfung ausreichend sind.
4. Entferne produktive Bindungen an:
   - `build_static_dashboard_display_dict`
   - hardcodierten Current-State Snapshot
   - implizite dummy/legacy payload fallback chains
   - UI-generierte Decision-/Safety-/Authority-Logik
5. Behalte bestehende ReadModel-Producer, die unabhängig und kanonisch sind.
6. Ersetze `/market` vorübergehend durch eine minimale Reset-Shell.

### Reset-Shell Contract

Die Shell darf nur zeigen:

```text
Market Dashboard
ARCHITECTURE RESET IN PROGRESS
READ ONLY
NO TRADING AUTHORITY
```

Zusätzlich:

- App-Health
- Build-/Commit-SHA
- keine fachliche Decision
- keine statischen Markt-/Risk-/Safety-Werte
- keine Governance-Card-Wand

### Gate

```text
OLD_MARKET_COMPOSITION_REACHABLE=false
STATIC_DP_FIXTURE_ON_MARKET=false
HARDCODED_CURRENT_STATE_ON_MARKET=false
DUMMY_MARKET_FALLBACK_ON_MARKET=false
TRADING_CORE_DIFF=false
RESET_SHELL_200=true
```

---

## PHASE 3 — ReadModel Contract Foundation

### Ziel

Ein typisiertes, versioniertes und fail-closed Consumer-Fundament schaffen.

### Schritte

1. Erzeuge ein Dashboard-ReadModel-Package, z. B.:

```text
src/webui/market_dashboard_readmodels_v1/
  __init__.py
  contracts.py
  provenance.py
  validation.py
  aggregate.py
```

Alternativ darf ein bestehender kanonischer ReadModel-Ort verwendet werden, wenn Ownership und Import-Richtung sauberer sind.

2. Definiere immutable Dataclasses oder äquivalente typed Contracts.
3. Implementiere Validierung:
   - schema/version
   - timestamps
   - enum values
   - source provenance
   - digest format
   - no NaN/inf where prohibited
   - stale/missing state
4. Definiere explizite `UnavailableSnapshotV1`-Semantik statt Dummy-Daten.
5. Schreibe Contract- und Serialization-Tests.
6. Implementiere keine UI und keine fachliche Berechnung.

### Gate

```text
READMODEL_CONTRACT_TESTS_PASS=true
IMMUTABILITY_PASS=true
PROVENANCE_REQUIRED=true
SILENT_DEFAULT_COUNT=0
DOMAIN_DECISION_LOGIC_ADDED=false
```

---

## PHASE 4 — Canonical Producer Adapters

### Ziel

Bestehende kanonische Systemoutputs read-only in Dashboard-Snapshots projizieren.

### Priorisierte Adapter

#### 4.1 Market Data

Reuse:

- `market_futures_ohlcv_readmodel.v0`
- `market_ranking_funnel_readmodel.v0`
- optional depth/tape readmodels

Anforderungen:

- Futures only
- explizite Venue/Instrument-Identität
- Source-Provenance
- kein stiller Dummy-Fallback
- stale data sichtbar

#### 4.2 Master V2 Decision

Neuer Adapter von kanonischer Evidence:

```text
CanonicalTradingDecisionEvidenceV1
  -> CanonicalDecisionSummaryV1
```

Der Adapter darf keine Entscheidung neu berechnen. Er darf ausschließlich Felder projizieren, Reason Codes sortieren und Provenance hinzufügen.

#### 4.3 Double Play

Neuer Adapter ausschließlich von der Evidence aus:

```text
double_play_composition_matrix_v1 result/evidence
  -> DoublePlayDecisionSnapshotV1
```

`build_static_dashboard_display_dict` ist als produktiver Datenpfad unzulässig.

#### 4.4 Safety und Authority

Konsolidiere read-only Zustände aus:

- Authority Boundary
- Kill Switch
- Risk Gate
- Execution permission/status
- Reconciliation unknown outcome / drift

Keine hardcodierten `false`, `blocked` oder `read_only`-Werte außer einem separat gekennzeichneten UI-Capability-Flag.

#### 4.5 Economic und Diagnostics

Reuse der vorhandenen Evidence-Bundles. Adapter müssen klar trennen:

```text
ECONOMIC_GATE = authoritative for promotion eligibility only
DIAGNOSTICS = diagnostic-only, never trading authority
```

### Gate

```text
CANONICAL_DECISION_ADAPTER_BOUND=true
CANONICAL_DP_ADAPTER_BOUND=true
STATIC_DP_PATH_REMOVED=true
SAFETY_AUTHORITY_PROVENANCE_PASS=true
ECONOMIC_SINGLE_SOURCE_PASS=true
DIAGNOSTIC_NON_AUTHORITY_MARKER=true
```

---

## PHASE 5 — Page Aggregate und Presenter Boundary

### Ziel

Eine einzige, schlanke Page-Komposition ohne fachliche Doppelwahrheiten.

### Zielstruktur

```text
MarketDashboardPageSnapshotV1
  market
  ranking
  decision
  double_play
  safety_authority
  execution
  economic
  diagnostics
  freshness
```

### Presenter-Regeln

Zulässig:

- Datum/Zahl formatieren
- Einheiten darstellen
- sortieren/gruppieren
- Reason Codes in erklärende Labels mappen
- responsive Display-Varianten erzeugen
- fehlende Daten als fehlend kennzeichnen

Verboten:

- Decision Sentence aus heterogenen Quellen synthetisieren
- Blocker neu ableiten
- Authority neu klassifizieren
- Risk-/Execution-Erlaubnis schätzen
- unbekannte Werte durch `safe looking defaults` ersetzen
- wirtschaftliche Bewertung neu berechnen

### Static Guard Tests

Tests müssen nach verbotenen Mustern suchen:

- direkte Konstruktion statischer DP-Fixtures auf `/market`
- Hardcoded `authority=false`, `blocked=true` o. ä. in produktiven Presentern
- `dummy` als automatischer produktiver Fallback
- Domain-Decision-Funktionen in Template-/Presenter-Modulen
- mehr als ein Owner für dieselbe Page-Fachinformation

### Gate

```text
ONE_PAGE_AGGREGATE_OWNER=true
UI_DECISION_LOGIC_COUNT=0
DUPLICATE_FACT_OWNER_COUNT=0
MISSING_SOURCE_RENDERING_PASS=true
```

---

## PHASE 6 — Product Surface Rebuild

### Ziel

Ein professionelles Trading-Dashboard, nicht ein Governance-Dokument in Kartenform.

### 6.1 Informationshierarchie

Above the fold beantwortet in dieser Reihenfolge:

1. Welches Instrument und welcher Marktstatus?
2. Was zeigt der Preis-/Marktverlauf?
3. Was ist die kanonische Systementscheidung?
4. Warum wurde diese Entscheidung getroffen?
5. Was blockiert Ausführung oder Promotion?
6. Wie frisch und vertrauenswürdig sind die Quellen?

### 6.2 Surface-Komposition

#### Global Header

- Produktname / Route
- Selected Instrument
- Venue
- Data freshness
- Read-only Capability
- kompakter Safety-/Kill-Switch-Indikator

Keine eigene Card-Wand.

#### Primary Market Workspace

- dominanter OHLCV-/Price-Chart
- Preis, Veränderung, Volumen/Marktmetriken
- Instrument Switcher/Ranking-Kontext
- kein Nested-Card-Framing

#### Canonical Decision Strip

- Decision
- Direction
- Evidence status
- wichtigste Reason Codes
- Blocker
- Authority/Execution status

Alle Werte aus den kanonischen Snapshots.

#### Secondary Analysis

- Double Play Composition
- Ranking / Watchlist
- Economic Summary
- Diagnostics

Sekundär, dicht und scanbar. Keine Wiederholung bereits gezeigter Statusfelder.

#### Engineering Drawer

- Provenance
- Digests
- schema versions
- source age
- missing-source details
- raw status codes

Standardmäßig eingeklappt.

### 6.3 Design Constraints

- Chrome/Playwright ist der primäre Browser- und Evidence-Pfad.
- Keine Safari-Abhängigkeit für Primärfreigabe.
- Kein Card-in-Card-in-Card-Aufbau.
- Maximal eine dominante Primary Surface plus wenige klare Secondary Surfaces.
- Status-Badges nur für echte Zustände, nicht als Dekoration.
- Farbe allein darf keine Safety-/Decision-Bedeutung tragen.
- Dichte wie bei einer professionellen Trading-Plattform, aber ohne imitierte Order Controls.
- Keine aktiven Buy/Sell/Submit Controls.
- Responsive Zielviewports mindestens `1512x982` und `1920x1080`.

### Gate

```text
ABOVE_FOLD_PRIMARY_CHART_VISIBLE=true
CANONICAL_DECISION_VISIBLE=true
GOVERNANCE_CARD_WALL=false
NESTED_CARD_VIOLATIONS=0
DUPLICATE_STATUS_RENDERINGS=0
NO_ORDER_CONTROLS=true
```

---

## PHASE 7 — Verification

### 7.1 Technische Tests

Mindestens:

```text
- unit tests for contracts/adapters/presenters
- static ownership tests
- route tests
- SSR snapshot tests
- missing/stale/malformed source tests
- import-boundary tests
- no-domain-change diff guard
```

### 7.2 Scenario Matrix

| Scenario | Erwartung |
|---|---|
| Alle Quellen vorhanden | vollständige Surface, Provenance sichtbar |
| Decision Evidence fehlt | `NOT_BOUND` / `MISSING_SOURCE`, keine Ersatzentscheidung |
| DP Evidence fehlt | DP-Bereich unavailable, keine Fixture |
| OHLCV stale | Chart sichtbar mit deutlichem stale state oder unavailable |
| Economic Bundle fehlt | Economic unavailable, keine Nullwerte als Ergebnis |
| Kill Switch aktiv | eindeutiger canonical safety state |
| Reconciliation unknown outcome | fail-closed Status sichtbar |
| Diagnostics fehlen | Diagnostics unavailable, Decision unverändert |
| malformed snapshot | Route fail-closed oder isolierter unavailable state; kein stiller Fallback |

### 7.3 Chrome Product Review

Playwright öffnet echtes Chrome headed und erzeugt Screenshots. Automatisierte Checks sind erforderlich, aber nicht ausreichend.

Automatisch prüfen:

- route status
- console errors
- overflow
- blank primary workspace
- duplicate text/status
- viewport fit
- accessibility basics
- screenshot diff thresholds

Operator Review prüft:

- wirkt die Seite wie ein professionelles Market Dashboard?
- ist die Informationshierarchie in wenigen Sekunden verständlich?
- dominiert der Markt-/Chart-Kontext statt Governance?
- sind Decision, Why und Blocker eindeutig?
- gibt es unnötige Boxen, Wiederholungen oder leere Flächen?

### Gate

```text
TECHNICAL_GATE_PASS=true
PRODUCT_GATE_PASS requires explicit operator GO
```

Ein automatisierter Screenshot-PASS darf niemals automatisch `PRODUCT_GATE_PASS=true` setzen.

---

## PHASE 8 — PR- und Merge-Strategie

Empfohlene bounded PR-Sequenz:

1. `PR-A: dashboard-reset-shell`
   - Baseline Evidence
   - Legacy Route entkoppeln
   - Reset-Shell
   - kein Core-Diff

2. `PR-B: dashboard-readmodel-contracts`
   - typed contracts
   - validation/provenance
   - tests

3. `PR-C: canonical-dashboard-adapters`
   - market/ranking reuse
   - Master V2 decision adapter
   - canonical DP adapter
   - safety/economic/diagnostics adapters

4. `PR-D: market-dashboard-product-surface`
   - page aggregate
   - presenter
   - templates/CSS
   - Chrome evidence

5. `PR-E: dashboard-closeout`
   - delete quarantine/legacy code
   - docs
   - final static guards
   - evidence manifest

### Merge-Regeln

- Kein Auto-Merge.
- Required checks müssen grün sein.
- Head SHA muss vor Merge verifiziert werden.
- Unexpected commits oder History Rewrite = HARD STOP.
- Unrelated CI-Infrastrukturfehler separat klassifizieren; nicht als Produkt-PASS interpretieren.
- Jeder PR bleibt unter dem vereinbarten bounded scope.

---

## 6. Definition of Done

Der Architektur-Reset ist abgeschlossen, wenn alle folgenden Bedingungen erfüllt sind:

```text
OLD_DASHBOARD_REMOVED_OR_QUARANTINED=true
TRADING_CORE_UNCHANGED=true
DASHBOARD_READ_ONLY=true
CANONICAL_DECISION_CONSUMER_BOUND=true
CANONICAL_DOUBLE_PLAY_CONSUMER_BOUND=true
STATIC_DECISION_FIXTURE_REMOVED=true
HARDCODED_SYSTEM_STATE_REMOVED=true
DUMMY_FALLBACK_REMOVED=true
CANONICAL_SAFETY_AUTHORITY_BOUND=true
PROVENANCE_COMPLETE=true
UI_BUSINESS_LOGIC_REMOVED=true
DUPLICATE_FACT_OWNERS_REMOVED=true
MISSING_DATA_FAIL_CLOSED=true
CHROME_TECHNICAL_REVIEW_PASS=true
OPERATOR_PRODUCT_REVIEW_PASS=true
LIVE_AUTHORIZED=false
ORDERS=false
```

---

## 7. Cursor Execution Prompt — Discovery und Reset PR-A

Der folgende Prompt ist der erste ausführbare Schritt. Er autorisiert ausschließlich Discovery, Evidence, bounded Reset und Reset-Shell. Er autorisiert noch keinen vollständigen Rebuild.

```text
PEAK_TRADE MARKET DASHBOARD ARCHITECTURE RESET — PR-A

MODE=IMPLEMENTATION_BOUNDED
LIVE_AUTHORIZED=false
ORDERS=false
SHADOW=false
PAPER=false
TESTNET=false
SCHEDULER=false
CAPITAL_CHANGE=false
AUTO_MERGE=false
HARD_STOP_ON_SCOPE_DRIFT=true

OBJECTIVE
Remove the current /market presentation composition from the active product route and replace it with a minimal read-only architecture-reset shell, while preserving all domain owners and reusable canonical read-model producers. Do not redesign or rebuild the final dashboard in this PR.

CANONICAL FACTS
- The dashboard is only a read-only consumer.
- Master V2 and double_play_composition_matrix_v1 are domain truth.
- The current dashboard DP display uses a static fixture path and is not canonical.
- market_dashboard_current_state_snapshot_v0 contains hardcoded display truth.
- UI-generated decision/safety/authority logic is prohibited.
- A technical pass is not a product pass.
- Chrome/Playwright is the primary browser evidence path.

STEP 0 — PREFLIGHT
1. Verify repo root, current branch, HEAD, origin/main, worktree, remotes and active processes.
2. If worktree is not clean, classify every change. HARD STOP on unrelated or unexplained changes.
3. Create a dedicated branch from current origin/main:
   fix/market-dashboard-architecture-reset-v1
4. Record all preflight data in evidence/market_dashboard_reset/pr_a/.

STEP 1 — READ-ONLY INVENTORY
Create machine-readable and human-readable inventories for:
- /market route and all route registrations
- src/webui market modules
- templates/peak_trade_dashboard market templates/partials
- market dashboard CSS/JS assets
- tests and scripts tied to /market
- imports to/from trading/master_v2, governance, risk, execution, observability and backtest
- all producers/readmodels consumed by the route

Classify each file:
DOMAIN_OWNER | CANONICAL_READMODEL | PRESENTER | TEMPLATE | ROUTE | FIXTURE | LEGACY_FALLBACK | TEST

Produce:
- file_inventory.tsv
- dependency_inventory.tsv
- preserve_list.txt
- delete_or_quarantine_allowlist.txt
- forbidden_scope_list.txt

HARD STOP if any proposed delete touches a domain owner.

STEP 2 — BASELINE EVIDENCE
Using Playwright with real Chrome/Chromium as primary path:
- start only the read-only web UI required for /market
- capture /market at 1512x982 and 1920x1080
- save rendered HTML
- save browser console output
- save the current template-context top-level keys
- run current relevant webui/market tests

Do not use Safari as primary evidence.
Do not activate paper, shadow, testnet, scheduler, execution or orders.

STEP 3 — BOUNDED RESET
Replace the active /market composition with a minimal reset shell.
The shell may display only:
- Market Dashboard
- ARCHITECTURE RESET IN PROGRESS
- READ ONLY
- NO TRADING AUTHORITY
- app health/build commit SHA if already available without adding a new domain dependency

The shell must not display:
- a decision
- DP state
- risk state
- authority state
- economic result
- market dummy data
- hardcoded system progress
- order controls

Remove the active /market bindings to:
- build_static_dashboard_display_dict
- hardcoded market_dashboard_current_state_snapshot_v0
- implicit source=dummy fallback
- UI-composed decision/safety/authority facts

Prefer deleting dead composition code when confidently isolated. Otherwise quarantine it under a clearly non-routed legacy location with an explicit deprecation marker. Do not duplicate truth.

Preserve independent canonical readmodel producers even if they are temporarily not consumed.

STEP 4 — GUARDS
Add tests proving:
- GET /market returns 200 and renders the reset shell
- old market_v0 composition is not routed
- static DP fixture builder is not reachable from /market
- hardcoded current-state snapshot is not reachable from /market
- dummy fallback is not reachable from /market
- no order/runtime action exists on the page
- forbidden domain-owner files have no diff

Add a static contract test that fails if /market imports the prohibited legacy producers again.

STEP 5 — VALIDATION
Run the narrow relevant tests first, then the bounded required repository validation appropriate for this scope.
Capture commands, exit codes and durations.
If a test exceeds 5 minutes, emit a progress diagnosis.
At 25 minutes, stop and diagnose rather than waiting indefinitely.

STEP 6 — CHROME EVIDENCE
Open the reset shell in headed Chrome/Chromium and capture final screenshots at both required viewports.
Verify:
- no console error
- no blank page
- no overflow
- exact reset-shell text
- no old dashboard landmarks/cards

This is a technical review only. Do not claim product approval.

STEP 7 — COMMIT AND PR
Create one bounded commit and push the branch.
Open a PR with:
- scope summary
- explicit no-core-change statement
- removed/quarantined legacy path list
- preserved producer list
- tests and Chrome evidence
- risks and next PR recommendation

Do not merge.
Do not enable auto-merge.
HARD STOP after PR creation.

MANDATORY FINAL OUTPUT
STATUS=PASS|FAIL
VERDICT=...
BRANCH=...
BASE_SHA=...
HEAD_SHA=...
WORKTREE_CLEAN=...
DOMAIN_OWNER_DIFF=false|true
OLD_MARKET_COMPOSITION_REACHABLE=false|true
STATIC_DP_FIXTURE_ON_MARKET=false|true
HARDCODED_CURRENT_STATE_ON_MARKET=false|true
DUMMY_FALLBACK_ON_MARKET=false|true
RESET_SHELL_200=false|true
CHROME_EVIDENCE_PASS=false|true
TECHNICAL_GATE_PASS=false|true
PRODUCT_GATE_PASS=false
TESTS=...
EVIDENCE_ROOT=...
COMMIT=...
PR_URL=...
AUTO_MERGE_ENABLED=false
MERGE_PERFORMED=false
LIVE_AUTHORIZED=false
ORDERS=false
HARD_STOP=true
```

---

## 8. Erwartete nächste Aktion nach PR-A

Erst nach Review und Merge von PR-A folgt PR-B mit den typed Dashboard ReadModel Contracts. Der Rebuild darf nicht direkt auf der alten Composition weiterarbeiten und darf keine statische Decision-Fixture wieder einführen.

