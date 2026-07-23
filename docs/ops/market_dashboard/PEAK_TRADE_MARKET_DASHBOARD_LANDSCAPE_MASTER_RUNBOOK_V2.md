# Peak_Trade — Market Dashboard Landscape Master Runbook V2

**Dokumenttyp:** Kanonisches Planungs-, Übergabe- und Ausführungsrunbook  
**Ziel:** Neuer Market-Workspace als strikt read-only Consumer des Peak_Trade-Systems  
**Status:** `PHASE_3_LANDSCAPE_SHELL_IMPLEMENTED_OPERATOR_APPROVAL_PENDING`  
**Geltung:** Ab dem ratifizierten Architekturstand `RATIFICATION_COMPLETE_NO_CLASS_A`  
**Primärbrowser:** Google Chrome / Playwright Real Chrome  
**Oberflächenprinzip:** Landscape · eine zusammenhängende Market-Workspace-Komposition · keine Card-Wand  
**Core-Status:** Master V2 / Double Play / Dynamic Scope / Safety bleiben unverändert  
**Runtime-Status:** `BOUND_NOT_ACTIVATED` bleibt intentional  
**Live-Status:** `LIVE_AUTHORIZED=false`, `ORDERS=false`

```text
CANONICAL_REPO_PATH=docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md
REPO_INGESTION_DATE=2026-07-23
SOURCE_FILENAME=PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md
PHASE_3_AUTHORIZED=true
PHASE_3_PR_2_SCOPE=LANDSCAPE_SHELL_ONLY
IMPLEMENTATION_AUTHORIZATION_STATUS=PHASE_3_SHELL_IN_PROGRESS_OPERATOR_APPROVAL_PENDING
PHASE_4_AUTHORIZED=false
OPERATOR_SKELETON_APPROVAL=PENDING
```

**Phasen-/PR-Mapping (explizit, keine stille Geschichtsrewrite):** Runbook-**PHASE 2** (ReadModel Foundation / Source Health) entspricht dem gemergten Implementierungs-**PR #5499** („PR 1 — ReadModel Contracts and Guards“). Runbook-**PHASE 3** / Implementierungs-**PR 2** (Landscape Shell) ist unter `OPERATOR_GO=PHASE_3_PR_2_LANDSCAPE_SHELL_ONLY` autorisiert; Operator-Skeleton-Approval bleibt `PENDING` bis Screenshot-Review.

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
`autonomy_stage` → `reuse_status=NOT_BOUND`, `owner=NONE`, `source/contract=NONE`.

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

## 6. Empfohlene PR-Sequenz

Jeder PR ist bounded. Kein Mega-PR.

### PR 0 — Discovery / Ratification Docs Only

```text
Scope:
- Current-state inventory
- Owner/source matrix
- Gap classification
- final file/path proposal

No implementation.
```

### PR 1 — ReadModel Contracts and Guards

```text
Scope:
- missing immutable contracts
- provenance/freshness
- unavailable semantics
- import/static guards
```

### PR 2 — Landscape Shell

```text
Scope:
- route
- page aggregate skeleton
- templates/CSS
- real sources where already safe
- NOT_BOUND elsewhere
```

### PR 3 — Market / Universe / Scope Binding

```text
Scope:
- market data
- ranking
- selected instrument
- dynamic scope projection
```

### PR 4 — Decision / Double Play Binding

```text
Scope:
- canonical decision evidence
- canonical DP evidence
- reasons/blockers
```

### PR 5 — Safety / Risk / Execution Binding

```text
Scope:
- safety authority
- risk/sizing/capital
- execution/reconciliation state
```

### PR 6 — Economic / Diagnostics / Autonomy Binding

```text
Scope:
- economic summary
- diagnostics
- autonomy status projections
```

### PR 7 — Product Polish and Operator Review

```text
Scope:
- visual hierarchy
- density
- timeline
- engineering drawer
- Chrome evidence
```

### PR 8 — Closeout / Cleanup

```text
Scope:
- bounded legacy cleanup
- docs/owner maps
- permanent regression guards
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

Nach explizitem Start des jeweiligen bounded PR-Slices zulässig:

- Read-only Discovery
- Docs
- Contracts
- Adapter-Projektionen
- Tests
- Templates/CSS
- Chrome Evidence
- PR-Erstellung

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
10. Recommend a bounded PR sequence. Do not create branches or files.

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

Diesen Abschnitt nach jedem gemergten Dashboard-PR aktualisieren.

```text
PROJECT=PEAK_TRADE
WORKSTREAM=MARKET_DASHBOARD_LANDSCAPE_V2

CANONICAL_PRINCIPLE=
Market Dashboard is a pure read-only consumer with zero trading,
runtime, scheduler, promotion, capital or execution authority.

CURRENT_PHASE=PHASE_3_LANDSCAPE_SHELL
LAST_COMPLETED_PHASE=PHASE_2
LAST_MERGED_PR=5500
PHASE_3_PR=2
BRANCH=feat/market-dashboard-landscape-shell-v2
BASE_SHA_EXPECTED=e18a16e138d643cac5748c8ccafaea0b871a80c8
OPEN_PR=SEE_PR_AFTER_OPEN

