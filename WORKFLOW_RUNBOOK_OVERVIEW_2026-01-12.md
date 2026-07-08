# Peak_Trade – Workflow & Runbook Übersicht

**Stand:** 2026-01-12  
**Version:** v1.0  
**Zweck:** Zentrale Übersicht aller Workflow- und Runbook-Dokumentation

---

## 📊 Executive Summary

Peak_Trade verfügt über eine **umfassende, 2026-ready Workflow- und Runbook-Infrastruktur** mit:

- **18+ CLI-Kommando-Sektionen** vollständig dokumentiert
- **12+ Standard & Incident Runbooks** für Live-Operations
- **Control Center** mit Layer-Matrix (L0-L6) & Evidence-System
- **100+ PR Merge Logs** für vollständige Nachvollziehbarkeit
- **Governance-first & Evidence-first** Approach
- **Safety-Sandbox** für Offline-Testing

---

## 📘 Installation & Roadmap (Snapshot 2026-01-12)

Für eine vollständige Installation (0→ready) und die Roadmap 2026 inkl. Governance-Gate für Phase 13:

- [INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md](INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md)
- [docs/INSTALLATION_QUICKSTART.md](docs/INSTALLATION_QUICKSTART.md)

Hinweis: Phase 13 (Production Live-Trading) erfordert explizites Governance-Gate-Approval (Details im verlinkten Snapshot).

---

## 🎯 Hauptdokumente (Quick Reference)

### 0. Workflow Notes & Policy
**Pfad:** `docs/ops/workflows/`  
**Zielgruppe:** Docs maintainers, PR authors, Workflow developers

**Key Documents:**
- [WORKFLOW_NOTES_FRONTDOOR.md](docs/ops/workflows/WORKFLOW_NOTES_FRONTDOOR.md) — Policy for illustrative path encoding (`&#47;`)
- [PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md](docs/ops/workflows/PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md) — Historical workflow snapshot
- [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](docs/ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md) — Troubleshooting docs gate failures
- [RUNBOOK_PR736_CI_SNAPSHOT_AUTOMERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md](docs/ops/runbooks/RUNBOOK_PR736_CI_SNAPSHOT_AUTOMERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md) — PR #736: CI snapshot → auto-merge enable → post-merge verify (main) (snapshot-only)
- [RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md](docs/ops/runbooks/RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md) — Local Docs Gates Snapshot (Changed Scope) — Operator Runbook (Cursor Multi-Agent)

**Purpose:** Documents illustrative example path policy (prevents docs-reference-targets-gate false positives) and provides historical workflow context.

### 1. CLI Cheatsheet
**Pfad:** `docs/CLI_CHEATSHEET.md`  
**Umfang:** 18 Hauptsektionen, ~690 Zeilen  
**Zielgruppe:** Entwickler, Operatoren, Research

#### Hauptsektionen:

| Sektion | Beschreibung | Wichtigste Commands |
|---------|--------------|---------------------|
| **1-2** | Einzelne & Portfolio-Backtests | `run_backtest.py`, `run_portfolio_backtest.py` |
| **2.1** | Portfolio-Recipes & Presets | `research_cli.py portfolio --portfolio-preset` |
| **3-5** | Parameter-Sweeps & Market-Scans | `run_sweep.py`, `run_market_scan.py`, `run_forward_signals.py` |
| **6** | Live-Workflows | `preview_live_orders.py`, `check_live_risk_limits.py`, `paper_trade_from_orders.py` |
| **7-9** | Auto-Portfolio-Builder | `build_auto_portfolios.py`, `analyze_experiments.py` |
| **10-11** | Strategie-Registry & Exchange-Tools | `inspect_exchange.py`, `scan_markets.py` |
| **11.1** | Live Portfolio Monitoring | `preview_live_portfolio.py` |
| **12** | Live-Ops CLI | `live_ops.py orders&#47;portfolio&#47;health` |
| **13** | Live Status Reports | `generate_live_status_report.py` |
| **14** | Scheduler & Job Runner | `run_scheduler.py` |
| **15-18** | Testnet-Orchestrator, Live Monitor, Alerts, Web-Dashboard | `testnet_orchestrator_cli.py`, `live_monitor_cli.py`, `live_alerts_cli.py`, `live_web_server.py` |

**Wichtigste Quick-Commands:**

```bash
# Health-Check
python scripts/live_ops.py health --config config/config.toml

# Portfolio-Snapshot
python scripts/live_ops.py portfolio --config config/config.toml

# Testnet-Status
python scripts/testnet_orchestrator_cli.py status

# Live Monitor
python scripts/live_monitor_cli.py overview --only-active

# Web-Dashboard starten
python scripts/live_web_server.py
```

---

### 2. Wave3 Control Center Cheatsheet v2
**Pfad:** `docs/ops/runbooks/Wave3_Control_Center_Cheatsheet_v2.md`  
**Stand:** 2026-01-08  
**Zielgruppe:** Operatoren, PR-Management

#### Kernfeatures:

**PR-Queue Management (Top 10):**

