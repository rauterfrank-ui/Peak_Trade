# Peak_Trade — Market Dashboard Landscape Master Runbook V2

**Dokumenttyp:** Kanonisches Planungs-, Übergabe- und Ausführungsrunbook  
**Ziel:** Neuer Market-Workspace als strikt read-only Consumer des Peak_Trade-Systems  
**Status:** `FINAL_PRODUCT_STATE_CLOSEOUT_COMPLETE_OPERATOR_PRODUCT_GATE_PASS`  
**Geltung:** Ab dem ratifizierten Architekturstand `RATIFICATION_COMPLETE_NO_CLASS_A`  
**Primärbrowser:** Google Chrome / Playwright Real Chrome  
**Oberflächenprinzip:** Landscape · eine zusammenhängende Market-Workspace-Komposition · keine Card-Wand  
**Core-Status:** Master V2 / Double Play / Dynamic Scope / Safety bleiben unverändert  
**Runtime-Status:** `BOUND_NOT_ACTIVATED` bleibt intentional  
**Live-Status:** `LIVE_AUTHORIZED=false`, `ORDERS=false`, `SCHEDULER=false`, `CAPITAL_CHANGE=false`  
**Hardened designation:** `CAPABILITY_PR_ONLY=true` (Micro-Slices und implizite Draft-PRs untersagt)

```text
CANONICAL_REPO_PATH=docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md
REPO_INGESTION_DATE=2026-07-23
SOURCE_FILENAME=PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md
RUNBOOK_VERSION=V2
HARDENED_CAPABILITY_PR_POLICY=true
CURRENT_MAIN_SHA=9ff632885422a92e86f9dbeda79aab160bf2346b
LAST_MERGED_PR=5569  # docs-only Consumer/Anti-SSOT wording after product review; no product/runtime change
LAST_MERGED_PR_VERDICT=CAPABILITY_SCOPE_REVIEW_PASS_SQUASH_MERGED
CURRENT_MARKET_ROUTE=GET_/market_LANDSCAPE_V2_OKX_FUTURES_OHLCV_INTRABAR_200
DASHBOARD_IMPLEMENTATION_PRESENT=true
DASHBOARD_ROLE=PURE_READ_ONLY_CONSUMER
RUNTIME_ACTIVATION=false
RUNTIME_ACTIVATED=false
TRADING_RUNTIME_NOT_ACTIVATED=true
MARKET_DASHBOARD_PHASE_5_PASS=true
TECHNICAL_PRODUCT_GATE=true
OPERATOR_PRODUCT_GATE=true
DAILY_OBSERVATION_USABLE=true
PHASE_5_PASS=true
WORKSTREAM_STATE=FINAL_CLOSEOUT_COMPLETE
OPERATOR_PRODUCT_REVIEW_STATUS=PASS
OPERATOR_PRODUCT_REVIEW_REVIEWED_SHA=88f2241819dcc160c3ce688a9c7397e7cc8becec
OPERATOR_PRODUCT_REVIEW_AFTER_PR=5568
OPERATOR_PRODUCT_REVIEW_SCOPE=READ_ONLY_DAILY_OBSERVATION_SURFACE
PR_5569_DOCS_ONLY_ANTI_SSOT=true
PR_5569_DID_NOT_INVALIDATE_PRODUCT_REVIEW=true
NEXT_CAPABILITY_AUTHORIZED=false  # further product candidates require separate GO
CAPABILITY_8_DOCS_OWNERSHIP_CLOSEOUT=MERGED
PRODUCT_APPROVAL_INFERRED=false
LIVE_AUTHORIZED=false
ORDERS=false
```

**Unterscheidung (verbindlich):** Dashboard-Implementierung auf `origin&#47;main` ist vorhanden und durch gemergte Capability-PRs belegt. Trading-Runtime bleibt nicht aktiviert; Orders/Scheduler/Capital/Live bleiben false. `IMPLEMENTATION_AUTHORIZED=false` in historischen Ratifikationsblöcken (z. B. Diagnostics 4.6C) bedeutet weiterhin „keine Autorisierung jener speziellen Bindung“, nicht „Dashboard existiert nicht“.

**Phasen-/PR-Mapping (explizit, keine stille Geschichtsrewrite):** Runbook-**PHASE 2** ≡ **PR #5499**. Runbook-**PHASE 3** Shell ≡ **PR #5501**. Spätere Capability-PRs bis **PR #5548** (authentic OKX Futures intrabar) sind gemergt; siehe § Current-State Ledger und §11.

---

## 0. Executive Decision

Das Market Dashboard wird **nicht erst nach vollständiger Vollautonomie** begonnen.

Der richtige Zeitpunkt ist ein gestufter Beginn:

1. **Jetzt:** Architektur, Datenverträge, Owner-Matrix, ReadModel-Grenzen und Landscape-Komposition festlegen.
2. **Danach:** Bestehende kanonische Producer read-only anbinden und fehlende Consumer-Snapshots sichtbar machen.
3. **Parallel zur weiteren Autonomieentwicklung:** Die Surface als Integrations- und Observability-Fenster ausbauen.
4. **Vor Runtime-Aktivierung:** Dashboard technisch und operativ vollständig nutzbar machen.
5. **Nach separatem Runtime-GO:** Aktivierte Zustände lediglich darstellen; niemals selbst auslösen.

Damit ist das Dashboard früh genug vorhanden, um fehlende Telemetrie und unvollständige ReadModels sichtbar zu machen, aber spät genug gebunden, dass es keine Architektur erfindet oder den Core beeinflusst.

```text
DECISION=START_DASHBOARD_CONTRACT_AND_ARCHITECTURE_NOW
FINAL_PRODUCT_SURFACE_BEFORE_FULL_AUTONOMY=true
DASHBOARD_DRIVES_CORE=false
DASHBOARD_CONSUMES_CANONICAL_OUTPUTS=true
CORE_CHANGE_FROM_DASHBOARD_WORK=false
RUNTIME_ACTIVATION_FROM_DASHBOARD_WORK=false
```

---

## 0.1 Current-State Ledger (post PR #5548)

