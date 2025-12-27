# Peak_Trade – Mini-Roadmap zu v1.0 Research & Live-Beta

Ziel dieser Mini-Roadmap ist es, die letzten ca. 15–20 % bis zu zwei klaren Meilensteinen zu strukturieren:

- **Research v1.0 fertig**
- **Live-Track v1.0 als „Beta-ready" (streng gegated, kein Blindflug)**

Dazu werden sieben Micro-Phasen definiert, die auf dem bestehenden Stand (Strategy-Library v1.1, StrategyProfiles & Tiering, Regime-/Portfolio-Layer, Research-Pipeline v2, Live-Playbooks/Runbooks) aufbauen.

---

## Übersicht der Micro-Phasen

| Micro-Phase | Fokus | Hauptziel |
|------------|-------|-----------|
| **Phase 75** | R&D | R&D-Wave v2 Experiments & Operator-View (CLI `view_r_and_d_experiments.py`) |
| **Phase 76** | R&D | R&D Experiments Overview v1.1 – R&D Hub mit Daily Summary & Run-Type-Filter |
| **Phase 80** | Research | Tiering → Portfolio-Presets & Sweeps |
| **Phase 80B** | Execution | Strategy-to-Execution Bridge & Shadow/Testnet Runner v0 |
| **Phase 81** | Research UX | Golden-Path-Workflows & Recipes |
| **Phase 82** | Research QA | E2E-Tests & Szenario-Library |
| **Phase 83** | Live-Gates | Tiering-/Profile-basierte Live-Gates |
| **Phase 84** | Monitoring | Operator-Dashboards & Alerts v1.0 |
| **Phase 85** | Web-Dashboard | Live-Track Session Explorer (Filter, Detail, Stats-API) |
| **Phase 86** | Freeze & Tag | Research v1.0 Freeze + Live-Beta Label |

---

## Phase 75 – R&D-Wave v2 Experiments & Operator-View

**Status:** ✅ ABGESCHLOSSEN

**Ziel:**
Standardisierte R&D-Experimente für fortgeschrittene Forschungsstrategien (Armstrong, Ehlers, López de Prado, El Karoui) sowie ein praktischer Operator-Workflow für deren Sichtung und Auswertung.

**Kern-Deliverables:**

- **Experiment-Katalog:** 18 Experiment-Templates für 9 Presets
  - Detail-Doku: [`PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md`](PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md)
- **R&D-Presets:** Konfiguration in `config/r_and_d_presets.toml`
  - Preset-Doku: [`PHASE_75_R_AND_D_STRATEGY_WAVE_V2_PRESETS.md`](PHASE_75_R_AND_D_STRATEGY_WAVE_V2_PRESETS.md)
- **Operator-View (Abschnitt 8):** Praktischer Workflow Strategy-Profile → Experiments-Viewer → Dashboard
- **R&D Experiments Viewer CLI:** `scripts/view_r_and_d_experiments.py`
  - Filter nach Preset, Tag, Strategy, Datum, Trades
  - Detail-Ansicht per Run-ID oder Datei-Pfad
  - JSON-Output für Notebooks/Reports

**Operator-Workflow (Kurzfassung):**

1. **Strategy-Profiling:** `python scripts/research_cli.py strategy-profile --strategy <id>`
2. **Experimente inspizieren:** `python scripts/view_r_and_d_experiments.py --preset <preset_id> --with-trades`
3. **Ausblick:** R&D-Dashboard (geplant)

**Definition of Done:**

- ✅ 18 Experiment-Templates definiert
- ✅ R&D-Presets dokumentiert und konfiguriert
- ✅ Operator-View dokumentiert (Abschnitt 8)
- ✅ CLI `view_r_and_d_experiments.py` implementiert und getestet (32 Tests)

---

## Phase 76 – R&D Experiments Overview v1.1

**Status:** ✅ ABGESCHLOSSEN

**Ziel:**
Schärft die R&D-Experimente-Übersicht im Web-Dashboard zu einem zentralen **R&D Hub** mit Daily-Summary-Kacheln („Heute fertig", „Aktuell laufend") und Run-Type-Filtern – direkt angebunden an Registry und R&D-API.

**Kern-Deliverables:**

- **R&D Hub UI:** Daily Summary Kacheln, Quick-Actions, kompaktes Tabellenlayout mit Status-/Run-Type-Badges
- **R&D-API v1.1:** Neue Felder (`run_type`, `tier`, `experiment_category`, `date_str`), erweiterte Status-Werte (`success`, `running`, `failed`, `no_trades`)
- **Neue Endpoints:**
  - `GET /api/r_and_d/today` – heute fertiggestellte Experimente
  - `GET /api/r_and_d/running` – aktuell laufende Experimente
  - `GET /api/r_and_d/categories` – verfügbare Kategorien & Run-Types