| PR# | Branch | Status | Risiko | Tier | Next Action |
|-----|--------|--------|--------|------|-------------|
| 608 | docs/pr607-merge-log | MERGEABLE | Low→Med | A | Lokale Änderungen prüfen → commit/push → merge |
| 604 | docs/ops-evidence-linking | MERGEABLE | Low | B | Checks → Diff → merge |
| 592 | docs/frontdoor-roadmap-runner | MERGEABLE | Med | C | Lint/Audit verifizieren → merge |
| 601 | evidence-index-v0.1 | CONFLICTING | Med | B | Rebase/Regenerate → merge |
| ... | ... | ... | ... | ... | ... |

**Pre-Flight Checks:**
```bash
cd /Users/frnkhrz/Peak_Trade
pwd && git rev-parse --show-toplevel && git status -sb
```

**Entscheidungsbaum:**
- **MERGEABLE (docs-only):** Checks → Diff → Merge
- **MERGEABLE (Tier C):** Checks (Lint/Audit) + Review → Merge
- **CONFLICTING:** Checkout → Rebase → Regenerate → Push → Merge

**Tier B Evidence v0.1:**
- `EV-20260103-CI-HARDENING` existiert
- Nächste Kandidaten: Wave3 Session, Runbooks Core, Merge Logs

---

### 3. AI Autonomy Control Center Operator Cheatsheet
**Pfad:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATOR_CHEATSHEET.md`  
**Stand:** 2026-01-09  
**Scope:** View-only / Docs-only Ops

#### Daily Routine (5–10 Minuten):

**Checklist:**
- [ ] GitHub Checks: required gates "green" (snapshot)
- [ ] Control Center Dashboard: lädt stabil (kein Timeout)
- [ ] Evidence: bei Abweichung → Operator Notes mit Timestamp

**"Wenn X, dann Y" Entscheidungsbaum:**
- Required gate rot → **Incident Triage starten (S2)**
- Dashboard timeout → **Timeout-sichere Methode + Evidence (S1)**
- Verdacht Scope Drift → **SCOPE_KEEPER aktivieren (S3)**

**Evidence Minimum (immer):**
- Timestamp (Europe/Berlin)
- Check-Name (exakt)
- 1 Screenshot oder 1 CLI Snippet
- 3 bullets: Symptom, Ursache, nächster Schritt

**Timeout-Safe Monitoring:**
- ❌ Kein Dauer-Streaming
- ✅ Status snapshots + manuelles Refresh
- ✅ "Attempt #" bei wiederholten Timeouts dokumentieren

**Triage Shortcuts:**
- **docs-reference-targets-gate:** Nicht existierende Targets / path-ähnliche Strings neutralisieren
- **Link Debt Trend:** Markdown-Hygiene, keine "nackten" Targets
- **Policy / Guardrails:** Stop → Eskalation → Evidence sichern

---

## 📚 Detaillierte Runbooks

### LIVE_OPERATIONAL_RUNBOOKS.md
**Pfad:** `docs/LIVE_OPERATIONAL_RUNBOOKS.md`  
**Version:** v1.6  
**Umfang:** ~1990 Zeilen, 12+ Runbooks

#### Standard-Runbooks (Operations):

| # | Runbook | Anwendungsfall | Zeitaufwand |
|---|---------|----------------|-------------|
| **2** | Testnet-Run starten | Testnet-Session hochfahren | 10-15 Min |
| **3** | Live-Run (Small Size) starten | Erster echter Live-Betrieb | 20-30 Min |
| **4** | Systemstart nach Wartung | Wiederanlauf nach Pause/Update | 15-20 Min |
| **5** | Sicheres Beenden laufender Sessions | Normales Herunterfahren | 5-10 Min |
| **6** | System-Health-Check | Tägliche Prüfung | 5-10 Min |
| **10a.10** | Shadow-/Testnet-Session mit Phase-80-Runner | Strategy-to-Execution Bridge | 15-20 Min |
| **12a** | Live-Track Panel Monitoring | Dashboard-basiertes Session-Monitoring | Laufend |
| **12b** | Live-Track Session Explorer | Filter, Detail, Stats-API | 5-15 Min |

#### Incident-Runbooks (Troubleshooting):

| # | Runbook | Anwendungsfall | Schweregrad |
|---|---------|----------------|-------------|
| **7** | Exchange-Fehler behandeln | API-Fehler, Timeouts, Rate-Limits | Medium-High |
| **7a** | Netzwerk-Fehler behandeln | Request timeout, Connection error | Medium |
| **7b** | Rate-Limit-Fehler behandeln | Rate limit exceeded | Low-Medium |
| **7c** | Authentication-Fehler behandeln | API-Keys ungültig | **High** |
| **8** | Risk-Limit-Verletzung | Umgang mit blockierten Orders | Medium |
| **9** | Auffällige PnL-Divergenzen | Performance weicht stark ab | Medium-High |
| **10** | Unvollständige Daten / Data-Gaps | Fehlende Marktdaten | Medium |

#### Spezial-Runbooks (Phase 64-67, 80-85):

| # | Runbook | Phase | Beschreibung |
|---|---------|-------|--------------|
| **10a** | Testnet-Orchestrator v1 | 64 | Multi-Run-Management, Status, Events |
| **10b** | Monitoring & CLI-Dashboards v1 | 65 | Live-Monitoring-System, Run-Übersicht |
| **10c** | Alerts & Incident Notifications v1 | 66 | PnL-Drop, No-Events, Error-Spike Rules |
| **10d** | Live Web Dashboard v0 | 67 | REST-API, HTML-Dashboard mit Auto-Refresh |
| **10a.10** | Phase-80-Runner | 80 | Strategy-to-Execution Bridge |
| **12a** | Live-Track Panel Monitoring | 82 | Dashboard-basiertes Session-Monitoring |
| **12b** | Live-Track Session Explorer | 85 | Filter, Detail-Ansicht, Statistiken |

#### Wichtige Command-Beispiele:

**Testnet-Orchestrator (10a):**
```bash
# Shadow-Run starten
python scripts/testnet_orchestrator_cli.py start-shadow \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --timeframe 1m