Repository-backed capability chain on `origin&#47;main` `6f38df4d833945197e8f472c09f402ee767c85ad` (squash-merge of PR #5548). PR numbers below are confirmed via GitHub merge history; do not invent additional PR IDs.

```text
OKX_CANONICAL_VENUE=true
FUTURES_ONLY=true
BTC_EXCLUDED=true
SPOT_EXCLUDED=true
GOVERNED_OKX_MARKET_DATA_PRODUCER_PATH=true
UNIVERSE_SELECTION_BINDING=true                 # PR #5521 / #5526 / #5527
SELECTED_INSTRUMENT_BINDING=true                # PR #5503 / #5527
IDENTITY_BINDING=true
CANONICAL_OHLCV_SNAPSHOT_BINDING=true           # PR #5526 / #5527
CONTINUOUS_OHLCV_REFRESH=true                   # PR #5528
PRODUCT_SURFACE_HARDENING=true                  # PR #5513 / #5514 (and related Phase-5 product PRs)
SOURCE_HEALTH_FRESHNESS_TREATMENT=true          # PR #5515
ENGINEERING_DRAWER=true                         # PR #5516
ACCESSIBILITY_BASELINE=true                     # PR #5518
PERFORMANCE_EVIDENCE=true                       # PR #5519
BOUNDED_ARCHIVE_ROOT_CONTRACT=true              # PR #5520
INTRABAR_CAPABILITY_MERGED=true                 # PR #5548
MODEL_A_CUMULATIVE_INTERVAL_VOLUME=true
DUPLICATE_TRADE_IDS_IGNORED=true
STALE_OBSERVATIONS_REJECTED=true
SAME_TIMESTAMP_VOLUME_NONDECREASING=true
INTERVAL_ROLLOVER=true
CLOSED_CANDLE_IMMUTABILITY=true
```

### PR #5548 — Canonical Record

```text
PR_NUMBER=5548
PR_STATE=MERGED
MERGE_METHOD=SQUASH
MERGE_COMMIT_SHA=6f38df4d833945197e8f472c09f402ee767c85ad
IMPLEMENTATION_HEAD_SHA=7576f2e1158a9365f2a664a5071cfa7dfda35434
EVIDENCE_BUNDLE_HEAD_SHA=c9d3b3839363cd90c8c6b674739baff0ea7cbf85
FINAL_SEAL_TIP_SHA=91b4a79cc1ab2d8c017ccee4567b6e7c9bd48ec1
VALID_EVIDENCE_PATH=evidence/market_dashboard_v2/intrabar_capability/2026-07-25T214037Z
INVALID_HISTORICAL_EVIDENCE_PATH=evidence/market_dashboard_v2/intrabar_capability/2026-07-25T211859Z
EVIDENCE_MANIFEST_SHA256=1cd1dfff96306087e19d5ca5a235664ddcfbef53b3e8740b4d301f0c5cffe085
EVIDENCE_THREE_STAGE_IDENTITY_VALID=true
SELF_REFERENTIAL_SEAL_REQUIRED=false
CONSOLE_LOG_PRESENT_AND_TRACKED=true
MANIFEST_INTERNALLY_CONSISTENT=true
ALL_REQUIRED_CHECKS_PASSED=true
ADMIN_BYPASS=false
PRIMARY_CHECKOUT_UNCHANGED_DURING_CAPABILITY=true
CORE_CHANGED=false
TRADING_LOGIC_CHANGED=false
AUTHORITY_CHANGED=false
RUNTIME_CHANGED=false
ORDERS_CHANGED=false
SCHEDULER_CHANGED=false
CAPITAL_CHANGED=false
```

**Evidence policy:** Only `2026-07-25T214037Z` is valid PR #5548 product evidence. `2026-07-25T211859Z` remains explicitly invalid historical evidence — do not delete, repair, reinterpret, or silently promote it.

### Confirmed merged Landscape V2 capability PRs (non-exhaustive relative to earlier reset era)

```text
#5499 ReadModel contracts/guards (PHASE 2)
#5500 Canonical Landscape V2 runbook ingestion (docs)
#5501 Landscape Shell (PHASE 3)
#5503 Market / Universe / Selected-Instrument binding
#5505 Dynamic Scope lifecycle binding
#5506 Canonical Decision projection binding
#5507 Canonical Double Play projection binding
#5508 Canonical Safety projection binding
#5509/#5510 Economic contract + explicit injection binding
#5511 Diagnostics OPTION_A KEEP_NOT_BOUND ratification
#5512 Autonomy OPTION_D KEEP_NOT_BOUND closeout
#5513/#5514 Product-surface reading-flow hardening
#5515 Source health / freshness compact treatment
#5516 Engineering drawer completion
#5517 Phase 5 TASK_4 timeline DEFERRED ratification
#5518 Accessibility baseline
#5519 Performance measurement evidence
#5520 Bounded durable archive-root contract
#5521 Universe Selection on canonical default path
#5526 OKX universe + selected OHLCV readmodels
#5527 Market dashboard OKX readmodel binding
#5528 Continuous read-only OKX OHLCV refresh
#5548 Authentic OKX Futures intrabar open-candle updates
```

### Phase / capability gate reconciliation (evidence-backed, not mechanical PASS)

```text
PHASE_0_FORMAL_ARTIFACTS=PARTIAL          # dedicated inventory/matrix/gap md files absent; discovery satisfied via later capability work
PHASE_1_SPEC_GATE=PARTIAL                 # landscape IA exists in-repo; OPERATOR_LAYOUT_APPROVAL not an explicit operator product PASS
PHASE_2_READMODEL_FOUNDATION=PASS         # PR #5499
PHASE_3_LANDSCAPE_SHELL=PARTIAL           # PR #5501 technical shell merged; OPERATOR_SKELETON/PRODUCT approval still PENDING
PHASE_4_PRODUCER_BINDINGS=PARTIAL         # market/scope/decision/DP/safety/risk/execution/economic/OKX bound; Cap6 ALT_A presents economic fields + honest diagnostics/autonomy NOT_BOUND
PHASE_4_6C_DIAGNOSTICS=DEFERRED           # OPTION_A KEEP_NOT_BOUND (ratified)
PHASE_4_7_AUTONOMY=DEFERRED               # OPTION_D KEEP_NOT_BOUND (ratified)
PHASE_5_PRODUCT_SURFACE=PASS              # TASK_1/7/8 PASS; TASK_4 DEFERRED non-blocking; OPERATOR_PRODUCT_GATE=true (review SHA 88f2241819dcc160c3ce688a9c7397e7cc8becec)
PHASE_6_AUTONOMY_PARALLEL=OPEN
PHASE_7_PRE_ACTIVATION_OBS=OPEN
PHASE_8_CLOSEOUT=OPEN
TECHNICAL_IMPLEMENTATION_INTRABAR=PASS    # PR #5548
PRODUCT_CAPABILITY_INTRABAR=PASS          # operator-visible open-candle revisions with valid evidence
OPERATOR_ACCEPTANCE_OVERALL=PASS          # Operator Product Review PASS on 88f2241819dcc160c3ce688a9c7397e7cc8becec (post PR #5568); PR #5569 docs-only Anti-SSOT wording did not invalidate
RUNTIME_ACTIVATION=NOT_APPLICABLE_FALSE   # intentionally not activated
```


---

## 1. Unverhandelbarer Systemvertrag

### 1.1 Das Dashboard ist nur Consumer

```text
Canonical Producers
        │
        ▼
Immutable, versionierte Read Models / Snapshots
        │
        ▼
Page Aggregate
        │
        ▼
Presenter
        │
        ▼
Market Landscape UI
```

Es existiert **keine Rückrichtung**.

```text
Market Dashboard
    ├── darf keine Decision erzeugen
    ├── darf keine Direction wählen
    ├── darf keinen Scope verändern
    ├── darf keinen Switch anfordern
    ├── darf keinen Risk-/Sizing-Wert setzen
    ├── darf keinen Order Intent erzeugen
    ├── darf keinen Scheduler starten
    ├── darf keine Promotion auslösen
    ├── darf keinen Gate-Status überschreiben
    └── darf keine Runtime aktivieren
```

### 1.2 Sole Authorities bleiben erhalten

| Domäne | Kanonischer Owner | Dashboard-Rolle |
|---|---|---|
| Market Context | Master V2 / Canonical Market Context | anzeigen |
| Dynamic Scope | Runtime Scope State | anzeigen |
| Bull/Bear & Switch | `transition_state` / Master V2 | anzeigen |
| Double Play | kanonischer Double-Play-Core / Composition | anzeigen |
| Decision | integrierter kanonischer Decision-Core | anzeigen |
| Risk | Risk Authority | anzeigen |
| Capital / Sizing | kanonischer Governance-/Sizing-Pfad | anzeigen |
| Safety / Kill Switch | eigenständige Veto-Domäne | anzeigen |
| Execution Intent | kanonischer Order-Intent-/Execution-Pfad | anzeigen |
| Reconciliation | kanonischer Reconciliation Owner | anzeigen |
| Economic Gate | kanonische Economic Evidence | anzeigen |
| Promotion | Governance-/Promotion-Owner | anzeigen |
| Runtime Activation | Pre-Activation Gate + Operator-GO | anzeigen |
| Vollautonomie | kanonische Autonomy-/Ops-Pipeline | anzeigen |

### 1.3 Fail-closed Darstellung

Fehlt eine Quelle, gilt:

```text
MISSING_SOURCE
NOT_BOUND
UNAVAILABLE
STALE
INVALID_PROVENANCE
SCHEMA_MISMATCH
```

Verboten sind:

```text
- erfundene Werte
- optisch sichere Default-Werte
- statische "alles okay"-Flags
- automatische Dummy-Fallbacks
- UI-seitig rekonstruierte Trading-Entscheidungen
- Zusammenführung widersprüchlicher Quellen zu einer neuen Wahrheit
```

---

## 2. Ausgangslage und ratifizierte Architekturwahrheit

Der aktuelle Architekturstand ist kein Reparaturfall.

```text
CORE_ARCHITECTURE_VALID=true
MASTER_V2_CANONICAL=true
DOUBLE_PLAY_AUTHORITY_VALID=true
DYNAMIC_SCOPE_AUTHORITY_VALID=true
SAFETY_AUTHORITY_VALID=true
OPS_DOUBLE_PLAY_NON_AUTHORITY_CONFIRMED=true
RUNTIME_BOUND_NOT_ACTIVATED_IS_INTENTIONAL=true
STRATEGY_SIGNAL_BLOCK_IS_INTENTIONAL=true
CLASS_A_CONFIRMED_DEFECTS=[]
CORE_CHANGE_REQUIRED=false
RUNTIME_CHANGE_REQUIRED=false
```

Für das Dashboard folgen daraus fünf Konsequenzen:

1. Es darf keinen angeblichen Core-Defekt „reparieren“.
2. Es darf Intentional Locks nicht als Funktionsfehler behandeln.
3. Es muss `BOUND_NOT_ACTIVATED` als gültigen Zustand darstellen.
4. Es muss Projection und Authority explizit unterscheiden.
5. Es darf zukünftige Architekturziele nicht als bereits aktive Funktionen anzeigen.

---

## 3. Zielbild: eine echte Landscape-Symbiose

Das Dashboard ist keine Sammlung loser Kacheln. Es ist ein zusammenhängender Market Workspace.

### 3.1 Primäre Informationsfrage

Die Seite muss innerhalb weniger Sekunden beantworten:

1. Welcher Markt und welches Instrument sind aktuell relevant?
2. Wie bewegt sich der Markt?
3. Was sieht das System?
4. Welche kanonische Entscheidung liegt vor?
5. Warum liegt sie vor?
6. Welche Gates oder Locks verhindern weitere Schritte?
7. Wie frisch, vollständig und belastbar sind die Daten?
8. In welcher Stufe der Research→Shadow→Testnet→Live-/Autonomy-Ladder befindet sich das System?

### 3.2 Landscape-Komposition

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ GLOBAL SYSTEM STRIP                                                         │
│ Instrument · Venue · Scope · Regime · Runtime State · Freshness · Safety    │
├───────────────────┬──────────────────────────────────────┬───────────────────┤
│ UNIVERSE / RANK   │                                      │ SYSTEM CONTEXT    │
│                   │          PRIMARY MARKET CHART         │ Scope             │
│ Watchlist         │                                      │ Regime            │
│ Ranking           │                                      │ Switch State      │
│ Eligibility       │                                      │ Source Health     │
├───────────────────┴──────────────────────────────────────┴───────────────────┤
│ CANONICAL DECISION STRIP                                                     │
│ Decision · Direction · Double Play · Reason Codes · Blockers · Confidence   │
├────────────────────────────┬─────────────────────────────┬───────────────────┤
│ RISK / SIZING / CAPITAL    │ EXECUTION / RECONCILIATION  │ ECONOMIC STATUS   │
│ read-only projection       │ read-only projection        │ evidence only     │
├────────────────────────────┴─────────────────────────────┴───────────────────┤
│ EVENT / DECISION TIMELINE                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ ENGINEERING DRAWER: provenance · schemas · digests · raw codes · diagnostics│
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Produktregeln

- Der Chart dominiert den sichtbaren Bereich.
- Decision und Blocker sind unmittelbar sichtbar.
- Die Oberfläche wirkt wie ein professioneller Market Workspace, nicht wie ein Governance-Bericht.
- Keine imitierte Trading-Funktionalität.
- Keine Buy-/Sell-/Submit-/Arm-/Activate-Schaltflächen.
- Interaktion ist nur lokale Ansicht: Instrument wählen, Panel öffnen, Zeitraum ändern, Details ein-/ausklappen.
- UI-Filter verändern ausschließlich die Darstellung und niemals kanonischen Scope oder Systemzustand.
- Keine mehrfach wiederholten Status-Badges.
- Keine verschachtelten Cards.
- Engineering-Details bleiben erreichbar, dominieren aber nicht das Produkt.

---

## 4. Zielarchitektur und Verdrahtung

### 4.1 Layer-Modell

```text
LAYER A — CANONICAL DOMAIN PRODUCERS
src/trading/master_v2/
src/risk_layer/
src/governance/
src/execution/
src/observability/
src/backtest/
src/research/
src/strategies/                 # nur vorhandene Research-/Signal-Evidence

LAYER B — CANONICAL READ PROJECTIONS
versionierte immutable Snapshots
keine Template-Abhängigkeit
keine Decision-Logik
keine Mutation des Producers

LAYER C — DASHBOARD AGGREGATION
ein Page-Aggregate
validiert Verfügbarkeit, Schema, Provenance und Freshness
keine fachliche Ableitung

LAYER D — PRESENTATION
Display-Formatting, Labels, Einheiten, Sortierung
keine Authority

LAYER E — LANDSCAPE UI
SSR/HTML/CSS und minimaler Client-State
keine Domainlogik
keine Trading-Aktion
```

### 4.2 Import-Richtung

Erlaubt:

```text
webui -> readmodel contracts
webui -> read-only adapters
read-only adapters -> canonical producer outputs
tests -> alle oben genannten Schichten
```

Verboten:

```text
canonical core -> webui
risk/execution/governance -> templates
domain owner -> dashboard presenter
dashboard -> mutable runtime service
dashboard -> order API
dashboard -> scheduler API
dashboard -> activation endpoint
```

### 4.3 Kanonische Snapshot-Familie

Die endgültigen Namen müssen gegen den realen Repo-Bestand geprüft werden. Die Semantik ist verbindlich, konkrete Dateinamen sind bei Discovery zu ratifizieren.

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping, Sequence


class Availability(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_BOUND = "NOT_BOUND"
    MISSING_SOURCE = "MISSING_SOURCE"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class SnapshotProvenanceV1:
    schema_id: str
    schema_version: str
    producer_module: str
    generated_at: datetime
    effective_at: datetime | None
    source_kind: str
    source_reference: str | None
    evidence_digest: str | None
    git_sha: str | None
    availability: Availability


@dataclass(frozen=True)
class CanonicalDecisionSnapshotV1:
    instrument_id: str
    decision: str
    direction: str
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]
    decision_id: str | None
    provenance: SnapshotProvenanceV1


@dataclass(frozen=True)
class MarketDashboardPageSnapshotV1:
    market: object
    universe: object
    scope: object
    decision: CanonicalDecisionSnapshotV1 | None
    double_play: object
    risk_sizing: object
    execution: object
    economic: object
    autonomy: object
    diagnostics: object
    source_health: Mapping[str, Availability]
    generated_at: datetime
```

Diese Strukturen sind illustrativ. Cursor darf sie nicht blind implementieren. Vor Implementierung muss geprüft werden, ob äquivalente versionierte Contracts bereits existieren.

### 4.4 Adapter-Vertrag

Ein Adapter ist nur Projektion:

```python
def project_decision_evidence(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> CanonicalDecisionSnapshotV1:
    """Pure read-only projection.

    Verboten:
    - Decision neu berechnen
    - Direction ändern
    - fehlende Reason Codes erfinden
    - Blocker aus anderen Quellen ergänzen
    - Runtime-Zustand verändern
    """
```

### 4.5 Page-Composition-Vertrag

```python
class MarketDashboardReadService:
    def load_page_snapshot(self) -> MarketDashboardPageSnapshotV1:
        """Load and validate immutable projections only."""
```

Die Route konsumiert genau diesen Service beziehungsweise einen im Repo bereits kanonischen äquivalenten Aggregate-Owner.

```python
@router.get("/market")
def market_dashboard() -> Response:
    page = read_service.load_page_snapshot()
    context = presenter.present(page)
    return render_template("market_landscape.html", **context)
```

Keine Domain-Funktion darf in Route oder Presenter aufgerufen werden, um eine Entscheidung zu erzeugen.

---

## 5. Phasenmodell

## PHASE 0 — Ratifikation, Scope Freeze und Repo Discovery

### Zweck

Den realen Repo-Zustand gegen dieses Runbook prüfen, ohne Code zu ändern.

### Aufgaben

1. Aktuellen `main`-/`origin&#47;main`-Stand, offene PRs und Worktree prüfen.
2. Kanonische Map of Truth, Runbooks und Architektur-Ratifikationen identifizieren.
3. Bestehende `/market`-Route, WebUI-Pakete, Templates und Tests inventarisieren.
4. Prüfen, ob das frühere Dashboard weiterhin gelöscht/404 ist oder neue Surface-Fragmente existieren.
5. Alle vorhandenen Market-, Decision-, Double-Play-, Risk-, Execution-, Economic-, Diagnostics- und Autonomy-ReadModels erfassen.
6. Für jedes sichtbare Zielfeld einen Producer, Contract und Availability-Status zuordnen.
7. Alte Dashboard-Runbooks nur als historische Designreferenz klassifizieren.
8. Einen `CURRENT_STATE`-Block erzeugen.
9. Keine Implementierung.

### Pflichtartefakte

```text
docs/ops/market_dashboard/
  MARKET_DASHBOARD_CURRENT_STATE_INVENTORY_V2.md
  MARKET_DASHBOARD_OWNER_AND_SOURCE_MATRIX_V2.md
  MARKET_DASHBOARD_GAP_CLASSIFICATION_V2.md
```

### Gate

```text
PHASE_0_PASS=true
CORE_CHANGE_REQUIRED=false
RUNTIME_CHANGE_REQUIRED=false
CURRENT_ROUTE_KNOWN=true
SOURCE_OWNER_MATRIX_COMPLETE=true
UNMAPPED_VISIBLE_FACT_COUNT=0
```

`UNMAPPED_VISIBLE_FACT_COUNT=0` bedeutet: Ein Feld ohne Quelle darf geplant werden, aber nur als `NOT_BOUND`/`MISSING_SOURCE`.

### Hard Stops

- unerklärter Worktree-Diff
- widersprüchliche Authority-Owner
- Versuch, Core-Semantik im Dashboard-Workstream zu ändern
- Versuch, Runtime-Aktivierung abzuleiten
- Versuch, eine historische Dashboard-Datei zur neuen SSOT zu erklären

---

## PHASE 1 — Kanonische Dashboard-Spezifikation

### Zweck

Die neue Surface vollständig spezifizieren, bevor produktive UI gebaut wird.

### Aufgaben

1. Informationsarchitektur des Landscape-Layouts definieren.
2. Visible Fact Registry erstellen.
3. Für jedes Feld festlegen:
   - Label
   - kanonischer Producer
   - Snapshot/Schema
   - Aktualisierungsfrequenz
   - Freshness-Grenze
   - Missing-State
   - Authority-Klasse
   - primäre/sekundäre Platzierung
4. Interaction Policy festlegen.
5. Verbotene Controls und Endpoints festhalten.
6. Viewport-Ziele und Above-the-Fold-Kriterien definieren.
7. Operator-Abnahmekriterien definieren.
8. Keine Domain- oder Runtime-Implementierung.

### Visible Fact Registry — Beispiel

| Visible Fact | Producer | Authority | Missing-State | Position |
|---|---|---:|---|---|
| Selected Instrument | Scope/Universe Projection | canonical projection | `NOT_BOUND` | Header |
| Market Price | Market Data ReadModel | data fact | `STALE`/`MISSING` | Chart |
| Decision | Master V2 Decision Evidence | canonical | `NOT_BOUND` | Decision Strip |
| DP Composition | Canonical Double Play Evidence | canonical | `NOT_BOUND` | Decision Strip |
| Runtime State | Runtime Bridge State | canonical status | `MISSING` | Header |
| Kill Switch | Safety Authority | veto authority | `MISSING` | Header/Risk |
| Economic Gate | Economic Evidence | promotion-only | `MISSING` | Secondary |
| Autonomy Stage | NONE (OPTION_D; docs-only ladder; no productive aggregate) | non-source / NOT_BOUND | `NOT_BOUND` | Secondary |

### Gate

```text
PHASE_1_PASS=true
VISIBLE_FACT_REGISTRY_COMPLETE=true
UNSOURCED_FACTS_RENDER_AS_MISSING=true
WRITE_CAPABILITY_COUNT=0
DOMAIN_LOGIC_IN_UI_SPEC=false
OPERATOR_LAYOUT_APPROVAL=true
```

---

## PHASE 2 — ReadModel Foundation und Source Health

### Zweck

Ein fail-closed, versioniertes Consumer-Fundament bauen.

### Aufgaben

1. Bestehende Contracts bevorzugen; Duplikate vermeiden.
2. Fehlende Dashboard-Projektionen als read-only Adapter ergänzen.
3. Provenance und Freshness vereinheitlichen.
4. `UnavailableSnapshot`-/Availability-Semantik bereitstellen.
5. Serialization- und Schema-Tests ergänzen.
6. Import-Boundary-Tests ergänzen.
7. Source-Health-Aggregat bereitstellen.
8. Noch keine finale Produkt-Surface.

### Mindestcontracts

```text
MarketInstrumentSnapshot
UniverseRankingSnapshot
DynamicScopeSnapshot
CanonicalDecisionSnapshot
DoublePlaySnapshot
RiskSizingCapitalSnapshot
SafetyAuthoritySnapshot
ExecutionReconciliationSnapshot
EconomicSummarySnapshot
AutonomyStageSnapshot
DiagnosticsSummarySnapshot
DashboardSourceHealthSnapshot
```

### Gate

```text
PHASE_2_PASS=true
READMODEL_CONTRACT_TESTS_PASS=true
PROVENANCE_COMPLETE=true
IMMUTABILITY_PASS=true
SILENT_DEFAULT_COUNT=0
DUPLICATE_TRUTH_OWNER_COUNT=0
FORBIDDEN_IMPORT_COUNT=0
```

### Nicht erlaubt

- Core-Modelle nur für UI-Komfort verändern
- Decision-Evidence nachbauen
- bestehende Authority abstrahieren und dabei semantisch verändern
- Live-/Order-/Scheduler-Abhängigkeit hinzufügen

---

## PHASE 3 — Landscape Shell und Product Skeleton

### Zweck

Die neue visuelle Komposition bauen, bevor alle Daten gebunden sind.

### Warum diese Phase vor Vollautonomie kommt

Die Shell validiert früh:

- Informationshierarchie
- benötigte ReadModels
- Platzbedarf
- Missing-State-UX
- Operator-Verständlichkeit
- Browser-/Viewport-Verhalten

Sie darf jedoch noch keine fehlenden Daten simulieren.

### Aufgaben

1. Neue `/market`-Landscape-Shell anlegen.
2. Ein zusammenhängendes CSS-Grid/Flex-Layout verwenden.
3. Primary Chart Workspace, Decision Strip, Secondary Rails und Engineering Drawer vorsehen.
4. Verfügbare Sources real anbinden.
5. Noch fehlende Sources ehrlich als `NOT_BOUND` darstellen.
6. Kein Mock-/Dummy-Datenpfad auf der produktiven Route.
7. Real-Chrome-Screenshots erzeugen.
8. Operator Product Review durchführen.

### Gate

```text
PHASE_3_PASS=true
MARKET_ROUTE_200=true
LANDSCAPE_COMPOSITION=true
PRIMARY_CHART_ABOVE_FOLD=true
CARD_WALL=false
NO_ORDER_CONTROLS=true
NO_FAKE_DOMAIN_DATA=true
MISSING_STATE_UX_PASS=true
CHROME_TECHNICAL_PASS=true
OPERATOR_SKELETON_APPROVAL=true
```

---

## PHASE 4 — Kanonische Producer-Bindung

### Zweck

Die Shell schrittweise mit echten Systemprojektionen füllen.

### Bindungsreihenfolge

#### 4.1 Markt und Universe

- Futures-only Instrumente
- OKX-Provenance
- Ranking
- Eligibility
- Selected Instrument
- OHLCV
- Freshness

#### 4.2 Dynamic Scope und Market Context

- Scope-Zustand
- Regime
- Bull/Bear-Kontext
- Scope-Wechsel
- Switch-State
- keine UI-seitige Ableitung

#### 4.3 Canonical Decision und Double Play

- Decision Outcome
- Direction
- Reason Codes
- Composition
- Blocker
- Pending-/Armed-Projektion nur so anzeigen, wie der kanonische Contract sie liefert

#### 4.4 Safety, Risk, Capital und Sizing

- Rollen getrennt beschriften
- kombinierte Offline-Implementierung nicht als Owner-Verschmelzung darstellen
- Kill Switch und Veto klar kennzeichnen
- keine Handlungsschaltflächen

#### 4.5 Execution und Reconciliation

- Intent-/Pipeline-Status
- Fill-/Roundtrip-/Reconciliation-Status
- Unknown Outcome
- Runtime-Lock
- ausschließlich read-only

#### 4.6 Economic, Research und Diagnostics

##### 4.6A — Economic Dashboard Contract Ratification (RATIFIED)

Canonical owners (separate):

```text
CANONICAL_ECONOMIC_OWNER=backtest.economic_viability_evidence_v1
CANONICAL_ECONOMIC_CONTRACT=EconomicViabilityEvidenceV1
CANONICAL_ECONOMIC_SCHEMA_VERSION=v1
CANONICAL_PROMOTION_OWNER=governance.promotion_loop.promotion_economic_gate_v1
ECONOMIC_AND_PROMOTION_SEPARATE=true
```

**A_STATUS — RATIFIED**

- Terminal economic outcome projects from `EconomicViabilityEvidenceV1.status`.
- Dashboard contract field: `economic_viability_status` (exact enum value).
- Forbidden contract field for this value: `economic_gate_status`.
- Do not map to `promotion_economic_gate_v1` or infer promotion eligibility.
- `economic_validity_proven` and `policy_threshold_status` remain distinct direct fields.

**B_SELECTOR — RATIFIED AS EXPLICIT INJECTION ONLY**

- Selection owner: `UPSTREAM_NOT_MARKET_DASHBOARD`.
- Dashboard must never discover or choose among repository evidence instances.
- Zero injected candidate → `availability=NOT_BOUND`.
- Exactly one valid injected candidate → field-for-field projection after validation.
- More than one injected candidate → fail closed `INVALID` +
  `AMBIGUOUS_ECONOMIC_EVIDENCE_SOURCE`.
- Invalid schema/digest/manifest/owner/contract → fail closed `INVALID`,
  no partial economic facts.

**C_LIFECYCLE — RATIFIED ABSENT**

Intentionally absent from `EconomicSummarySnapshotV1` for Phase 4.6B:

- `DEVELOPMENT_ONLY`, `HOLDOUT`, `SEALED_LONG_PANEL`, `TERMINAL`,
  `PREREGISTRATION_ONLY`, `NOT_EVALUATED`

Missing lifecycle context is not an error until a later independent context
contract is separately ratified.

**D_CONTRACT — RATIFIED MINIMAL DIRECT PROJECTION**

`EconomicSummarySnapshotV1` fields (plus existing availability/provenance envelope):

```text
economic_viability_status
economic_validity_proven
profitability_claim_allowed
policy_threshold_status
policy_version
authority_effect
runtime_effect
order_effect
reason_codes
profit_factor
net_return
max_drawdown
sharpe
trade_count
funding_drag
evidence_ref
contract_version
owner
strategy_id
strategy_version
config_digest
implementation_digest
data_digest
manifest_digest
wiring_chain_digest
policy_digest
```

Rules: direct copy only; no recomputation; no promotion/research-workflow/
risk-capital-sizing fields; optional source absences remain absent/None.

##### 4.6B — Economic Explicit Injection Binding (RATIFIED separately)

- Explicit injection binding of one EconomicViabilityEvidenceV1 instance
- keine Anlageempfehlung
- Lifecycle context only after separate ratification

##### 4.6C — Diagnostics Summary Contract Architecture Ratification (RATIFIED OPTION A)

```text
PHASE=PHASE_4_6C_DIAGNOSTICS_SUMMARY_CONTRACT_ARCHITECTURE_RATIFICATION
RATIFY_OPTION_A_KEEP_NOT_BOUND=true
DIAGNOSTICS_SUMMARY_STATUS=NOT_BOUND
SOLE_DIAGNOSTICS_OWNER=UNRESOLVED
IMPLEMENTATION_AUTHORIZED=false
TYPED_INJECTION_BOUNDARY_AUTHORIZED=false
SUMMARY_PRODUCER_EVIDENCE_RATIFIED=false
CONSUMER_CONTRACT_REDESIGN_REQUIRED=true
WORKFLOW_DASHBOARD_READMODEL_V1=NON_SOURCE_PROJECTION_ONLY
OPTION_B_NEW_DOMAIN_NEUTRAL_DIAGNOSTICS_EVIDENCE=REJECTED
OPTION_D_SOURCE_HEALTH_ONLY=REJECTED
OPTION_C_MULTIPLE_DOMAIN_SPECIFIC_DIAGNOSTICS=DEFERRED_SEPARATE_OPERATOR_AUTHORIZED_REDESIGN
```

**A_STATUS — RATIFIED KEEP NOT_BOUND**

- `diagnostics_summary` remains `NOT_BOUND`.
- Sole owner remains `UNRESOLVED`.
- No diagnostics producer, adapter, typed injection boundary, or evidence
  contract is authorized by this decision.
- `DiagnosticsSummarySnapshotV1` MUST NOT be bound to
  `WorkflowDashboardReadModelV1`.
- `WorkflowDashboardReadModelV1` remains `NON_SOURCE` / `PROJECTION_ONLY`.
- `summary` is not ratified as producer-owned evidence; treat as
  unresolved/presenter-oriented semantics until a separate consumer-contract
  redesign is ratified.
- No inference, cross-source aggregation, archive selection, or free-text
  evidence generation is permitted.

**REJECTED / DEFERRED**

- OPTION_B (new domain-neutral diagnostics evidence): explicitly rejected.
- OPTION_D (source-health only): explicitly rejected.
- OPTION_C (multiple domain-specific diagnostics): architecturally admissible
  only as a future separately authorized surface-and-contract redesign phase;
  not part of this closeout.

Canonical owner registry note:
`src/webui/market_dashboard_landscape_v2/owner_registry.py` slot
`diagnostics_summary` → `reuse_status=NOT_BOUND`, `owner=UNRESOLVED`.

#### 4.7 Autonomy State — Architecture Ratification Closeout (RATIFIED OPTION D)

```text
PHASE=PHASE_4_7B_AUTONOMY_OPTION_D_CLOSEOUT
PHASE_4_7A_RATIFIED_OPTION_D=true
RATIFY_OPTION_D_NO_CANONICAL_AGGREGATE_REQUIRED=true
AUTONOMY_STAGE_BINDING_STATUS=NOT_BOUND
AUTONOMY_AGGREGATE_REQUIRED=false
AUTONOMY_BINDING_COMPLETE_BY_EXPLICIT_NOT_BOUND=true
SOLE_AUTONOMY_OWNER=NONE
SOLE_AUTONOMY_PRODUCER=NONE
SOLE_AUTONOMY_CONTRACT=NONE
SOURCE_TYPE=DOCS_ONLY
AUTHORITY_EFFECT=NONE
STAGE_LADDER_PRODUCTIVE_OR_DOCS_ONLY=DOCS_ONLY
CROSS_SOURCE_SYNTHESIS_AUTHORIZED=false
WORKFLOW_DASHBOARD_READMODEL_V1=NON_SOURCE
DASHBOARD_CAN_BE_OWNER=false
BINDING_AUTHORIZED=false
PRODUCER_CREATION_AUTHORIZED=false
CONTRACT_CREATION_AUTHORIZED=false
ADAPTER_CREATION_AUTHORIZED=false
DASHBOARD_INJECTION_AUTHORIZED=false
```

**D_STATUS — RATIFIED NO CANONICAL AGGREGATE; KEEP NOT_BOUND**

- `autonomy_stage` remains explicitly `NOT_BOUND`.
- Phase 4.7 does **not** require a canonical unified Autonomy-State aggregate.
- Autonomy stages 0–7 remain **docs-only informative review vocabulary**
  (roadmap §3.1 / Runtime Lane Taxonomy §12). They are **not** productive
  operational state.
- Autonomy stage is **not** runtime bridge status (`BOUND_NOT_ACTIVATED` /
  `CANONICAL_RUNTIME_ENTRYPOINT_STATUS` remain a separate Runtime State fact).
- Autonomy stage is **not** promotion eligibility, scheduler status, worker/
  job status, safety veto, capital authorization, operator-GO, or live
  authorization.
- Separate canonical facts may be displayed only through their own
  independently ratified source families.
- No cross-source synthesis into an Autonomy state is allowed.
- `WorkflowDashboardReadModelV1` remains `NON_SOURCE`.
- The Market Dashboard cannot own or infer Autonomy state.
- No Autonomy producer, contract, adapter, projection helper, or dashboard
  injection is authorized by this closeout.

**Product intent (unchanged, not binding under OPTION_D)**

Operators may still *want* a future coherent Autonomy readout. Under OPTION_D
that intent stays aspirational / `NOT_BOUND` until a separate, explicitly
authorized architecture decision supersedes this closeout. Do **not** calculate
a next permissible stage, synthesize gate results into one ladder state, or treat
Runtime Bridge / Pre-Activation / Promotion / Scheduler / Worker / Operator-GO
as inputs to one Autonomy aggregate.

Canonical owner registry note:
`src/webui/market_dashboard_landscape_v2/owner_registry.py` slot
`autonomy_stage` → `reuse_status=NOT_BOUND`, `owner=NONE`, `source&#47;contract=NONE`.

### Gate pro Bindung

```text
SOURCE_EXISTS=true
SOURCE_CANONICAL_OR_RATIFIED_PROJECTION=true
PROVENANCE_PASS=true
FRESHNESS_PASS_OR_VISIBLE_STALE=true
NO_RECOMPUTATION=true
NO_MUTATION=true
TESTS_PASS=true
```

### Abschlussgate

```text
PHASE_4_PASS=true
CANONICAL_MARKET_BOUND=true
CANONICAL_SCOPE_BOUND=true
CANONICAL_DECISION_BOUND=true
CANONICAL_DOUBLE_PLAY_BOUND=true
CANONICAL_SAFETY_BOUND=true
CANONICAL_EXECUTION_STATE_BOUND=true
ECONOMIC_SINGLE_SOURCE_BOUND=true
AUTONOMY_STATE_BOUND_OR_NOT_BOUND_VISIBLE=true
```

---

## PHASE 5 — Product Surface V1

### Zweck

Aus dem Skeleton eine belastbare tägliche Operator-Surface machen.

### Aufgaben

1. Visuelle Dichte optimieren.
2. Redundanzen entfernen.
3. Decision → Why → Blocker als primären Lesefluss schärfen.
4. Timeline für Zustandsübergänge ergänzen.
   — **DEFERRED** (explicit operator ratification; see § Phase 5 TASK_4 below).
5. Source-Health und Freshness kompakt machen.
6. Engineering Drawer vervollständigen.
7. Tastatur-/Fokus- und Accessibility-Basis prüfen.
8. Performance messen.
9. SSR-/Client-Hydration-Komplexität minimal halten.
10. Kein aktiver Trading-Workflow.

### Qualitätsziele

```text
FIRST_MEANINGFUL_CONTENT_FAST=true
NO_HORIZONTAL_OVERFLOW=true
NO_BLANK_PRIMARY_WORKSPACE=true
DUPLICATE_STATUS_RENDERINGS=0
PRIMARY_FACTS_UNDERSTOOD_WITHIN_SECONDS=true
ENGINEERING_DETAIL_AVAILABLE_BUT_SECONDARY=true
```

### Gate

```text
PHASE_5_PASS=true
TECHNICAL_PRODUCT_GATE=true
OPERATOR_PRODUCT_GATE=true
DAILY_OBSERVATION_USABLE=true
```

The Gate block above remains the Phase-5 product closeout **definition**.
Current-state recording (not a rewrite of historical TASK_* ratifications): after
the Operator Product Review on exact `origin/main` commit
`88f2241819dcc160c3ce688a9c7397e7cc8becec` (post PR #5568), these criteria are
`true` for the read-only daily observation surface. TASK_4 timeline remains
DEFERRED / honest `NOT_BOUND` and non-blocking. PR #5569 later merged docs-only
Consumer / Anti-SSOT wording on `9ff632885422a92e86f9dbeda79aab160bf2346b` and
did not change product/runtime behavior or invalidate that review.

### TASK_4 — State-Transition Timeline Explicit Phase-5 Deferral (RATIFIED)

```text
PHASE=PHASE_5_TASK_4_STATE_TRANSITION_TIMELINE_DEFERRAL_RATIFICATION
OPERATOR_DECISION=B_EXPLICIT_PHASE_5_DEFERRAL
PERMANENT_NOT_APPLICABLE=false
TASK_4_STATE_TRANSITION_TIMELINE=DEFERRED
TASK_4_PHASE_5_BLOCKING=false
TASK_4_IMPLEMENTED=false
TASK_4_PERMANENTLY_NOT_APPLICABLE=false
TIMELINE_SOURCE_AVAILABLE=false
TIMELINE_SOURCE_REGISTERED=false
TIMELINE_UI_STATE=NOT_BOUND
CURRENT_TIMELINE_EVENT_COUNT=0
CANONICAL_TIMELINE_SOURCE_EXISTS=false
INVENTED_HISTORY_ALLOWED=false
RECONSTRUCTED_HISTORY_ALLOWED=false
FUTURE_PRODUCER_WORK_AUTHORIZED=false
SEPARATE_OPERATOR_GO_REQUIRED=true
PHASE_5_PASS=false
```

**Phase-5 product obligation**

- Display canonical timeline history only if a valid durable source exists.
- Without such a source, the Landscape MUST keep the honest `NOT_BOUND`
  placeholder and MUST NOT invent, reconstruct, or synthesize events.

**Current repository truth**

- No eligible durable canonical state-transition / decision-event producer
  exists for Market Dashboard Landscape V2.
- `CanonicalTradingDecisionEvidenceV1`, Double Play display snapshots,
  `RuntimeScopeState`, and `transition_state` / `TransitionDecision` are
  current-state or single-step semantics — not durable ordered history.
- Replay projections, live execution timelines, diagnostics, engineering
  drawer slots, source-health rows, reason-code arrays, browser-local
  history, and polling-derived diffs are ineligible timeline sources.
- Owner registry has no `event_decision_timeline` slot; presenter keeps
  `timeline.availability=NOT_BOUND` and `events=[]`.

**Current Phase-5 resolution**

- `TASK_4_STATE_TRANSITION_TIMELINE=DEFERRED` (not PASS; not permanent
  NOT_APPLICABLE).
- After this explicit operator deferral, TASK_4 does **not** block Phase-5
  technical closeout.
- Other Phase-5 gaps remain independently open (including visual density,
  performance measurement, and the operator product gate). TASK_7 keyboard /
  focus accessibility baseline is implemented (see § TASK_7 below).
- The existing UI `NOT_BOUND` placeholder remains the required fail-closed
  representation.

**Future work (not authorized by this ratification)**

- A separate producer-side durable-history workstream may be proposed later.
- It requires a separate operator GO and must define canonical owner, event
  semantics, ordering, timestamps, persistence, retention, provenance,
  schema versioning, and a read-only projection.
- Dashboard remains consumer-only.
- This ratification does **not** authorize producer creation, persistence,
  event schemas, Landscape binding, or any Core/Runtime/Strategy/Execution
  change.

### TASK_7 — Keyboard / Focus / Accessibility Baseline (IMPLEMENTED)

```text
PHASE=PHASE_5_TASK_7_KEYBOARD_FOCUS_ACCESSIBILITY_BASELINE
TASK_7_STATE=PASS
TASK_7_IMPLEMENTED=true
TASK_4_STATE_TRANSITION_TIMELINE=DEFERRED
PHASE_5_PASS=false
OPERATOR_PRODUCT_GATE=false
```

**Established facts (this slice)**

- Single page-level `<h1>` (`Market Landscape`) in the Global System Strip.
- Nested `<main>` removed from the Landscape template; `base.html` owns the
  sole page `<main>` landmark. Region landmarks remain via `<header>` /
  `<aside>` / `<section>` / native `<details>` plus `data-mdl-region` markers.
- Interactive surface is native-only: app-chrome home `<a>` and Engineering
  Drawer `<details>`/`<summary>` (Enter/Space native; Escape closes and
  restores focus to `summary`).
- No positive `tabindex`, no clickable `div`/`span` controls, no write /
  order / activation controls.
- Visible `:focus-visible` ring (2px `#7dd3fc`, offset 3px); universal CSS
  reset no longer suppresses `outline` globally.
- Closed Engineering Drawer content is not keyboard-focusable; read-only
  Decision / Why / Blockers / Source Health / Safety rows stay non-focusable.
- Instrument / watchlist remain server-rendered read-only facts — no local
  selection control exists in this surface (nothing invented for a11y theater).
- No Landscape CSS transitions/animations → reduced-motion treatment
  `NOT_APPLICABLE` (no new animation introduced).

**Tests / evidence**

- `tests/webui/test_market_landscape_dashboard_v2_accessibility_baseline_v0.py`
- Existing shell-route + architecture-guard suites remain green.
- Evidence pack: `evidence/market_dashboard_v2/phase5/task7_accessibility/`

**Unresolved / still open for Phase 5 (pre-TASK_8 closeout note superseded below)**

- Operator product gate remains false; Phase 5 remains incomplete until
  TASK_1 + operator product gate.
- TASK_4 timeline remains `DEFERRED`.

### TASK_8 — Performance Measurement (MEASURED)

```text
PHASE=PHASE_5_TASK_8_PERFORMANCE_MEASURED
TASK_8_STATE=PASS
TASK_8_IMPLEMENTED=true
TASK_4_STATE=DEFERRED
PHASE_5_PASS=false
OPERATOR_PRODUCT_GATE=false
PERFORMANCE_BUDGET_RATIFIED=false
CHROME_REVIEW_STATUS=PARTIAL
STALE_PID_ONLY_BLOCKER=true
```

**Established facts (this slice — measurement only, no production mutation)**

- Exact base SHA `c48a020547c4343bdaf67cf7134daa80ef9b8253` (main == origin/main).
- GET `/market` HTML response ~49537 bytes (TestClient); page-owned static
  `market_dashboard_landscape_v2.css` 12057 + `.js` 832 = 12889 bytes;
  shared base CSS also loaded (~98KB on disk); no duplicate asset loading;
  no source maps / dev payloads exposed on page assets.
- Bounded in-process route timing (warmup 5, n=30): p50 ~1.1ms, p95 ~1.4ms,
  status/byte consistent; **not** a ratified production budget.
- Real Chrome Playwright (`channel=chrome` 150.x) route-fulfill metrics on
  1512x982 and 1920x1080 (3 runs each, cache disabled via CDP): DCL/load
  ~50–70ms local, FCP/LCP ~84–96ms, CLS 0, long tasks 0, 6 requests,
  ~160670 fulfilled bytes, 678 DOM nodes; primary workspace visible; chart
  container non-empty; no horizontal overflow; no console/page/network errors.
- Canonical `review_server.sh status` remains `STALE_PID` — diagnosed only,
  **not** auto-repaired; Chrome review path therefore PARTIAL while Playwright
  Real Chrome measurements remain valid evidence.
- Client JS is a tiny presentation IIFE: no hydration framework, no timers/
  polling, no network/write calls → `CLIENT_COMPLEXITY_CLASS=PASS`.
- No numeric performance budget invented; descriptive classification only.

**Tests / evidence**

- Relevant shell / architecture / accessibility / chrome-evidence / contracts /
  tombstone suites green (67 passed).
- Evidence pack: `evidence/market_dashboard_v2/phase5/task8_performance/`

**Unresolved / still open for Phase 5**

- Operator product gate remains false; Phase 5 remains incomplete until
  independent operator product review.
- TASK_4 timeline remains `DEFERRED`.
- Canonical review-server STALE_PID remains an operator/infra follow-up
  outside this measurement slice.

### TASK_1 — Visual Density Optimized (IMPLEMENTED)

```text
PHASE=PHASE_5_TASK_1_VISUAL_DENSITY_OPTIMIZED
TASK_1_STATE=PASS
TASK_1_IMPLEMENTED=true
TASK_4_STATE_TRANSITION_TIMELINE=DEFERRED
PHASE_5_PASS=false
TECHNICAL_PRODUCT_GATE=true
OPERATOR_PRODUCT_GATE=false
CAPABILITY=MARKET_DASHBOARD_PRODUCT_MATURITY_AND_CHROME_EVIDENCE_V1
```

**Established facts (this slice — presentation only)**

- Tighter Landscape spacing (strip/workspace/decision/ops/gov/timeline) without
  introducing card borders or structural divider lines.
- Unavailable Risk / Execution / Economic detail cells render as em-dash while
  the column summary retains the single canonical availability label and reason
  codes — no repeated MISSING_SOURCE badges on every detail field.
- Decision → Why → Blockers primary reading flow, Source Health compact rows,
  Engineering Drawer, keyboard/focus baseline, and honest Timeline `NOT_BOUND`
  remain intact.
- No producer, authority, runtime, order, or domain recomputation changes.

**Tests / evidence**

- Shell-route density guard + existing Landscape owner suites.
- Evidence pack: `evidence/market_dashboard_v2/capability7_product_maturity/`

---

## PHASE 6 — Parallelisierung mit Vollautonomie

### Zweck

Dashboard und Autonomie sauber zusammenführen, ohne dass das Dashboard die Autonomie besitzt.

### Grundregel

Neue Autonomiekomponenten liefern eigene kanonische Status-/Evidence-Snapshots. Das Dashboard konsumiert sie erst danach.

```text
Autonomy Producer
      │
      ▼
Versioned State/Evidence Snapshot
      │
      ▼
Dashboard Adapter
      │
      ▼
Landscape Projection
```

### Dashboard-seitig darstellbare Autonomieinformationen

- aktuelle Ladder-Stufe
- Gate-Ergebnisse
- Scheduler-Status
- Worker-/Job-Status
- letzte erfolgreiche Pipeline
- Fehler-/Retry-Zustände
- Promotion Eligibility
- Activation Lock
- Operator-GO erforderlich
- Runtime Bridge Status

### Verboten

- Scheduler aus UI starten
- Jobs retryen
- Promotion bestätigen
- Runtime armen
- Tokens eingeben
- Kapital freigeben
- Live aktivieren

Diese Funktionen gehören auch später nicht in das reine Market Dashboard.

### Gate

```text
PHASE_6_PASS=true
AUTONOMY_PROJECTIONS_READ_ONLY=true
AUTONOMY_COMMAND_ENDPOINT_COUNT=0
DASHBOARD_AUTHORITY_COUNT=0
BOUND_NOT_ACTIVATED_RENDERED_CORRECTLY=true
```

---

## PHASE 7 — Pre-Activation Observability Readiness

### Zweck

Vor jeder separaten Runtime-Aktivierungsentscheidung prüfen, ob das Dashboard das System ausreichend transparent darstellt.

Diese Phase autorisiert keine Aktivierung.

### Muss sichtbar sein

- Runtime Bridge State
- Pre-Activation Gate
- Safety/Kill Switch
- Authority Boundary
- Scope/Decision/Double-Play-Kette
- Risk/Sizing-/Capital-Projektion
- Execution Mode
- Reconciliation Health
- Source Freshness
- Unknown/Missing/Invalid States
- Audit-/Evidence-Verweise
- aktuelle Autonomy-Stufe

### Gate

```text
PHASE_7_PASS=true
OBSERVABILITY_COVERAGE_COMPLETE=true
UNKNOWN_STATES_VISIBLE=true
FAIL_CLOSED_STATES_VISIBLE=true
NO_ACTIVATION_FROM_UI=true
RUNTIME_STILL_NOT_ACTIVATED=true
SEPARATE_OPERATOR_GO_REQUIRED=true
```

---

## PHASE 8 — Stabilisierung, Closeout und Dauerbetrieb

### Zweck

Die neue Surface als kanonischen Consumer abschließen.

### Aufgaben

1. Alte Dashboard-Fragmente und historische Route-Bindungen inventarisieren.
2. Nur nach separatem bounded Cleanup-GO löschen oder archivieren.
3. Truth Map / Docs-Navigation aktualisieren.
4. Owner-Map aktualisieren.
5. Static Guards dauerhaft machen.
6. Screenshot-/Route-/Contract-Regressionssuite etablieren.
7. Dieses Runbook mit finalen Pfaden und tatsächlichen Schemanamen aktualisieren.
8. Handover-Block und aktuellen Zustand fortschreiben.

### Definition of Done

```text
MARKET_DASHBOARD_CANONICAL_CONSUMER=true
LANDSCAPE_PRODUCT_SURFACE=true
TRADING_CORE_UNCHANGED=true
RUNTIME_AUTHORITY_UNCHANGED=true
NO_UI_DOMAIN_LOGIC=true
NO_UI_WRITE_PATH=true
NO_ORDER_CONTROLS=true
NO_DUMMY_PRODUCTION_DATA=true
NO_DUPLICATE_FACT_OWNER=true
PROVENANCE_COMPLETE=true
MISSING_DATA_FAIL_CLOSED=true
CHROME_REGRESSION_PASS=true
OPERATOR_PRODUCT_APPROVAL=true
DOCS_SSOT_UPDATED=true
```

---

## 6. Capability-PR-Strategie

Jeder PR bildet eine vollständige Capability mit klarer Definition of Done.
Historische Planungsnamen „PR 0…8“ unten sind **Capability-Ziele**, keine Aufforderung zu Micro-Slices.
Micro-Slices und Draft-PRs sind grundsätzlich untersagt, sofern der Operator sie nicht ausdrücklich verlangt.

### Verbindliche Capability-Regeln

```text
CAPABILITY_PR_ONLY=true
MICRO_PR_ALLOWED=false
DRAFT_PR_ALLOWED_ONLY_IF_OPERATOR_REQUESTS=true
EACH_PR_HAS_DEFINITION_OF_DONE=true
EACH_PR_DELIVERS_OPERATOR_VISIBLE_VALUE=true
NO_ARTIFICIAL_SLICE_SPLITTING=true
MERGE_WHEN_CAPABILITY_COMPLETE=true
```

Eine Capability darf mehrere Producer, ReadModels, Adapter, Tests, Dokumentation und UI-Anteile umfassen, sofern sie gemeinsam eine fachlich abgeschlossene Fähigkeit liefern. Eine künstliche Zerlegung ausschließlich zur Erhöhung der PR-Anzahl ist unzulässig.
Standing offline GO darf **eine** vollständige, nicht-aktivierende Capability PR abdecken. Draft PR ist verboten, außer der Operator fordert Draft ausdrücklich.

### Capability-Ziele (historische Planungsnamen beibehalten; Status laut Ledger)

```text
Capability 0 Discovery & Architektur-Ratifikation — PARTIAL/effective via later work
Capability 1 Read-only Foundation — PASS (#5499)
Capability 2 Marktoberfläche End-to-End / Landscape Shell — TECHNICAL_PASS (#5501); operator product PENDING
Capability 3 Kanonische Marktbindung (incl. OKX OHLCV + continuous refresh + intrabar) — PASS through #5548 for market/OHLCV path
Capability 4 Entscheidungsfähigkeit (Decision/DP) — PASS technical (#5506/#5507); operator product PENDING
Capability 5 Operative Projektion (Safety #5508; Risk/Sizing/Capital + Execution/Reconciliation #5562) — TECHNICAL_PASS
Capability 6 Governance & Autonomieprojektion — PASS_ALT_A (#5563; economic fields presented; diagnostics/autonomy remain ratified NOT_BOUND; no supersession)
Capability 7 Produktreife — TECHNICAL_PASS (#5564 density/drawer/a11y/perf/source-health; timeline DEFERRED; review-server identity #5565; OPERATOR_PRODUCT_GATE=false)
Capability 8 Produktionsabschluss — DOCS_CLOSEOUT_MERGED (#5566; merge SHA 02e4081498ee926fa6a3740d65d67be7de4a0c56; docs/ownership closeout only; OPERATOR_PRODUCT_GATE unchanged PENDING; PRODUCT_APPROVAL_INFERRED=false)
```

---

## 7. Test- und Evidence-Strategie

### 7.1 Contract Tests

- immutable snapshots
- schema/version validation
- provenance mandatory
- timestamp validation
- enum validation
- serialization stability
- stale/missing/invalid states

### 7.2 Adapter Tests

- exact field projection
- no recomputation
- no hidden defaults
- no cross-source enrichment that changes semantics
- missing source remains missing

### 7.3 Page Aggregate Tests

- one aggregate owner
- contradictory sources fail closed
- source health complete
- partial page remains renderable
- decision missing does not create fallback decision

### 7.4 Route/UI Tests

- `/market` returns 200
- no write form
- no action endpoint
- no order controls
- no runtime controls
- no hidden command calls
- proper unavailable states
- no console errors
- no overflow

### 7.5 Static Architecture Guards

Tests oder CI-Guards müssen verhindern:

```text
- webui imports mutable execution/order services
- domain packages import webui/templates
- static DP fixture returns to /market
- hardcoded authority/safety facts
- production dummy fallback
- duplicated visible-fact owner
- UI-side decision/risk/sizing calculation
```

### 7.6 Chrome Evidence

Pflichtviewports:

```text
1512x982
1920x1080
```

Optional:

```text
2560x1440
```

Evidence:

```text
evidence/market_dashboard_v2/<phase>/<pr>/
  git_state.txt
  source_owner_matrix.tsv
  route_test.txt
  contract_tests.txt
  static_guards.txt
  console.log
  market_1512x982.png
  market_1920x1080.png
  rendered_market.html
  evidence_manifest.sha256
```

Automatisierter PASS ist kein Operator Product PASS.

---

## 8. Operator-GO-Matrix

### Standing GO im Dashboard-Workstream

Nach explizitem Operator-Start **einer** vollständigen, nicht-aktivierenden Capability PR zulässig:

- Read-only Discovery
- Docs
- Contracts
- Adapter-Projektionen
- Tests
- Templates/CSS
- Chrome Evidence
- Ready (non-draft) Capability-PR-Erstellung, außer Operator verlangt ausdrücklich Draft

Nicht zulässig ohne explizite Operator-Anforderung: Micro-Slices, künstliche Slice-Splits, automatische Draft-PR-Erzeugung.

### Separates GO zwingend

```text
- Core-Semantikänderung
- Strategy Wiring
- Runtime Activation
- Orders
- Scheduler Activation
- Shadow/Paper/Testnet
- Capital Change
- Promotion
- Live
- Massenlöschung historischer Dateien
- Änderung kanonischer Authority
```

Dashboard-Arbeit darf diese GO-Klassen niemals implizit einschließen.

---

## 9. Cursor-Betriebsregeln

```text
CURSOR_AGENT_MODE=DIRECT_AGENT_ONLY
SUB_AGENTS=false
AUTO_MERGE=false
LIVE_AUTHORIZED=false
ORDERS=false
SHADOW=false
PAPER=false
TESTNET=false
SCHEDULER=false
CAPITAL_CHANGE=false
HARD_STOP_ON_SCOPE_DRIFT=true
```

### Arbeitsweise

1. Vor jedem PR `main == origin&#47;main` prüfen.
2. Worktree muss sauber sein oder vollständig klassifiziert werden.
3. Erst Repo-Wahrheit lesen, dann Änderung planen.
4. Keine Dateinamen aus diesem Runbook blind übernehmen.
5. Bestehende kanonische Contracts bevorzugen.
6. Keine zweite Wahrheit erzeugen.
7. Keine Sub-Agents.
8. Nach PR-Erstellung stoppen.
9. Merge nur nach separatem Auftrag.
10. Bei unerwartetem Core-Diff sofort stoppen.

### Fortschrittsregeln

```text
>5 Minuten:
- Fortschritt und aktuellen Blocker ausgeben

>25 Minuten:
- stoppen
- Diagnose ausgeben
- keine Endlosschleife
```

---

## 10. Erster ausführbarer Cursor-Auftrag

Dieser Auftrag startet ausschließlich **Phase 0**. Er verändert kein Repo.

```text
PEAK_TRADE MARKET DASHBOARD LANDSCAPE V2 — PHASE 0 READ-ONLY RATIFICATION

MODE=READ_ONLY
DIRECT_AGENT_ONLY=true
SUB_AGENTS=false
REPO_MUTATION=false
COMMIT=false
PUSH=false
PR=false
AUTO_MERGE=false

LIVE_AUTHORIZED=false
ORDERS=false
SHADOW=false
PAPER=false
TESTNET=false
SCHEDULER=false
CAPITAL_CHANGE=false
RUNTIME_ACTIVATION=false

OBJECTIVE
Establish the exact current repository truth required to build a new Market Dashboard V2 as a pure read-only Landscape consumer. Do not implement, edit, delete, format, rename, generate tracked evidence, or modify any file.

CANONICAL ARCHITECTURE
- Master V2 remains the canonical decision core.
- Double Play authority remains canonical and sole.
- Dynamic Scope authority remains canonical.
- Safety/Kill Switch remains an independent veto authority.
- Runtime BOUND_NOT_ACTIVATED is intentional.
- Strategy-Signal Selection D / Slice 2 lock is intentional.
- The Market Dashboard owns no business logic, trading authority, runtime authority, order authority, scheduler authority, promotion authority or capital authority.
- Missing data must be rendered as NOT_BOUND, MISSING_SOURCE, STALE or INVALID. It must never be invented.
- The target product is one coherent Landscape market workspace, not a governance card wall.
- Chrome/Playwright Real Chrome is the primary product evidence path.

READ FIRST
Locate and read the current canonical:
- Map of Truth
- Master V2 / Double Play runbooks
- Runtime bridge and pre-activation contracts
- Dynamic Scope authority documents
- Safety/Authority contracts
- Autonomy/Vollautonomie runbooks
- Dashboard/WebUI owner maps and docs
- current /market route state
- historical Market Dashboard runbooks only as non-canonical design references

DISCOVERY TASKS
1. Verify repo root, branch, HEAD, origin/main, worktree and open PRs.
2. Determine the exact current state of GET /market:
   - route exists / 404 / reset shell / other
   - route registration
   - template
   - presenter/page aggregate
   - JS/CSS
   - tests
3. Inventory all current read-only producers or snapshots relevant to:
   - market data / OHLCV / depth / tape
   - universe / ranking / eligibility
   - selected instrument
   - dynamic scope
   - market context / regime
   - canonical decision
   - Double Play
   - risk / sizing / capital
   - safety / kill switch / authority
   - execution / order-intent status / reconciliation
   - economic evidence
   - diagnostics
   - runtime bridge
   - autonomy ladder / scheduler / worker status
4. For every candidate source record:
   - exact path
   - symbols
   - owner
   - schema/version
   - producer type
   - authority class
   - current consumer(s)
   - provenance/freshness fields
   - safe for dashboard reuse: YES/NO/CONDITIONAL
5. Identify any existing dashboard contracts, adapters, page aggregates, presenters or static fixtures.
6. Identify forbidden write/action paths the new /market route must never import or call.
7. Produce a visible-fact/source matrix for the proposed Landscape:
   - Visible Fact
   - Canonical Producer
   - Existing Contract
   - Availability
   - Missing-State
   - Proposed Surface Region
8. Classify gaps only as:
   A_CONFIRMED_DEFECT
   B_INTENTIONAL_LOCK
   C_DOCS_OR_HYGIENE
   D_FUTURE_ONLY
   E_UNPROVEN
   F_MISSING_READ_PROJECTION
9. Explicitly distinguish:
   - missing producer
   - existing producer but no dashboard projection
   - historical/legacy source
   - non-authoritative diagnostic source
10. Recommend one next Capability PR (not Micro-Slices). Do not create branches or files.

FORBIDDEN
- no Core changes
- no Runtime changes
- no Strategy wiring
- no activation
- no dashboard implementation
- no template/CSS work
- no screenshots requiring server mutation
- no cleanup
- no file creation
- no tracked evidence
- no Sub-Agents

MANDATORY FINAL OUTPUT
STATUS=PASS|FAIL
VERDICT=...
BASE_SHA=...
MAIN_EQUALS_ORIGIN_MAIN=true|false
WORKTREE_CLEAN=true|false
OPEN_PRS=[...]
MARKET_ROUTE_STATE=...
CORE_ARCHITECTURE_VALID=true|false
CORE_CHANGE_REQUIRED=false|true
RUNTIME_CHANGE_REQUIRED=false|true
DASHBOARD_CAN_BE_PURE_CONSUMER=true|false
EXISTING_CANONICAL_SOURCE_COUNT=...
MISSING_READ_PROJECTION_COUNT=...
MISSING_PRODUCER_COUNT=...
FORBIDDEN_WRITE_PATHS=[...]
VISIBLE_FACT_MATRIX_COMPLETE=true|false
GAPS_CLASS_A=[...]
GAPS_CLASS_B=[...]
GAPS_CLASS_C=[...]
GAPS_CLASS_D=[...]
GAPS_CLASS_E=[...]
GAPS_CLASS_F=[...]
RECOMMENDED_PR_SEQUENCE=[...]
NEXT_ACTION=...
REPO_MUTATION=false
HARD_STOP=true
```

---

## 11. Übergabeprotokoll für neue Chats

Diesen Abschnitt nach jedem gemergten Dashboard-Capability-PR aktualisieren.

```text
PROJECT=PEAK_TRADE
WORKSTREAM=MARKET_DASHBOARD_LANDSCAPE_V2

CANONICAL_PRINCIPLE=
Market Dashboard is a pure read-only consumer with zero trading,
runtime, scheduler, promotion, capital or execution authority.

CURRENT_MAIN_SHA=9ff632885422a92e86f9dbeda79aab160bf2346b
LAST_MERGED_PR=5569
OPEN_PR=NONE
CURRENT_PHASE=FINAL_PRODUCT_STATE_CLOSEOUT_COMPLETE
LAST_COMPLETED_TECHNICAL_CAPABILITY=CAPABILITY_7_PRODUCT_MATURITY_PR_5564_PLUS_REVIEW_SERVER_IDENTITY_PR_5565
LAST_PRODUCT_CAPABILITY=PR_5568_DAILY_OKX_ARCHIVE_OBSERVATION
OPERATOR_PRODUCT_REVIEW_REVIEWED_SHA=88f2241819dcc160c3ce688a9c7397e7cc8becec
OPERATOR_PRODUCT_REVIEW_AFTER_PR=5568
PR_5569_DOCS_ONLY_ANTI_SSOT=true
MARKET_DASHBOARD_PHASE_5_PASS=true
TECHNICAL_PRODUCT_GATE=true
OPERATOR_PRODUCT_GATE=true
DAILY_OBSERVATION_USABLE=true
WORKSTREAM_STATE=FINAL_CLOSEOUT_COMPLETE

MARKET_DASHBOARD_CANONICAL_CONSUMER=true
OKX_CANONICAL_VENUE=true
FUTURES_ONLY=true
BTC_EXCLUDED=true
SPOT_EXCLUDED=true
CANONICAL_OHLCV_BOUND=true
CONTINUOUS_OHLCV_REFRESH=true
INTRABAR_CAPABILITY_MERGED=true
VALID_INTRABAR_EVIDENCE_PATH=evidence/market_dashboard_v2/intrabar_capability/2026-07-25T214037Z
INVALID_HISTORICAL_EVIDENCE_PATH=evidence/market_dashboard_v2/intrabar_capability/2026-07-25T211859Z
EVIDENCE_MANIFEST_SHA256=1cd1dfff96306087e19d5ca5a235664ddcfbef53b3e8740b4d301f0c5cffe085
CAPABILITY_7_EVIDENCE_PATH=evidence/market_dashboard_v2/capability7_product_maturity/

CANONICAL_ROUTE=GET_/market
CANONICAL_TEMPLATE=templates/peak_trade_dashboard/market_landscape_v2.html
CANONICAL_STATIC_SURFACES=[
  "static/css/market_dashboard_landscape_v2.css",
  "static/js/market_dashboard_landscape_v2.js"
]
CANONICAL_READ_AGGREGATE=MarketDashboardReadServiceV1+present_market_landscape_v2
CANONICAL_SHELL_ROUTER=src/webui/market_dashboard_landscape_shell_router_v2.py
CANONICAL_PRODUCER_BINDING=src/webui/market_dashboard_landscape_producer_binding_v2.py
LEGACY_PRODUCT_TOMBSTONE=docs/webui/MARKET_DASHBOARD_REMOVED.md

CORE_ARCHITECTURE_VALID=true
CORE_CHANGE_REQUIRED=false
RUNTIME_CHANGE_REQUIRED=false
MASTER_V2_CANONICAL=true
DOUBLE_PLAY_CANONICAL=true
DYNAMIC_SCOPE_CANONICAL=true
SAFETY_AUTHORITY_CANONICAL=true
RUNTIME_BOUND_NOT_ACTIVATED=true
LIVE_AUTHORIZED=false
ORDERS=false
SCHEDULER=false
CAPITAL_CHANGE=false
SHADOW=false
PAPER=false
TESTNET=false

TARGET_UI=
One coherent professional Landscape market workspace.
Primary chart above the fold with authentic OKX Futures OHLCV + intrabar tip.
Decision / Why / Blocker immediately visible.
No governance card wall.
No order or activation controls.

CURRENT_MARKET_ROUTE=GET_/market_LANDSCAPE_V2_OKX_FUTURES_OHLCV_INTRABAR_200
CURRENT_BOUND_SOURCES=[
  "OKX public market-data producer path (governed; futures-only)",
  "universe_selection + selected instrument identity",
  "canonical OHLCV snapshot + continuous refresh + intrabar open-candle (MODEL_A)",
  "dynamic_scope lifecycle projection",
  "canonical_decision + double_play display projection",
  "safety_authority KillSwitch projection",
  "risk_sizing_capital explicit injection projection",
  "execution_reconciliation explicit injection projection",
  "economic_summary explicit injection projection",
  "Capability 6 ALT_A: economic ops-band field presentation (evidence-only)",
  "Capability 6 ALT_A: diagnostics NOT_BOUND + NON_AUTHORITATIVE presentation",
  "Capability 6 ALT_A: autonomy/promotion/activation NOT_BOUND + BOUND_NOT_ACTIVATED lock presentation",
  "Capability 7: product-maturity density/drawer/a11y/perf/source-health (technical)",
  "source_health / freshness",
  "engineering drawer",
  "page_aggregate MarketDashboardReadServiceV1",
  "presenter present_market_landscape_v2 (formatting only)",
  "shell runtime constant BOUND_NOT_ACTIVATED (non-authoritative product metadata)"
]
NOT_BOUND_SOURCES=[
  "diagnostics_summary (Phase 4.6C OPTION_A KEEP_NOT_BOUND)",
  "autonomy_stage (Phase 4.7 OPTION_D KEEP_NOT_BOUND)",
  "event_decision_timeline (Phase 5 TASK_4 DEFERRED; honest NOT_BOUND placeholder)",
  "regime / bull_bear / switch (lifecycle scope bound; these remain unbound)"
]
MISSING_READ_PROJECTIONS=[
  "regime / bull_bear / switch Landscape binding",
  "confidence Landscape binding"
]
MISSING_PRODUCERS=[
  "event_decision_timeline durable ordered transition/decision history (no canonical producer; Phase 5 TASK_4 deferred)"
]
KNOWN_INTENTIONAL_LOCKS=[
  "BOUND_NOT_ACTIVATED",
  "LIVE/ORDERS/SCHEDULER fail-closed",
  "Strategy Signal Selection D / Slice 2 blocked",
  "Ops Double Play projection-only",
  "Phase 4.6C diagnostics_summary OPTION_A KEEP_NOT_BOUND",
  "Phase 4.7A/4.7B autonomy_stage OPTION_D KEEP_NOT_BOUND",
  "Phase 5 TASK_4 event_decision_timeline B_EXPLICIT_PHASE_5_DEFERRAL",
  "PR #5548 invalid historical evidence 2026-07-25T211859Z must not be promoted",
  "Operator Product Gate PASS recorded from review SHA 88f2241819dcc160c3ce688a9c7397e7cc8becec; do not re-infer from technical/Chrome evidence alone"
]
TASK_4_STATE_TRANSITION_TIMELINE=DEFERRED
TASK_4_PHASE_5_BLOCKING=false
TASK_4_IMPLEMENTED=false
TASK_4_PERMANENTLY_NOT_APPLICABLE=false
TIMELINE_SOURCE_AVAILABLE=false
TIMELINE_UI_STATE=NOT_BOUND
FUTURE_PRODUCER_WORK_AUTHORIZED=false
PHASE_5_PASS=true
MARKET_DASHBOARD_PHASE_5_PASS=true
TECHNICAL_PRODUCT_GATE=true
OPERATOR_PRODUCT_GATE=true
DAILY_OBSERVATION_USABLE=true

CAPABILITY_PR_ONLY=true
MICRO_PR_ALLOWED=false
DRAFT_PR_ALLOWED_ONLY_IF_OPERATOR_REQUESTS=true
EACH_PR_HAS_DEFINITION_OF_DONE=true
EACH_PR_DELIVERS_OPERATOR_VISIBLE_VALUE=true
NO_ARTIFICIAL_SLICE_SPLITTING=true

PHASE_PR_MAPPING=[
  "PHASE 2 == PR #5499",
  "PHASE 3 Shell == PR #5501",
  "OKX OHLCV continuous refresh == PR #5528",
  "Intrabar open-candle == PR #5548 (merge SHA 6f38df4d833945197e8f472c09f402ee767c85ad)",
  "Risk/Exec binding == PR #5562",
  "Capability 6 ALT_A == PR #5563",
  "Capability 7 product maturity == PR #5564",
  "Cap7 review-server macOS path identity == PR #5565 (merge SHA 33811dc5162b6fff6bb778204024f1d6d4c1b4b5)",
  "Capability 8 docs/ownership closeout == PR #5566 (merge SHA 02e4081498ee926fa6a3740d65d67be7de4a0c56; docs/ownership closeout only; not product PASS)",
  "Daily OKX archive observation == PR #5568 (merge SHA 88f2241819dcc160c3ce688a9c7397e7cc8becec; Operator Product Review PASS on this SHA)",
  "Consumer/Anti-SSOT wording == PR #5569 (merge SHA 9ff632885422a92e86f9dbeda79aab160bf2346b; docs-only; did not invalidate product review)"
]

NEXT_CANONICAL_ACTION=RETURN_TO_OPERATOR_FOR_SEPARATELY_AUTHORIZED_WORKSTREAM
WORKSTREAM_STATE=FINAL_CLOSEOUT_COMPLETE
Operator Product Review PASS is recorded on reviewed SHA
`88f2241819dcc160c3ce688a9c7397e7cc8becec` (post PR #5568). PR #5569
(`9ff632885422a92e86f9dbeda79aab160bf2346b`) is subsequent docs-only
Consumer / Anti-SSOT wording and did not change runtime or product behavior.
No automatic next Dashboard capability. Do not authorize Runtime, Orders,
Scheduler, Capital, Promotion, Shadow, Paper, Testnet or Live from this seal.
Missing Decision/Risk/Safety producers remain fail-closed / NOT_BOUND where unbound.

SEPARATE_GO_REQUIRED_FOR=[
  "Core changes",
  "Runtime activation",
  "Strategy wiring",
  "Orders",
  "Scheduler",
  "Shadow/Paper/Testnet",
  "Capital",
  "Promotion",
  "Live",
  "Mass cleanup",
  "Any new Dashboard capability beyond sealed daily observation truth",
  "diagnostics_summary redesign (beyond OPTION_A)",
  "autonomy_stage aggregate (beyond OPTION_D)",
  "event_decision_timeline durable producer + read-only projection"
]
```

### Prior Next Capability PR — executed as Risk/Exec binding Capability (historical command below)

```text
CAPABILITY_OBJECTIVE=
Bind risk_sizing_capital and execution_reconciliation as one complete
read-only operative projection capability on Market Dashboard Landscape V2.

DEFINITION_OF_DONE=
- owner_registry reuse_status REUSED (or honest STALE/MISSING via injection) for
  risk_sizing_capital and execution_reconciliation
- field-for-field projection only; no recomputation; no order/execution imports in UI
- /market shows operator-visible Risk/Sizing/Capital and Execution/Reconciliation
  facts or honest NOT_BOUND/MISSING/STALE (no dummy values)
- architecture guards + focused webui/ops tests green
- Chrome evidence 1512x982 + 1920x1080
- CAPABILITY_PR_ONLY Ready PR (not Draft unless operator requests Draft)
- CORE/RUNTIME/ORDERS/SCHEDULER/CAPITAL unchanged

CURSOR_COMMAND=
PEAK_TRADE MARKET DASHBOARD LANDSCAPE V2 — NEXT CAPABILITY PR
MODE=IMPLEMENTATION
DIRECT_AGENT_ONLY=true
SUB_AGENTS=false
AUTO_MERGE=false
REPO_ROOT=/Users/frnkhrz/Peak_Trade
BASE_SHA=origin/main
CAPABILITY_PR_ONLY=true
MICRO_PR_ALLOWED=false
DRAFT_PR_ALLOWED_ONLY_IF_OPERATOR_REQUESTS=true
OBJECTIVE=Bind Risk/Sizing/Capital + Execution/Reconciliation read-only projections on /market as one Capability PR.
LIVE_AUTHORIZED=false
ORDERS=false
SCHEDULER=false
CAPITAL_CHANGE=false
RUNTIME_ACTIVATION=false
FORBIDDEN=reopen PR #5548 intrabar scope; Micro-Slices; implicit Draft PR; Core/strategy/authority/runtime activation changes
DOD=operator-visible operative projection OR honest missing states; tests+Chrome evidence; Ready non-draft PR; no merge without operator
```

---

## 12. Abschlussentscheidung

```text
STATUS=MARKET_DASHBOARD_V2_FINAL_PRODUCT_STATE_CLOSEOUT_COMPLETE
VERDICT=DASHBOARD_IMPLEMENTATION_PRESENT_ON_MAIN; CAPS_1_TO_7_TECHNICAL_RECORDED; CAP8_DOCS_OWNERSHIP_CLOSEOUT_MERGED_VIA_PR_5566; PR_5568_DAILY_OBSERVATION_MERGED; OPERATOR_PRODUCT_REVIEW_PASS_ON_88f2241819dcc160c3ce688a9c7397e7cc8becec; PR_5569_DOCS_ONLY_ANTI_SSOT_ON_9ff632885422a92e86f9dbeda79aab160bf2346b; RUNTIME_NOT_ACTIVATED; OPERATOR_PRODUCT_GATE=true; MARKET_DASHBOARD_PHASE_5_PASS=true; DAILY_OBSERVATION_USABLE=true; PRODUCT_APPROVAL_INFERRED=false
DASHBOARD_ROLE=PURE_READ_ONLY_CONSUMER
LANDSCAPE_TARGET=true
CORE_CHANGE_AUTHORIZED=false
RUNTIME_CHANGE_AUTHORIZED=false
RUNTIME_ACTIVATED=false
DASHBOARD_IMPLEMENTATION_PRESENT=true
MARKET_DASHBOARD_PHASE_5_PASS=true
TECHNICAL_PRODUCT_GATE=true
OPERATOR_PRODUCT_GATE=true
DAILY_OBSERVATION_USABLE=true
PHASE_5_PASS=true
WORKSTREAM_STATE=FINAL_CLOSEOUT_COMPLETE
CAPABILITY_PR_ONLY=true
MICRO_PR_ALLOWED=false
DRAFT_PR_ALLOWED_ONLY_IF_OPERATOR_REQUESTS=true
LIVE_AUTHORIZED=false
ORDERS=false
SCHEDULER=false
CAPITAL_CHANGE=false
FIRST_ACTION=RETURN_TO_OPERATOR_FOR_SEPARATELY_AUTHORIZED_WORKSTREAM
```

Das Dashboard ist zu keinem Zeitpunkt eine fachliche Wahrheit. Es ist dauerhaft eine reine read-only Projektion der kanonischen Producer-Landschaft und bleibt ausschließlich Consumer kanonischer ReadModels.

```text
DASHBOARD_IS_CONSUMER_ONLY=true
DASHBOARD_IS_AUTHORITY=false
DASHBOARD_IS_TRUTH_OWNER=false
DASHBOARD_IS_SSOT=false
SECOND_TRUTH_ALLOWED=false
CANONICAL_PRODUCERS_REMAIN_OWNERS=true
MISSING_DATA_REMAINS_FAIL_CLOSED=true
NO_DOMAIN_LOGIC_IN_UI=true
NO_RUNTIME_AUTHORITY=true
NO_WRITE_PATH=true
```