- **Dokumentation:** [`PHASE_76_R_AND_D_EXPERIMENTS_OVERVIEW_V1_1.md`](PHASE_76_R_AND_D_EXPERIMENTS_OVERVIEW_V1_1.md)

**Operator-Nutzen:**

- Fokus: Tagesübersicht über fertige & laufende R&D-Runs
- Schnellscan über Status, Run-Type, Tier und Kategorie
- Vorbereitung für kommende R&D-Wellen (Ehlers, Armstrong, Lopez de Prado, El Karoui)

**Definition of Done:**

- ✅ API-Endpoints liefern korrekte Daten (9 Endpoints)
- ✅ Tabelle filterbar und sortierbar (inkl. Run-Type-Filter)
- ✅ Daily Summary Kacheln implementiert
- ✅ 51 Tests für API-Endpoints grün

---

## Phase 80 – Tiered Portfolio Presets v1.0 (Research)

**Status:** ✅ ABGESCHLOSSEN

**Ziel:**
Die Informationen aus `StrategyProfile` und `config/strategy_tiering.toml` werden aktiv im Portfolio-/Regime-Layer verwendet. Standard-Presets verwenden nur Strategien mit `tier = "core"`, `aux` ist optional, `legacy` nur noch explizit.

**Kern-Deliverables:**

- Portfolio-Preset-Configs (z.B. `config/portfolio_presets/*.toml`) mit:
  - „Core Balanced"-Preset,
  - „Core Trend+MeanReversion"-Preset,
  - „Core+Aux Aggro"-Preset.
- Helper-Funktionen, die Tiering-informationen beim Bauen von Portfolios berücksichtigen.
- Doku-Abschnitt zu „Tiered Portfolio Presets".

**Definition of Done:**

- Mindestens drei definierte und getestete Presets.
- Tests, die sicherstellen, dass:
  - `legacy`-Strategien nicht automatisch in Presets landen,
  - `core`-Filterung korrekt funktioniert.
- Beispiel-CLI-Befehle dokumentiert.

---

## Phase 80B – Strategy-to-Execution Bridge & Shadow/Testnet Runner v0

**Status:** ✅ ABGESCHLOSSEN

**Ziel:**
Orchestrierter Flow von konfigurierten Strategien über Signale zu Orders, die via `ExecutionPipeline.execute_with_safety()` an sichere Targets (Shadow/Testnet) durchgereicht werden.

**Kern-Deliverables:**

- `LiveSessionRunner` + `LiveSessionConfig` + `LiveSessionMetrics` (`src/execution/live_session.py`)
- CLI `scripts/run_execution_session.py` für Shadow/Testnet-Sessions
- Shadow/Testnet-Session-Flow: Strategy → Signals → Orders → ExecutionPipeline
- Safety: LIVE-Mode explizit und hart blockiert (an 3 Stellen), Safety-Gates & RiskLimits integriert
- 24 Tests (Config, Runner, CLI, Pipeline-Integration) grün
- Phasen-Dokumentation: `docs/PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md`

**Baut auf:**

- Phase 64 (TestnetOrchestrator)
- Phase 71 (Live-Execution-Design & Gating)
- Phase 16A (ExecutionPipeline)
- Phase 17 (SafetyGuard)

**Nächste Schritte:**

- Phase 8x+: Erweiterung zum voll orchestrierten Live-Track (Scheduler, Heartbeats, Monitoring, Incident-Hooks) – auf Basis von Phase 80B.

---

## Phase 81 – Research Golden Paths & Recipes

**Ziel:**  
2–3 klar dokumentierte Golden Paths, die einen kompletten Research-Flow beschreiben – von der Strategie-Idee bis zum Portfolio-Einsatz.

**Kern-Deliverables:**

- `docs/PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md` mit:
  - Golden Path 1: Neue Strategie von 0 → StrategyProfile + Tiering.
  - Golden Path 2: Bestehende Strategie → Sweep → Robustness → Portfolio.
  - Golden Path 3: Portfolio-Bau mit Tiering (core/aux).
- Optional: kleine Wrapper-Skripte zur Automatisierung.

**Definition of Done:**

- Mindestens zwei Golden Paths sind Ende-zu-Ende durchführbar (mit Test-/Dummy-Daten).
- Verlinkung aus Onboarding-/Overview-Dokumenten.

---

## Phase 82 – Research QA & Szenario-Library

**Ziel:**  
Ein Research-spezifisches QA-Netz mit definierten Markt-Szenarien und E2E-Tests.

**Kern-Deliverables:**

- `config/scenarios/` mit mindestens drei Szenarien:
  - z.B. `flash_crash`, `sideways_low_vol`, `trend_regime`.
- `tests/test_research_e2e_scenarios.py`:
  - End-to-End-Tests, die Research-Pipeline, StrategyProfile und Portfolio-Reports verbinden.