# Status aller Runs
python scripts/testnet_orchestrator_cli.py status

# Events tailen
python scripts/testnet_orchestrator_cli.py tail --run-id <RUN_ID> --limit 50
```

**Live Monitor (10b):**
```bash
# Run-Übersicht
python scripts/live_monitor_cli.py overview --only-active

# Run-Details
python scripts/live_monitor_cli.py run --run-id <RUN_ID>

# Live-Tailing
python scripts/live_monitor_cli.py follow --run-id <RUN_ID> --refresh-interval 2.0
```

**Alerts (10c):**
```bash
# Alle Checks
python scripts/live_alerts_cli.py run-rules \
  --run-id <RUN_ID> \
  --pnl-drop-threshold-pct 5.0 \
  --no-events-max-minutes 10 \
  --error-spike-max-errors 5
```

**Web-Dashboard (10d):**
```bash
# Dashboard starten
python scripts/live_web_server.py

# Mit Custom-Parametern
python scripts/live_web_server.py \
  --host 0.0.0.0 \
  --port 9000 \
  --auto-refresh-seconds 10
```

**Wichtige URLs:**
- Dashboard: `http://localhost:8000/`
- Health-Check: `http://localhost:8000/health`
- Runs-Liste (JSON): `http://localhost:8000/runs`
- Run-Snapshot (JSON): `http://localhost:8000/runs/{run_id}/snapshot`

---

### RUNBOOKS_LANDSCAPE_2026_READY.md
**Pfad:** `docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md`  
**Version:** v1.1 (Dezember 2025)  
**Zweck:** Zentrale Runbook-Tabelle & Quick-Reference

#### Zentrale Runbook-Tabelle:

| Runbook | Pfad | Version | Scope / Zweck | Primary Cluster | Layer | Status |
|---------|------|---------|---------------|-----------------|-------|--------|
| **ExecutionPipeline Governance & Risk** | `docs/runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md` | v1.1 | Governance & Risk für ExecutionPipeline | Phase 16A | Execution & Governance | ✅ 2026-ready |
| **Live Risk Severity Integration** | `docs/runbooks/LIVE_RISK_SEVERITY_INTEGRATION.md` | v1.0 | Severity-Ampel (GREEN/YELLOW/RED) | Cluster 80–81 | Live-Risk, Monitoring | ✅ 2026-ready |
| **Live Alert Pipeline** | `docs/runbooks/LIVE_ALERT_PIPELINE_SLACK_EMAIL_RUNBOOK_V1.md` | v1.0 | Alert-Pipeline (Slack, E-Mail) | Cluster 82–83 | Alerts & Monitoring | ✅ 2026-ready |
| **Incident Runbook Integration** | `docs/runbooks/INCIDENT_RUNBOOK_INTEGRATION_V1.md` | v1.0 | Incident-Handling, Alert-Mapping | Cluster 84 | Incident-Management | ✅ 2026-ready |
| **Go/No-Go 2026** | `docs/GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md` | v1.0 | Live Alerts & Escalation-Freigabe | Cluster 82–85 | Governance, Decision-Gates | ✅ 2026-ready |
| **R&D-Runbook Armstrong & El Karoui** | `docs/runbooks/R_AND_D_RUNBOOK_ARMSTRONG_EL_KAROUI_V1.md` | v1.0 | R&D-Experimente | Phase 78 | R&D, Research | ⚠️ R&D only |
| **R&D-Playbook Armstrong & El Karoui** | `docs/runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md` | v1.0 | Best Practices, Parameter-Sweeps | Phase 78 | R&D, Methodik | ⚠️ R&D only |
| **Armstrong × El Karoui Cross-Run Findings** | `docs/runbooks/ARMSTRONG_ELKAROUI_CROSS_RUN_FINDINGS_V1.md` | v1.0 | Meta-Analyse, Findings | Phase 78 | R&D, Meta-Analyse | ⚠️ R&D only |
| **Offline-Realtime-Pipeline** | `docs/runbooks/OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md` | v1.0 | Safety-Sandbox (synthetische Ticks) | Phase 16A | Offline Testing | ✅ Safety-Sandbox |

#### Quick-Reference: Welche Situation → Welches Runbook?

