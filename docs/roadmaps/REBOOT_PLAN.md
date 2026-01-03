# REBOOT PLAN

**Zweck:** Operative Prinzipien und Mapping für den Roadmap-Reboot (V2).

---

## Prinzipien

### 1. Safety & Governance First
- **Alle Live-Execution-Paths** müssen durch Governance-Gates.
- **Risk-Limits** sind mandatory, nicht optional.
- **Kill-Switch** muss testbar und dokumentiert sein.
- **No Silent Bypasses:** Jede Umgehung eines Gates muss auditierbar sein (Log-Entry).

### 2. Deterministisch & Reproduzierbar
- **Backtest-Ergebnisse** müssen bit-identical sein bei gleichem Input.
- **Registry-Logging** ist Pflicht für alle Runs (Backtest, Paper, Live).
- **Seed-Management:** Random-Seeds in Config, nicht hardcoded.
- **Data-Versioning:** Parquet-Cache mit Hash-Checksums.

### 3. CI-First & Test-Coverage
- **Kein Merge ohne grüne CI.**
- **Test-Coverage >80%** für kritische Pfade (Execution, Risk, Backtest).
- **Smoke-Tests <5s**, Full-Suite <90s.
- **Flaky-Tests** werden als P0-Bugs behandelt.

### 4. "No Magic Auto-Live"
- **Auto-Promotion-Loops** bleiben im R&D-Status.
- **Live-Deployment** nur nach manuellem Review + Checklist.
- **Shadow-Runs** sind Pflicht vor Testnet-Deployment.
- **Real-Money-Execution** nur nach explizitem Go/No-Go-Review.

### 5. Docs als Code
- **Docs leben im Repo**, nicht in externen Tools.
- **Docs sind versioniert** (Git).
- **Docs werden im PR reviewed** (wie Code).
- **Broken Links = CI-Failure** (via Markdown-Link-Checker).

---

## Governance & Release Flow (Mini-Checklist)

### A. Feature-Development
1. **Branch:** `feature/<name>` oder `docs/<name>`
2. **Entwicklung:** Code + Tests + Docs im PR
3. **PR-Review:** Min. 1 Approval (bei Solo-Dev: Self-Review mit Checklist)
4. **CI-Check:** Alle Tests grün, Linter happy
5. **Merge:** Squash-Merge nach `main` (oder `dev` je nach Workflow)

### B. Live-Deployment (Testnet)
1. **Shadow-Run:** Min. 24h Shadow-Execution auf Paper
2. **Governance-Gate:** `check_live_readiness.py` → PASS
3. **Risk-Config-Review:** Limits konservativ, Kill-Switch aktiv
4. **Approval:** Dokumentiertes Go (z.B. Issue, Checklist-File)
5. **Deployment:** Start via `scripts/live/run_live_session.py`
6. **Monitoring:** Erste 4h aktiv überwacht (Alerts, Logs)

### C. Live-Deployment (Real-Money)
1. **Alle Testnet-Schritte** erfolgreich abgeschlossen
2. **Risk-Gate-Review:** VaR, Liquidity, Stress-Szenarien validiert
3. **Incident-Runbook:** Vorhanden und getestet (Drill durchgeführt)
4. **Approval:** Explizites Go/No-Go-Meeting (dokumentiert)
5. **Soft-Launch:** Minimale Position-Sizes (z.B. 1% Portfolio)
6. **Ramp-Up:** Schrittweise Erhöhung über 2–4 Wochen

---

## Mapping-Tabelle: "Keep / Freeze / Replace / Rebuild"

### Keep (Unverändert weiternutzen)

| Komponente                  | Begründung                                      |
|-----------------------------|-------------------------------------------------|
| `src/data/`                 | Funktioniert, Tests ok, keine Bugs              |
| `src/backtest/engine.py`    | Core-Engine stabil, nur Bugfixes               |
| `src/strategies/` (OOP)     | Neue Strategie-Klassen sind gut strukturiert   |
| `src/core/peak_config.py`   | Config-Loader ist robust                        |
| `src/live/risk_limits.py`   | Risk-Limits funktionieren, nur Extensions nötig |
| `tests/` (Smoke + Unit)     | Test-Suite ist grün, nur ergänzen              |
| `scripts/run_backtest.py`   | Funktioniert, keine Änderungen nötig           |

### Freeze (Nicht weiter expandieren, aber behalten)

| Komponente                       | Begründung                                          |
|----------------------------------|-----------------------------------------------------|
| `src/strategies/legacy/`         | Legacy-Strategien bleiben für Backwards-Compat      |
| Auto-Promotion-Loop              | Bleibt im R&D-Status, kein Ausbau ohne Review      |
| Macro-Regime-Module (alt)        | Wird durch P7 (Regime-Detection-V2) ersetzt        |
| RL-basierte Strategien           | Bleiben in `archive/`, kein aktives Development    |
| Multi-Exchange-Integrations      | Nur Kraken/Binance, keine weiteren Exchanges       |

### Replace (Schrittweise ersetzen)