- einfache Baseline-Erwartungsbereiche für Demo-Strategien.

**Definition of Done:**

- Mindestens drei Szenarien definiert und getestet.
- 2–3 E2E-Tests laufen stabil und zuverlässig.
- Laufzeit bleibt CI-freundlich.

---

## Phase 83 – Live-Gating & Risk Policies v1.0

**Ziel:**  
Nur Strategien und Portfolios, die bestimmte Research-Kriterien erfüllen, sind für Shadow/Testnet/LIVE überhaupt zugelassen.

**Kern-Deliverables:**

- Modul für Live-Gates (z.B. `src/live/live_gates.py`) mit:
  - `check_strategy_live_eligibility(strategy_id)`.
- Integration in bestehende Live-/Shadow-/Testnet-Entry-Skripte:
  - Abbruch, wenn Strategien nicht live-eligible sind.
- `config/live_policies.toml` mit:
  - Minimalanforderungen (tier, allow_live, Sharpe, MaxDD etc.).

**Definition of Done:**

- Mindestens ein Live-/Readiness-Skript nutzt Live-Gates.
- Tests für Live-Gate-Logik inkl. Positiv-/Negativfällen.

---

## Phase 84 – Operator Dashboards & Alerts v1.0

**Ziel:**  
Operatoren erhalten eine schnell erfassbare Sicht auf Strategien, Profile, Tiering, Live-Eignung und aktuelle Runs.

**Kern-Deliverables:**

- CLI-Dashboard (z.B. `scripts/operator_dashboard.py`) mit:
  - Übersicht: Strategien + Tiering + Live-Status.
  - Übersicht: letzte Research-/Profil-Runs.
- Optional: einfache Web- oder TUI-Ansicht.
- einfache Alerts (z.B. veraltete Profile).

**Definition of Done:**

- Ein Operator kann per Single-Command den Zustand der Strategien und Live-Eignung prüfen.
- Mindestens ein Testfile für das Dashboard.
- Kurzer Abschnitt in Operator-/Runbook-Dokumentation.

---

## Phase 85 – Live-Track Session Explorer (Web-Dashboard v1)

**Status:** ✅ ABGESCHLOSSEN

**Kurzbeschreibung:**
Operatoren bekommen im Web-Dashboard eine durchsuchbare, filterbare Übersicht aller Live-Sessions (Shadow/Testnet/Live) – mit Detailansicht, Stats-API und direkter Verlinkung zur Session-Registry.

**Kern-Deliverables:**

- **Live-Track-Liste:** Filterbare Session-Übersicht im Dashboard (`/` Startseite), Filter via Query-Params (`?mode=shadow`, `?status=completed`)
- **Session-Detailseite:** Klickbare Sessions → `/session/{session_id}` mit allen Metriken (PnL, Drawdown, Orders, Errors, Timestamps)
- **Stats-Endpoint:** `/api/live_sessions/stats` liefert Aggregationen (Anzahl Sessions pro Mode/Status, Avg PnL, etc.)

**Operator-Nutzen:**

- Schnelle Übersicht über laufende und abgeschlossene Sessions
- Direkte Navigation von Dashboard → Session-Detail → Session-Logs
- Stats-API für externe Monitoring-Tools (Grafana, Alerting)

**Abhängigkeiten:**

- Baut auf: Phase 80 (LiveSessionRunner), Phase 81 (Session-Registry), Phase 83 (Live-Gates), Phase 84 (Operator-Workflow)

**Implementierung:**

- `src/webui/live_track.py` – Service-Layer für Session-Abfragen
- `src/webui/app.py` – Neue API-Endpoints (`/api/live_sessions`, `/api/live_sessions/{session_id}`, `/api/live_sessions/stats`)
- `templates/peak_trade_dashboard/index.html` – Filter-UI
- `templates/peak_trade_dashboard/session_detail.html` – Detail-View (NEU)
- `tests/test_webui_live_track.py` – 54 Tests

**Definition of Done:**

- ✅ Session-Liste filterbar (mode, status)
- ✅ Session-Detail zeigt alle relevanten Metriken
- ✅ Stats-Endpoint liefert Aggregationen
- ✅ 54 Tests grün

---

## Phase 85-alt – Live-Beta Drill (Shadow/Testnet)

> **Hinweis:** Dieser Abschnitt beschreibt die ursprünglich geplante Phase 85.
> Die tatsächlich implementierte Phase 85 ist der "Live-Track Session Explorer" (siehe oben).

**Ziel:**
Ein vollständiger Drill eines potenziellen Live-Betriebs, aber in Shadow/Testnet – inklusive Incident-Simulation.

**Kern-Deliverables:**

- `docs/PHASE_85_LIVE_BETA_DRILL.md` mit:
  - Szenario, Ablauf, Checks.