| Situation | Relevante Runbooks | Kommentar |
|-----------|-------------------|-----------|
| **Pre-Session-Check vor Live/Paper-Session** | ExecutionPipeline Governance & Risk, Live Risk Severity Integration | Daily Checks, Risk-Ampel prüfen |
| **Order wird blockiert (ExecutionStatus ≠ OK)** | ExecutionPipeline Governance & Risk, Go/No-Go 2026 | Status-Code nachschlagen, Entscheidungsbaum |
| **RED Severity im Live-Dashboard** | Live Risk Severity Integration, Incident Runbook, Go/No-Go 2026 | Severity-Runbook folgen, Incident eröffnen |
| **Unklare Incident-Ursache** | Live Alert Pipeline, Incident Runbook Integration | Alert-Pipeline debuggen |
| **Neue Alerts / Änderungen Escalation** | Go/No-Go 2026, Live Alert Pipeline | Nur über Go/No-Go-Prozess |
| **R&D-Strategie Armstrong/El Karoui** | R&D-Runbook, R&D-Playbook | Setup & Methodik prüfen |
| **Execution-Pipeline offline testen** | Offline-Realtime-Pipeline | Synthetische Ticks + Paper-Execution |

---

### RUNBOOKS_AND_INCIDENT_HANDLING.md
**Pfad:** `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`  
**Version:** Phase 25/56  
**Zweck:** Grundlegende Runbooks für Shadow-Modus, System-Pause, und Incident-Handling-Prozesse

#### Kern-Runbooks:
- **Shadow-Run:** Durchführung von Shadow-/Dry-Runs mit vollständiger Checkliste (Konfiguration, Durchführung, Ergebnisse, Troubleshooting)
- **System pausieren/stoppen:** Sichere Pausierung bei unerwartetem Verhalten, Scheduler-Management, Log-Sicherung
- **Incident-Handling:** Schweregrade (Low/Medium/High), Reaktionsschema (Sofortmaßnahmen → Analyse → Behebung → Post-Mortem), Incident-Report-Vorlage
- **Vorbereitung Testnet/Live:** Platzhalter für zukünftige Runbooks (Start/Stop Testnet/Live, Kill-Switch, Graceful Degradation, Position Liquidation)

**Zielgruppe:** Operatoren, Entwickler (Shadow-Modus + erste Incident-Response-Prozesse)  
**Status:** ✅ Aktiv (Shadow-Modus), ⚠️ Platzhalter für Live-Runbooks (Stufe 4)

**Verwandte Dokumente:**
- [INCIDENT_SIMULATION_AND_DRILLS.md](docs/INCIDENT_SIMULATION_AND_DRILLS.md) — Praktische Übungen und Drill-Szenarien
- [LIVE_OPERATIONAL_RUNBOOKS.md](docs/LIVE_OPERATIONAL_RUNBOOKS.md) — Erweiterte Runbooks für Testnet/Live
- [INCIDENT_DRILL_LOG.md](docs/INCIDENT_DRILL_LOG.md) — Dokumentation durchgeführter Übungen

---

### RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md
**Pfad:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md`  
**Stand:** 2026-01-09  
**Version:** v0.1  
**Scope:** Docs-only / Operator Workflow

#### Kernprinzipien (Guardrails):

- **No-Live / Governance-Locked:** Keine Live-Trading-Ausführung
- **Evidence-first:** Jede Aussage auf Artefakt/Log/Doc referenziert
- **Determinismus:** Reproduzierbare Änderungen
- **SoD / Separation of Duties:** Operator dokumentiert, Reviewer bestätigt

#### Entry Points (Single Source of Truth):

1. **Primary:** `docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md`
2. **Navigation:** `docs/ops/control_center/CONTROL_CENTER_NAV.md`
3. **Ops README Index:** `docs/ops/README.md` → Abschnitt „AI Autonomy Control Center"

#### Operator Rollenmodell:

| Rolle | Verantwortung | Hut |
|-------|---------------|-----|
| **SHIFT OPERATOR** | Daily Routine + Triage, Operator Output | Operations |
| **CI GUARDIAN** | CI Gates prüfen, Status dokumentieren | CI/CD |
| **REVIEWER** | PRs/Governance-Änderungen prüfen, Go/No-Go | Review |

#### Daily / Shift Routine (10–15 Minuten):

**Pre-Check:**
1. Öffne `AI_AUTONOMY_CONTROL_CENTER.md`
2. Scanne **At-a-glance KPIs**
3. Scanne **Layer Status Matrix (L0–L6)**

**Minimaler Daily-Status (Pflicht):**
- Datum / Zeitfenster
- Layer-Status (L0–L6): OK / WARN / FAIL
- CI Gate Snapshot: PASS / FAIL / UNKNOWN
- Neue Evidence-Artefakte vorhanden? (ja/nein)

**Output-Format:** Siehe Abschnitt 9 (Operator Output Template)

#### Layer-Triage Playbook (L0–L6):

**Ziel:** Einheitliche Interpretation
- **OK:** Keine offenen Findings, Artefakte vollständig, CI Gates grün
- **WARN:** Non-blocking Findings / Degradations
- **FAIL:** Blocking Gate / fehlende Artefakte / Policy-Verstoß

**Triage-Checkliste (für jeden Layer):**
1. Status in Matrix prüfen
2. Evidence prüfen (Run Manifest / Operator Output)
3. CI Gates prüfen (7 required checks)
4. Troubleshooting anwenden
5. Entscheidung dokumentieren: Monitor / Fix Required / Escalate

**Standard-Trigger für WARN/FAIL:**
- Fehlende/nicht auflösbare Doc-Links
- Evidence Pack unvollständig
- CI Gate Failure in required checks
- Policy/Guardrail Konflikt

#### CI Gates Verifikation (Required Checks):

**7 Required Checks:**
1. Prüfe aktuellen Status im PR/Commit Kontext
2. Dokumentiere: PASS/FAIL pro Gate
3. Dokumentiere: Run-ID / Commit SHA / PR #
4. Dokumentiere: Timestamp

> Wenn CI unbekannt: als **UNKNOWN** markieren, nicht als PASS!

#### Troubleshooting (Standardfälle):

**1. Docs Reference Targets Gate fail:**
- Symptome: "missing reference targets" oder Text als Pfad interpretiert
- Fix: Branch/Code-Pfade in Inline-Code setzen, echte Links korrigieren

**2. "CI Watch" timeouts / hängt:**
- Vorgehen: Polling statt watch, zuletzt abgeschlossene Runs prüfen
- Dokumentiere: Alternative + Zeitpunkt

**3. Layer Matrix zeigt WARN/FAIL ohne Artefakte:**
- Control Center Navigation → Evidence / Runbooks
- Fehlende Artefakte explizit notieren
- Issue/PR für Artefakt-Nachlieferung

---

## 🏗️ Operations-Struktur

### Verzeichnis-Übersicht: `docs/ops/`

**Control Center:**
- `control_center&#47;AI_AUTONOMY_CONTROL_CENTER.md`
- `control_center&#47;CONTROL_CENTER_NAV.md`

