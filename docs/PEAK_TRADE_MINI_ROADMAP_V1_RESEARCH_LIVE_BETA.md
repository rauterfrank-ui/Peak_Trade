# Peak_Trade – Mini-Roadmap zu v1.0 Research & Live-Beta

Ziel dieser Mini-Roadmap ist es, die letzten ca. 15–20 % bis zu zwei klaren Meilensteinen zu strukturieren:

- **Research v1.0 fertig**
- **Live-Track v1.0 als „Beta-ready" (streng gegated, kein Blindflug)**

Dazu werden sieben Micro-Phasen definiert, die auf dem bestehenden Stand (Strategy-Library v1.1, StrategyProfiles & Tiering, Regime-/Portfolio-Layer, Research-Pipeline v2, Live-Playbooks/Runbooks) aufbauen.

---

## Übersicht der Micro-Phasen

| Micro-Phase | Fokus | Hauptziel |
|------------|-------|-----------|
| **Phase 80** | Research | Tiering → Portfolio-Presets & Sweeps |
| **Phase 81** | Research UX | Golden-Path-Workflows & Recipes |
| **Phase 82** | Research QA | E2E-Tests & Szenario-Library |
| **Phase 83** | Live-Gates | Tiering-/Profile-basierte Live-Gates |
| **Phase 84** | Monitoring | Operator-Dashboards & Alerts v1.0 |
| **Phase 85** | Live-Beta Drill | Kompletter Dry-Run (Shadow/Testnet) |
| **Phase 86** | Freeze & Tag | Research v1.0 Freeze + Live-Beta Label |

---

## Phase 80 – Tiered Portfolio Presets v1.0 (Research)

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

## Phase 85 – Live-Beta Drill (Shadow/Testnet)

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
| 81    | Research Golden Paths & Recipes         | 16    | ✅     |
| 82    | Research QA & Szenario-Library          | 28    | ✅     |
| 83    | Live-Gating & Risk Policies v1.0        | 27    | ✅     |
| 84    | Operator Dashboards & Alerts v1.0       | 15    | ✅     |
| 85    | Live-Beta Drill (Shadow/Testnet)        | 40    | ✅     |
| 86    | Research v1.0 Freeze & Live-Beta Label  | -     | ✅     |
| **Summe** |                                      | **159** | ✅  |

**Neue / erweiterte Komponenten (Auszug):**

- **Config**
  - `config/portfolio_presets/` (3 Presets)
  - `config/scenarios/` (3 Szenarien)
  - `config/live_policies.toml`
- **Source**
  - `src/experiments/portfolio_presets.py`
  - `src/live/live_gates.py`
- **Scripts**
  - `scripts/run_research_golden_path.py`
  - `scripts/operator_dashboard.py`
  - `scripts/run_live_beta_drill.py`
- **Tests**
  - `tests/test_portfolio_presets_tiering.py`
  - `tests/test_research_golden_paths.py`
  - `tests/test_research_e2e_scenarios.py`
  - `tests/test_live_gates.py`
  - `tests/test_operator_dashboard.py`
  - `tests/test_live_beta_drill.py`
- **Doku**
  - `docs/PHASE_80_TIERED_PORTFOLIO_PRESETS.md`
  - `docs/PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md`
  - `docs/PHASE_82_RESEARCH_QA_AND_SCENARIOS.md`
  - `docs/PHASE_83_LIVE_GATING_AND_RISK_POLICIES.md`
  - `docs/PHASE_84_OPERATOR_DASHBOARD.md`
  - `docs/PHASE_85_LIVE_BETA_DRILL.md`
  - `docs/PHASE_86_RESEARCH_V1_FREEZE.md`

**Aktueller Gesamtstatus:**

- ✅ **Research v1.0 abgeschlossen (Scope-Freeze)**
- ✅ Vollständige Research-Pipeline mit Golden Paths & QA-Szenarien
- ✅ Tiered Portfolio Presets mit automatischer Eligibility (core/aux/legacy)
- ✅ Shadow-/Testnet-Stack in einem Live-Beta-Drill validiert
- ⚠️ **Live-Beta:** Shadow/Testnet als produktionsreifer Pfad, echtes Live bleibt weiterhin streng gegated und bewusst als „Beta" markiert.