READMODEL_FOUNDATION_COMPLETE=true
PR_1_MERGED=true
SOURCE_HEALTH_IMPLEMENTED=true
ARCHITECTURE_GUARDS_IMPLEMENTED=true
PHASE_3_AUTHORIZED=true
PHASE_3_SHELL_IMPLEMENTED=true
OPERATOR_SKELETON_APPROVAL=PENDING
PHASE_4_AUTHORIZED=false

CORE_ARCHITECTURE_VALID=true
CORE_CHANGE_REQUIRED=false
RUNTIME_CHANGE_REQUIRED=false
MASTER_V2_CANONICAL=true
DOUBLE_PLAY_CANONICAL=true
DYNAMIC_SCOPE_CANONICAL=true
SAFETY_AUTHORITY_CANONICAL=true
RUNTIME_BOUND_NOT_ACTIVATED=true

TARGET_UI=
One coherent professional Landscape market workspace.
Primary chart above the fold.
Decision / Why / Blocker immediately visible.
No governance card wall.
No order or activation controls.

CURRENT_MARKET_ROUTE=GET_/market_LANDSCAPE_V2_PHASE_3_SHELL_200
CURRENT_BOUND_SOURCES=[
  "src/webui/market_dashboard_landscape_v2 (read-only projection contracts)",
  "page_aggregate MarketDashboardReadServiceV1 (NOT_BOUND bundle + source health)",
  "presenter present_market_landscape_v2 (formatting only)",
  "shell runtime constant BOUND_NOT_ACTIVATED (non-authoritative product metadata)"
]
NOT_BOUND_SOURCES=[
  "market_instrument / OHLCV chart",
  "universe_ranking",
  "dynamic_scope / regime / switch",
  "canonical_decision / confidence",
  "double_play",
  "risk_sizing_capital",
  "safety_authority",
  "execution_reconciliation",
  "economic_summary",
  "autonomy_stage (OPTION_D explicit NOT_BOUND; no producer/contract)",
  "diagnostics_summary",
  "event_decision_timeline"
]
MISSING_READ_PROJECTIONS=[
  "market/universe/scope UI binding (PR 3 / Phase 4.1-4.2)",
  "decision/DP UI binding (PR 4 / Phase 4.3)",
  "safety/risk/execution UI binding (PR 5 / Phase 4.4-4.5)",
  "economic/diagnostics UI binding (PR 6 / Phase 4.6); autonomy remains OPTION_D NOT_BOUND"
]
MISSING_PRODUCERS=[]
KNOWN_INTENTIONAL_LOCKS=[
  "BOUND_NOT_ACTIVATED",
  "LIVE/ORDERS/SCHEDULER fail-closed",
  "Strategy Signal Selection D / Slice 2 blocked",
  "Ops Double Play projection-only",
  "Phase 4 producer binding not authorized in this PR",
  "Phase 4.6C diagnostics_summary OPTION_A KEEP_NOT_BOUND (owner UNRESOLVED; WorkflowDashboardReadModelV1 NON_SOURCE)",
  "Phase 4.7A/4.7B autonomy_stage OPTION_D KEEP_NOT_BOUND (aggregate not required; owner/producer/contract=NONE; runtime bridge status separate NON_SOURCE)"
]

PHASE_PR_MAPPING=[
  "Runbook PHASE 2 == Implementation PR #5499 (labeled PR 1 ReadModel Contracts)",
  "Runbook PHASE 3 == Implementation PR 2 Landscape Shell (this PR; operator approval pending)",
  "PHASE 0 / PHASE 1 not claimed complete in-repo (no durable Phase 0/1 artifacts)"
]

NEXT_CANONICAL_ACTION=
Operator reviews Phase 3 screenshots and PR.
Do not start Phase 4 producer binding without a new OPERATOR_GO.

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
  "Phase 4 producer binding"
]
```

---

## 12. Abschlussentscheidung

```text
STATUS=MARKET_DASHBOARD_V2_READMODEL_FOUNDATION_COMPLETE
VERDICT=PHASE_2_COMPLETE_VIA_PR_5499; PHASE_3_LANDSCAPE_SHELL_NOT_AUTHORIZED; REMAIN_PURE_READ_ONLY_CONSUMER
DASHBOARD_ROLE=PURE_READ_ONLY_CONSUMER
LANDSCAPE_TARGET=true
CORE_CHANGE_AUTHORIZED=false
RUNTIME_CHANGE_AUTHORIZED=false
IMPLEMENTATION_AUTHORIZED=false
PHASE_3_AUTHORIZED=false
FIRST_ACTION=MERGE_CANONICAL_RUNBOOK_DOCS_INGESTION_THEN_PREPARE_PHASE_3_COMMAND_ONLY
```

Das Dashboard wird damit weder zu früh als neue fachliche Wahrheit gebaut noch so spät, dass fehlende Observability erst nach Vollautonomie sichtbar wird. Es wächst kontrolliert mit der kanonischen Producer-Landschaft und bleibt dauerhaft eine reine Projektion.