**Evidence & Audit:**
- `EVIDENCE_INDEX.md` - Zentrale Evidence-Verwaltung
- `EVIDENCE_SCHEMA.md` - Evidence-Artefakt-Schema
- `evidence&#47;` - Evidence-Artefakte
- `EVIDENCE_ENTRY_TEMPLATE.md` - Template für neue Evidence

**CI/CD & Branch Management:**
- `BRANCH_PROTECTION_REQUIRED_CHECKS.md`
- `CI_HARDENING_SESSION_20260103.md`
- `REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md`
- `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`
- `ci_required_checks_matrix_naming_contract.md`

**Merge Logs:**
- `merge_logs&#47;` - Über 100+ PR Merge Logs
- `MERGE_LOG_TEMPLATE_COMPACT.md`
- `MERGE_LOG_TEMPLATE_DETAILED.md`
- `MERGE_LOG_WORKFLOW.md`

**Runbooks:**
- `runbooks&#47;` - Spezifische Runbooks
- `KILL_SWITCH_RUNBOOK.md`
- `EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md`
- `POLICY_CRITIC_TRIAGE_RUNBOOK.md`

**Guides:**
- `guides&#47;` - Operator-Guides
- `DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md`
- `POLICY_SAFE_DOCUMENTATION_GUIDE.md`
- `PR_MANAGEMENT_TOOLKIT.md`

**Wave Management:**
- `WAVE3_QUICKSTART.md`
- `WAVE3_OPERATOR_BRIEFING.md`
- `WAVE3_MERGE_READINESS_MATRIX.md`
- `wave3_restore_queue.md`

---

## 🔄 Workflow-Dokumentation

### WORKFLOW_NOTES.md
**Pfad:** `docs/WORKFLOW_NOTES.md`  
**Stand:** 03.12.2025  
**Zweck:** ChatGPT ↔ Claude Code ↔ Repo Workflow

#### Rollenaufteilung:

| Rolle | Verantwortung |
|-------|---------------|
| **Frank (Owner)** | Entscheidet nächsten Block/Fokus |
| **ChatGPT (Co-Pilot)** | Erstellt große, in sich geschlossene Prompts |
| **Claude Code** | Führt Änderungen im Repo aus |

#### Typischer Ablauf:

1. **Frank:** Sagt Fokus, z.B. "weiter mit Position Sizing"
2. **ChatGPT:** Liefert großen Textblock ("Claude-Code-Prompt")
3. **Frank:** Kopiert Prompt in Claude Code, lässt ausführen
4. **Frank:** Führt ggf. `python scripts/...` aus
5. **Frank:** Meldet zurück: "Alle Aufgaben erfolgreich!"
6. **ChatGPT:** Geht davon aus, Block ist umgesetzt, liefert nächsten Prompt

#### Stilregeln:

- **Sprache:** Deutsch (außer Code/Docs)
- **Ton:** Locker, technisch präzise, Emojis erlaubt 😄
- **Struktur:** Klar getrennte Abschnitte (1️⃣, 2️⃣, 3️⃣)
- **Am Ende:** "Abschlussbericht"-Anweisungen für Claude

#### Aktueller technischer Stand:

> **Venue clarification:** Kraken is not the current canonical target venue (`default_exchange=okx_europe_eea`).

**Data-Layer:** ✅ Loader, Normalizer, Cache, legacy Kraken public-OHLCV (nicht kanonischer Ziel-Venue; default_exchange=okx_europe_eea)  
**Strategy-Layer:** ✅ BaseStrategy, MACrossover, RsiReversion, DonchianBreakout  
**Core-Layer:** ✅ Config, PositionSizing, RiskManagement  
**Backtest-Layer:** ✅ BacktestEngine, Stats  
**Registry:** ✅ Strategy Registry, build_strategy_from_config  
**Runner:** ✅ Spezifische & generischer Runner