- Skript/Workflow, der:
  - Live-Gates verwendet,
  - Shadow/Testnet-Sessions startet,
  - Monitoring/Logs erzeugt,
  - ein oder zwei Incident-Szenarien simuliert.

**Definition of Done:**

- Mindestens ein Drill wurde erfolgreich durchgeführt und ausgewertet.
- Dokumentierte Lessons Learned.

---

## Phase 86 – Research v1.0 Freeze & Live-Beta Label

**Ziel:**  
Formelle Markierung des erreichten Stands: Research v1.0 ist fertig, Live-Track ist Beta-ready.

**Kern-Deliverables:**

- Git-Tags (z.B. `v1.0-research`, `v1.0-live-beta`).
- `docs/PEAK_TRADE_V1_RELEASE_NOTES.md`:
  - Zusammenfassung der Features,
  - bekannte Einschränkungen,
  - Ausblick auf v1.1 / v2.
- Klar definierter Scope-Freeze für die wichtigsten Komponenten.

**Definition of Done:**

- Alle Tests grün.
- Status-Overview dokumentiert Research v1.0 und Live-Beta-Status.
- Tags sind im Repo erstellt und dokumentiert.

---

## Abschluss – Stand nach Phasen 80–86

Die in dieser Mini-Roadmap definierten Micro-Phasen 80–86 wurden vollständig umgesetzt:

| Phase | Feature                                  | Tests | Status |
|-------|------------------------------------------|-------|--------|
| 80    | Tiered Portfolio Presets v1.0           | 33    | ✅     |
| 80B   | Strategy-to-Execution Bridge v0         | 24    | ✅     |
| 81    | Research Golden Paths & Recipes         | 16    | ✅     |
| 82    | Research QA & Szenario-Library          | 28    | ✅     |
| 83    | Live-Gating & Risk Policies v1.0        | 27    | ✅     |
| 84    | Operator Dashboards & Alerts v1.0       | 15    | ✅     |
| 85    | Live-Track Session Explorer (Web-Dashboard v1) | 54 | ✅     |
| 86    | Research v1.0 Freeze & Live-Beta Label  | -     | ✅     |
| **Summe** |                                      | **197** | ✅  |

**Neue / erweiterte Komponenten (Auszug):**

- **Config**
  - `config/portfolio_presets/` (3 Presets)
  - `config/scenarios/` (3 Szenarien)
  - `config/live_policies.toml`
- **Source**
  - `src/experiments/portfolio_presets.py`
  - `src/live/live_gates.py`
  - `src/execution/live_session.py` (Phase 80B: LiveSessionRunner, LiveSessionConfig, LiveSessionMetrics)
- **Scripts**
  - `scripts/run_research_golden_path.py`
  - `scripts/operator_dashboard.py`
  - `scripts/run_live_beta_drill.py`
  - `scripts/run_execution_session.py` (Phase 80B: Shadow/Testnet Session CLI)
- **Tests**
  - `tests/test_portfolio_presets_tiering.py`
  - `tests/test_research_golden_paths.py`
  - `tests/test_research_e2e_scenarios.py`
  - `tests/test_live_gates.py`
  - `tests/test_operator_dashboard.py`
  - `tests/test_live_beta_drill.py`
  - `tests/test_live_session_runner.py` (Phase 80B: 24 Tests)
  - `tests/test_webui_live_track.py` (Phase 85: 54 Tests)
- **Doku**
  - `docs/PHASE_80_TIERED_PORTFOLIO_PRESETS.md`
  - `docs/PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md` (Phase 80B)
  - `docs/PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md`
  - `docs/PHASE_82_RESEARCH_QA_AND_SCENARIOS.md`
  - `docs/PHASE_83_LIVE_GATING_AND_RISK_POLICIES.md`
  - `docs/PHASE_84_OPERATOR_DASHBOARD.md`
  - `docs/PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md`
  - `docs/PHASE_86_RESEARCH_V1_FREEZE.md`
- **Web-UI (Phase 85)**
  - `src/webui/live_track.py` – Service-Layer
  - `src/webui/app.py` – API-Endpoints (erweitert)
  - `templates/peak_trade_dashboard/index.html` – Filter-UI
  - `templates/peak_trade_dashboard/session_detail.html` – Detail-View

**Aktueller Gesamtstatus:**

- ✅ **Research v1.0 abgeschlossen (Scope-Freeze)**
- ✅ Vollständige Research-Pipeline mit Golden Paths & QA-Szenarien
- ✅ Tiered Portfolio Presets mit automatischer Eligibility (core/aux/legacy)
- ✅ Shadow-/Testnet-Stack in einem Live-Beta-Drill validiert
- ⚠️ **Live-Beta:** Shadow/Testnet als produktionsreifer Pfad, echtes Live bleibt weiterhin streng gegated und bewusst als „Beta" markiert.