| Alt                              | Neu                                     | Phase |
|----------------------------------|-----------------------------------------|-------|
| Manuelle Governance-Checklists   | `scripts/governance/check_live_readiness.py` | P2    |
| Ad-hoc Order-Logging             | `src/execution/telemetry.py` (strukturiert) | P3    |
| Basic Risk-Limits                | Liquidity + Stress Gates (P4)          | P4    |
| Lokale Backtest-Logs             | WebUI-Dashboard (P6)                   | P6    |
| Manual Regime-Annotation         | HMM-basierte Regime-Detection (P7)     | P7    |

### Rebuild (Neu schreiben, alte Version deaktivieren)

| Komponente                       | Begründung                                          | Phase |
|----------------------------------|-----------------------------------------------------|-------|
| Shadow-Execution-Replay          | Alte Version zu fragil, kein Diff-Support          | P5    |
| Multi-Strategy-Portfolio-Backtest | Alte Implementierung fehlt Correlation-Metriken    | P8    |
| Observability (Ad-hoc-Logs)      | Prometheus + Grafana als Standard                  | P9    |

---

## Scope-Boundaries (Was NICHT gemacht wird)

### Out-of-Scope für Reboot V2
- **RL-Strategien:** Bleiben in Archive, kein aktives Development.
- **Auto-Deployment-Pipelines:** Keine CD für Live-Execution (nur CI für Tests).
- **Multi-Currency-Portfolios:** Nur Single-Currency (z.B. USD oder EUR) pro Portfolio.
- **High-Frequency-Trading:** Kein Sub-Second-Execution (Latenz-Optimierung out-of-scope).
- **WebUI Write-Ops:** Dashboard bleibt Read-Only (keine Order-Placement via UI).
- **Real-Money-Live ohne Testnet:** Testnet ist mandatory Gate vor Real-Money.

### Debt & Backlog (Nach Reboot)
- **Order-Queue-Modul** (für gleichzeitige Orders in Multi-Strat-Portfolios) → P10+
- **Advanced Position-Sizing** (Kelly-Criterion, Risk-Parity) → P10+
- **Exchange-Aggregation-Layer** (Multi-Exchange-Routing) → V3
- **Mobile-App / Telegram-Bot** (Alert-Delivery) → V3
- **Machine-Learning-Feature-Store** (für RL/ML-Strategien) → V3

---

## Release-Versionierung

| Version | Scope                                      | Status      |
|---------|--------------------------------------------|-------------|
| v1.0    | MVP (Backtest, Registry, Paper-Trade)      | ✅ Deployed |
| v1.1    | Live-Track-Dashboard, Smoke-Tests          | ✅ Deployed |
| v2.0    | Reboot-Roadmap P0–P9                       | 🚧 In Arbeit |
| v3.0    | Multi-Exchange, RL-Strategien, Real-Money  | 📅 Geplant  |

---

## Kommunikation & Tracking

### Wo wird gearbeitet?
- **Branch:** `docs/reboot-roadmap-v2` (für P0), dann Feature-Branches per Phase.
- **Issues:** GitHub Issues mit Labels `reboot-v2`, `p0`–`p9`, `risk`, `governance`.
- **PR-Templates:** Checklist mit Exit-Criteria pro Phase (in `.github/PULL_REQUEST_TEMPLATE.md`).

### Wer entscheidet?
- **Solo-Dev:** Self-Review mit expliziter Checklist (dokumentiert im PR).
- **Team-Setup:** Min. 1 Approval + CI-Green.
- **Live-Execution:** Go/No-Go-Review mit dokumentiertem Outcome (Issue + Approval-Comment).

### Wo wird dokumentiert?
- **Roadmap:** `docs/roadmaps/REBOOT_ROADMAP_V2.md` (diese Datei ist Single-Source-of-Truth).
- **Phase-Details:** `docs/<domain>/PHASE_<N>_<NAME>.md` (z.B. `docs/governance/PHASE_P2_LIVE_EXECUTION_GATE.md`).
- **Lessons Learned:** `docs/roadmaps/REBOOT_LESSONS_LEARNED.md` (nach P9).

---

## Risiko-Mitigation

| Risk                                  | Likelihood | Impact | Mitigation                                      |
|---------------------------------------|------------|--------|-------------------------------------------------|
| CI-Tests werden flaky (P1)            | MED        | HIGH   | Daily Monitoring, Flaky-Test-Report (P1)       |
| Governance-Gate zu strikt (P2)        | MED        | MED    | Bypass-Log + Review-Loop nach 2 Wochen         |
| Regime-Detection instabil (P7)        | HIGH       | MED    | Fallback auf Rule-Based (RSI+ATR)              |
| Multi-Strat-Portfolio Timing-Bug (P8) | MED        | HIGH   | Order-Queue-Modul als P10 (Debt), jetzt FIFO   |
| Observability-Overhead (P9)           | LOW        | LOW    | Sampling-Rate konfigurierbar (default: 100%)    |

---

**Dokument-Ende**