**Nächster Block:** Doku & Architektur (vorbereitet)

---

## 📍 Aktuelle Arbeitsschwerpunkte

### Control Center (Wave3)

**Layer Status Matrix (L0-L6):**
- **L0:** Foundation (Config, Core Utils)
- **L1:** Data Layer
- **L2:** Strategy Layer
- **L3:** Execution Layer
- **L4:** Risk & Governance Layer
- **L5:** Monitoring & Alerting Layer
- **L6:** Operations & Documentation Layer

**Prinzipien:**
- **Evidence-first:** Jede Aussage dokumentiert
- **Timeout-Safe Monitoring:** Polling statt Streaming
- **7 Required CI Gates:** Mandatory für Merge
- **No-Live / Governance-Locked:** Keine Live-Ops ohne Freigabe

### PR-Management (Wave3)

**Aktuelle Top 10 PRs:**
- **PR #608:** docs/pr607-merge-log (MERGEABLE, Low→Med, Tier A)
- **PR #604:** docs/ops-evidence-linking (MERGEABLE, Low, Tier B)
- **PR #592:** docs/frontdoor-roadmap-runner (MERGEABLE, Med, Tier C)
- **PR #601:** evidence-index-v0.1 (CONFLICTING, Med, Tier B)
- **PR #598-#587:** CONFLICTING (Rebase/Regenerate erforderlich)
- **PR #586:** DRAFT (Backlog)

**Workflow:**
1. **MERGEABLE (docs-only):** Checks → Diff → Merge
2. **MERGEABLE (Tier C):** Checks (Lint/Audit) + Review → Merge
3. **CONFLICTING:** Checkout → Rebase → Regenerate → Push → Merge

**Tier-Entscheidungen:**
- **Tier A:** Merge Logs, Operator Notes (Low Risk)
- **Tier B:** Evidence Index, Runbooks Core (Med Risk)
- **Tier C:** Scripts, Workflows, CI-Integration (Med-High Risk)

### Evidence v0.1

**Existierende Evidence:**
- `EV-20260103-CI-HARDENING` ✅

**Nächste Kandidaten:**
- Wave3 Session
- Runbooks Core
- Merge Logs Index

---

## 🎯 Quick-Access Übersicht

### Zentrale Einstiegspunkte

```bash
# 1. CLI Hauptkommandos
docs/CLI_CHEATSHEET.md

# 2. Operator Daily Routine (5-10 Min)
docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATOR_CHEATSHEET.md

# 3. Wave3 PR-Management
docs/ops/runbooks/Wave3_Control_Center_Cheatsheet_v2.md

# 4. Control Center Operations
docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md

# 5. Vollständige Runbook-Landscape
docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md

# 6. Live Operations (inkl. alle 12+ Runbooks)
docs/LIVE_OPERATIONAL_RUNBOOKS.md

# 7. Evidence Index
docs/ops/EVIDENCE_INDEX.md

# 8. Workflow Notes
docs/WORKFLOW_NOTES.md

# 9. Ops README
docs/ops/README.md

# 10. Control Center (Primary)
docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md
```

### Wichtigste CLI-Commands

```bash
# ═══════════════════════════════════════════════════════════════
# TÄGLICHE OPERATIONEN
# ═══════════════════════════════════════════════════════════════

# Health-Check Live-/Testnet-Setup
python scripts/live_ops.py health --config config/config.toml

# Portfolio-Snapshot (Text)
python scripts/live_ops.py portfolio --config config/config.toml

# Portfolio-Snapshot (JSON)
python scripts/live_ops.py portfolio --config config/config.toml --json

# Testnet-Orchestrator: Status
python scripts/testnet_orchestrator_cli.py status

# Live Monitor: Übersicht
python scripts/live_monitor_cli.py overview --only-active

# Web-Dashboard starten
python scripts/live_web_server.py

# ═══════════════════════════════════════════════════════════════
# SHADOW/TESTNET-SESSIONS
# ═══════════════════════════════════════════════════════════════

# Shadow-Run starten
python scripts/testnet_orchestrator_cli.py start-shadow \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --timeframe 1m

# Testnet-Run starten
python scripts/testnet_orchestrator_cli.py start-testnet \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --timeframe 1m

# Run stoppen
python scripts/testnet_orchestrator_cli.py stop --run-id <RUN_ID>

# Events tailen
python scripts/testnet_orchestrator_cli.py tail --run-id <RUN_ID> --limit 50

# ═══════════════════════════════════════════════════════════════
# MONITORING & ALERTS
# ═══════════════════════════════════════════════════════════════

# Run-Details
python scripts/live_monitor_cli.py run --run-id <RUN_ID>

# Live-Tailing
python scripts/live_monitor_cli.py follow \
  --run-id <RUN_ID> \
  --refresh-interval 2.0

# Alerts prüfen
python scripts/live_alerts_cli.py run-rules \
  --run-id <RUN_ID> \
  --pnl-drop-threshold-pct 5.0 \
  --no-events-max-minutes 10

# ═══════════════════════════════════════════════════════════════
# BACKTESTS & RESEARCH
# ═══════════════════════════════════════════════════════════════

# Einzelner Backtest
python scripts/run_backtest.py --strategy ma_crossover --symbol BTC/EUR

# Portfolio-Backtest
python scripts/run_portfolio_backtest.py

# Parameter-Sweep
python scripts/run_sweep.py \
  --strategy ma_crossover \
  --grid config/sweeps/ma_crossover.toml

# Market-Scan
python scripts/run_market_scan.py \
  --strategy ma_crossover \
  --symbols "BTC/EUR,ETH/EUR,LTC/EUR" \
  --mode forward

# ═══════════════════════════════════════════════════════════════
# SYSTEM-CHECKS
# ═══════════════════════════════════════════════════════════════

# Tests ausführen
pytest -q --tb=no

# Readiness-Check
python scripts/check_live_readiness.py --stage testnet

# Risk-Limits prüfen
python scripts/check_live_risk_limits.py
```

---

## ✅ Status-Zusammenfassung

### Dokumentation

| Kategorie | Status | Umfang | 2026-ready |
|-----------|--------|--------|------------|
| **CLI Cheatsheet** | ✅ Vollständig | 18 Sektionen, 690 Zeilen | ✅ Ja |
| **Live Operational Runbooks** | ✅ Vollständig | 12+ Runbooks, 1990 Zeilen | ✅ Ja |
| **Runbooks Landscape** | ✅ Vollständig | 9 Runbooks katalogisiert | ✅ Ja |
| **Control Center Operations** | ✅ Vollständig | Layer L0-L6, CI Gates | ✅ Ja |
| **Wave3 Cheatsheets** | ✅ Vollständig | PR-Management, Daily Routine | ✅ Ja |
| **Workflow Notes** | ✅ Vollständig | ChatGPT↔Claude↔Repo | ✅ Ja |
| **Evidence System** | ✅ v0.1 | Index, Schema, Templates | ✅ Ja |
| **Merge Logs** | ✅ 100+ PRs | Vollständige Nachvollziehbarkeit | ✅ Ja |

### Architektur-Prinzipien

| Prinzip | Status | Beschreibung |
|---------|--------|--------------|
| **Governance-first** | ✅ Etabliert | No-Live ohne explizite Freigabe |
| **Evidence-first** | ✅ Etabliert | Jede Aussage dokumentiert |
| **Safety-Sandbox** | ✅ Verfügbar | Offline-Testing ohne Risiko |
| **Separation of Duties** | ✅ Etabliert | Operator/Reviewer-Rollen getrennt |
| **CI/CD Gates** | ✅ Mandatory | 7 Required Checks für Merge |
| **Audit-fähig** | ✅ Vollständig | Merge Logs, Evidence, Runbooks |

### Tool-Verfügbarkeit

| Tool | CLI | Web-Dashboard | Status |
|------|-----|---------------|--------|
| **Live-Ops** | ✅ | ✅ | Vollständig |
| **Testnet-Orchestrator** | ✅ | ✅ | v1 (Phase 64) |
| **Live Monitor** | ✅ | ✅ | v1 (Phase 65) |
| **Alerts** | ✅ | ✅ | v1 (Phase 66) |
| **Web-Dashboard** | — | ✅ | v0 (Phase 67) |
| **Phase-80-Runner** | ✅ | — | v0 (Phase 80) |
| **Live-Track Panel** | — | ✅ | v1 (Phase 82) |
| **Session Explorer** | — | ✅ | v1 (Phase 85) |

---

## 🧹 Repo Hygiene / Cleanup Inventory (Snapshots)

**Status:** Phase 7 Finish/Closeout completed (snapshot-based inventory established)  
**Scope:** Documentation-only, NO actions without explicit operator approval

### Runbook & Inventory
- **Phase 7 Runbook:** [RUNBOOK_PHASE7_WORKFLOW_DOCS_FINISH_CLOSEOUT_2026-01-12_CURSOR_MULTI_AGENT.md](docs/ops/runbooks/RUNBOOK_PHASE7_WORKFLOW_DOCS_FINISH_CLOSEOUT_2026-01-12_CURSOR_MULTI_AGENT.md)
- **Post-Merge Verify Snapshot (main) — PR #734:** [RUNBOOK_POST_MERGE_VERIFY_SNAPSHOT_MAIN_PR734_2026-01-14_CURSOR_MULTI_AGENT.md](docs/ops/runbooks/RUNBOOK_POST_MERGE_VERIFY_SNAPSHOT_MAIN_PR734_2026-01-14_CURSOR_MULTI_AGENT.md)
- **Cleanup Inventory (Snapshots):** [docs/ops/_archive/repo_cleanup/2026-01-12/](docs/ops/_archive/repo_cleanup/2026-01-12/README.md)

### Key Features
- **Snapshot-Only:** Branch/worktree/artifact inventory (read-only)
- **Safety Protocol:** Two-stage approval process (Preview → Execute)
- **Guardrails:** NO branch deletions, NO worktree operations without explicit approval
- **Classifications:** [merged], [unmerged], [gone], [worktree-protected]

**Phase 7 Status:** ✅ Snapshot inventory complete, links validated

---

## 📋 Checklisten

### Daily Operator Checklist (5-10 Min)

```
TÄGLICHE ROUTINE:
□ Control Center öffnen (AI_AUTONOMY_CONTROL_CENTER.md)
□ At-a-glance KPIs scannen
□ Layer Status Matrix (L0-L6) prüfen
□ GitHub Checks: 7 required gates (snapshot)
□ Control Center Dashboard: Stabilität prüfen
□ Bei Abweichungen: Operator Notes mit Timestamp
□ Bei required gate rot: Incident Triage starten
□ Bei Dashboard timeout: Timeout-sichere Methode nutzen
□ Neue Evidence-Artefakte dokumentieren
□ Daily-Status in Operator Output schreiben
```

### Pre-Session Checklist (Shadow/Testnet)

```
VOR SESSION-START:
□ Environment-Mode korrekt (paper/testnet)
□ Strategie in Config definiert
□ Live-Risk-Limits konfiguriert
□ Readiness-Check ausgeführt (PASSED)
□ Health-Check ausgeführt (OK)
□ Dashboard verfügbar
□ Monitoring-Terminal bereit
□ Logs-Verzeichnis geprüft
```

### Post-Session Checklist (Shadow/Testnet)

```
NACH SESSION-ENDE:
□ Dashboard refreshen
□ Session in Liste sichtbar
□ Status = "completed" (grün)
□ Realized PnL dokumentieren
□ Max Drawdown < Limit (z.B. < 5%)
□ Notes-Feld auf Auffälligkeiten prüfen
□ Registry-Eintrag verifizieren
□ Report-CLI ausführen
□ Ergebnisse interpretieren
□ Bei Auffälligkeiten: Incident-Runbook anwenden
□ Operator Output schreiben
```

### PR-Merge Checklist (MERGEABLE)

```
PR-MERGE (DOCS-ONLY):
□ Export GH_PAGER und PAGER setzen
□ PR Checks prüfen (statusCheckRollup)
□ Alle required checks PASS
□ PR Diff anzeigen (erste 200 Zeilen)
□ Diff inhaltlich prüfen
□ Bei Auffälligkeiten: Review anfordern
□ Merge ausführen (squash, delete-branch)
□ Checkout main + pull --ff-only
□ Git status prüfen (clean)
□ Merge Log erstellen (optional bei docs-only)
```

### Incident-Response Checklist

```
BEI INCIDENT:
□ Severity einschätzen (Low/Medium/High)
□ Betroffenes System identifizieren
□ Entsprechendes Incident-Runbook öffnen
□ Schritt-für-Schritt-Anweisungen folgen
□ Artefakte sichern (Logs, Config, Screenshots)
□ Run-ID / Session-ID / PR # dokumentieren
□ Timestamp (Europe/Berlin) festhalten
□ 3 bullets: Symptom, Ursache, nächster Schritt
□ Bei High-Severity: Owner informieren
□ Nach Behebung: Incident-Report erstellen
□ Post-Mortem planen (bei High-Severity)
```

---

## 🔗 Referenzen & Cross-Links

### Governance & Safety

- `SAFETY_POLICY_TESTNET_AND_LIVE.md` - Safety-Policies
- `GOVERNANCE_AND_SAFETY_OVERVIEW.md` - Governance-Übersicht, Rollen
- `docs/ops/P0_GUARDRAILS_QUICK_REFERENCE.md` - P0 Guardrails
- `docs/governance/` - Governance-Dokumente

### CI/CD & Branch Protection

- `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md` - Required Checks
- `docs/ops/CI_HARDENING_SESSION_20260103.md` - CI Hardening
- `docs/ops/ci/` - CI-Workflows & -Konfiguration

### Evidence & Audit

- `docs/ops/EVIDENCE_INDEX.md` - Evidence-Registry
- `docs/ops/EVIDENCE_SCHEMA.md` - Evidence-Schema
- `docs/ops/evidence/` - Evidence-Artefakte
- `docs/audit/` - Audit-Berichte

### Phase-Dokumentation

- `PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md` - Strategy-to-Execution Bridge
- `PHASE_81_LIVE_SESSION_REGISTRY.md` - Live-Session-Registry
- `PHASE_82_LIVE_TRACK_DASHBOARD.md` - Live-Track Panel
- `PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md` - Operator-Workflow
- `PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md` - Demo Walkthrough
- `PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md` - Session Explorer

---

## 📝 Changelog

| Version | Datum | Änderungen |
|---------|-------|------------|
| **v1.0** | 2026-01-12 | Initial erstellte Übersicht basierend auf aktuellem Peak_Trade-Stand |

---

## 📞 Support & Kontakt

Bei Fragen oder Problemen:

1. **Dokumentation prüfen:** Dieser Workflow/Runbook-Übersicht
2. **Runbook konsultieren:** Relevantes Runbook aus `docs/runbooks/` oder `docs/LIVE_OPERATIONAL_RUNBOOKS.md`
3. **Control Center:** `docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md`
4. **Incident-Runbook:** Bei Problemen entsprechendes Incident-Runbook anwenden
5. **Eskalation:** Bei Unsicherheit Owner informieren

---

**Stand:** 2026-01-12  
**Nächste Aktualisierung:** Nach größeren Änderungen an Workflow/Runbooks oder quarterly review

---

*Diese Übersicht ist ein lebendes Dokument. Bei Änderungen an Prozessen, Architektur oder Runbooks sollte sie aktualisiert werden.*
