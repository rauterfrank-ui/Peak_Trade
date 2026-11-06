# Peak_Trade – Vollständiges Audit (Runbook + Checklist + Report-Template)

Stand: 2025-12-30 (Europe/Berlin)

Dieses Dokument ist als **Audit-Paket** gedacht: Du kannst es 1:1 ins Repo übernehmen (z.B. unter `docs/audit/`), als Arbeitsgrundlage für ein vollständiges System-Audit bis hin zur **Live-Trade Go/No-Go Entscheidung**.

---

## 0) Ziel und Definition „vollständig“

Ein „vollständiges Audit“ ist hier **evidenzbasiert** und endet nicht bei Code-Review, sondern umfasst:

1. **Korrektheit** (Backtest/Simulation/Execution-Verträge, deterministische Ergebnisse)
2. **Safety & Governance** (Killswitch, Gating, Live/Shadow/Bounded-Auto, Change-Control)
3. **Risk Controls** (Limits, Exposure, Drawdown, Order-Risk, Circuit Breaker)
4. **Security** (Secrets, Keys, Supply Chain, Zugriff, Logging von sensiblen Daten)
5. **Operations** (Runbooks, Monitoring/Alerting, Incident Response, Rollback)
6. **Reproduzierbarkeit** (Build, Lockfiles, CI, Artefakt-Erzeugung, Reports)
7. **Compliance-Readiness** (Audit Trail, Datenherkunft, Aufbewahrung, Verantwortlichkeiten)

**Definition of Done (DoD):**
- Es existiert ein `AUDIT_REPORT.md` mit **Evidence-Index**, **Findings**, **Risikoregister**, **Remediation-Plan** und **Go/No-Go**.
- Alle P0 Findings sind geschlossen oder formal akzeptiert (mit Owner + Ablaufdatum + Kompensation).
- Live-Trade ist nur zulässig, wenn Go/No-Go „GO“ und die notwendigen Gates aktiv sind.

---

## 1) Audit-Deliverables (Repo-Struktur)

Empfohlene Ablage:

```
docs/audit/
  AUDIT_MASTER_PLAN.md
  AUDIT_CHECKLIST.md
  AUDIT_REPORT.md
  EVIDENCE_INDEX.md
  RISK_REGISTER.md
  GO_NO_GO.md
  findings/
    FND-0001.md
    FND-0002.md
  evidence/
    snapshots/
    commands/
    ci/
    screenshots/
scripts/audit/
  run_audit_snapshot.py
  run_audit_commands.sh
```

Minimal-Set (wenn du schlank starten willst):
- `docs/audit/AUDIT_REPORT.md`
- `docs/audit/EVIDENCE_INDEX.md`
- `docs/audit/RISK_REGISTER.md`

---

## 2) Audit-Phasen (Runbook)

### Phase A0 – Scope Freeze & Audit Setup (1–2h)
**Ziel:** Audit-Zeitpunkt definieren (Commit/PR), Audit-Owner, Artefakt-Struktur anlegen.

**Tasks**
- Audit-Baseline: `git rev-parse HEAD` notieren
- `docs/audit/` anlegen
- Evidence-Namenskonvention festlegen (Datum, Commit, Host)

**Outputs**
- `AUDIT_MASTER_PLAN.md` (Scope, Rollen, Zeitplan)
- `EVIDENCE_INDEX.md` initial

---

### Phase A1 – Inventory & Architektur-Überblick (2–4h)
**Ziel:** Was ist im System? Welche Subsysteme? Welche Datenflüsse?

**Evidence**
- Repo Tree Snapshots (Top-Level + `src/` + `scripts/` + `docs/`)
- High-level Diagramm (Text reicht): Daten → Strategie → Sizing → Risk → Orders → Execution → Ledger/Reports

**Outputs**
- Architektur-Abschnitt in `AUDIT_REPORT.md`
- Liste der „kritischen Pfade“ (Live relevant)

---

### Phase A2 – Build, CI, Reproduzierbarkeit (2–6h)
**Ziel:** Auditierbarer Build, deterministische Runs, CI-Policies verstehen.

**Checks**
- Dependencies/Lockfiles vorhanden und konsistent
- CI Gates: required checks, Policy guards, docs gates, tests matrix
- Repro: identische Inputs → identische Outputs (Snapshots/Seeds)

**Evidence**
- CI Run Links + Logs
- `pip&#47;uv` freeze / lockfile
- `pytest` Ergebnis + `ruff`/`mypy` (falls genutzt)

---

### Phase A3 – Backtest-Korrektheit & Research Hygiene (4–12h)
**Ziel:** Backtest Engine, Signal→Position→PnL Pipeline und Kennzahlen korrekt.

**Checks**
- Lookahead Bias / leakage
- Gebühren/Slippage/Latency Modell
- Portfolio Accounting: fills/fees/ledger
- Reconciliation: Positions vs ledger

**Evidence**
- Goldens: ausgewählte Backtests mit festen Seeds + Snapshots
- Tests, die Invarianten abdecken (PnL, exposure bounds)

---

### Phase A4 – Risk Layer & Limits (4–12h)
**Ziel:** Limits sind durchgängig, nicht umgehbar, und greifen im Live-Pfad.

**Checks**
- Pre-trade checks (order sizing, max notional, max leverage, open orders)
- Runtime checks (drawdown halt, equity floor, circuit breakers)
- Governance: live allowlist, strategy switch sanity checks, “manual_only” default

**Evidence**
- Konfig-Beispiele (redacted)
- Unit-Tests für risk policies + runtime hook coverage

---

### Phase A5 – Execution Pipeline & Exchange Integration (4–16h)
**Ziel:** Order-Lifecycle ist robust: idempotent, retries, partial fills, cancellation.

**Checks**
- Order states & transitions
- Idempotency keys / clientOrderId
- Retry policy & rate limits
- Failure modes: disconnect, stale data, rejected orders
- Shadow/Testnet vs Live: hart getrennt

**Evidence**
- Sequence diagrams / state machine
- Test harness / simulations
- Logs (redacted) + recon diffs

---

### Phase A6 – Security & Secrets (2–8h)
**Ziel:** Keine Secrets im Repo, keine Leaks in Logs, Supply-chain minimiert.

**Checks**
- Secrets scanning (gitleaks/detect-secrets)
- `.env` / keyfiles ausgeschlossen
- Logging policy: keys/tokens nie loggen
- Dependency scanning (pip-audit/safety)

**Evidence**
- Scan Reports + Remediations
- Zugriffskonzept (wo liegen Keys, wie werden sie geladen)

---

### Phase A7 – Ops Readiness (4–16h)
**Ziel:** Operator kann Live sicher fahren: Monitoring, Alerting, Incidents, Rollback.

**Checks**
- Runbooks: deploy, rollback, incident, exchange outage, data outage
- Monitoring/Alerting: risk breaches, trade anomalies, latency spikes
- Audit Trail: wer hat was wann getan (operator actions)

**Evidence**
- Runbook Index + Drill-Protokolle
- Screenshots/Logs aus Dry-Run Drills

---

### Phase A8 – Go/No-Go Board (2–4h)
**Ziel:** Formales Gate: alle Findings klassifiziert; GO nur bei erfüllten Bedingungen.

**Outputs**
- `GO_NO_GO.md`
- `RISK_REGISTER.md` final
- `AUDIT_REPORT.md` final (mit Sign-off)

---

## 3) Severity-Klassifikation (P0–P3)

- **P0 Blocker:** Kann zu unkontrolliertem Loss, unautorisierten Trades oder Secret Leak führen.
- **P1 High:** Kann in Stress-Case zu signifikantem Fehlverhalten führen; muss vor Live gelöst oder kompensiert werden.
- **P2 Medium:** Verbesserungen/Hardening; kann nach Live in bounded mode geplant werden.
- **P3 Low:** Hygiene / Doku / Nice-to-have.

---

## 4) Template: Findings (pro Finding eine Datei)

Datei: `docs/audit/findings/FND-0001.md`

- **Titel:**
- **Severity:** P0/P1/P2/P3
- **Subsystem:** (Data/Strategy/Backtest/Risk/Execution/Ops/Security/CI)
- **Beschreibung:** Was ist das Problem?
- **Impact:** Warum relevant (Failure mode)?
- **Evidence:** Links/Logs/Code-Stellen
- **Repro Steps:** (wenn möglich)
- **Fix Plan:** konkrete Schritte
- **Owner:** Name/Rolle
- **Due Date:**
- **Status:** Open / In progress / Fixed / Accepted (mit Begründung)

---

## 5) Template: Risk Register

Datei: `docs/audit/RISK_REGISTER.md`

Spalten (oder Bullet pro Risk):
- Risk ID
- Beschreibung
- Likelihood (L/M/H)
- Impact (L/M/H)
- Mitigation
- Detection
- Owner
- Status
- Review Date

---

## 6) Template: Evidence Index

Datei: `docs/audit/EVIDENCE_INDEX.md`

Einträge:
- **EV-0001:** Repo Snapshot (tree, counts) – Pfad / Command Output
- **EV-0002:** CI Required Checks – Screenshot/Log
- **EV-0003:** Tests Matrix – Log
- **EV-0004:** Secrets Scan – Report
- …
Jeder Finding verweist auf mindestens ein Evidence Item.

---

## 7) Recommended Commands (Operator)

Diese Kommandos sind bewusst „konservativ“ formuliert; falls du `uv` nutzt, ersetze entsprechend.

### Repo & Build Snapshot
```bash
git status
git rev-parse HEAD
git remote -v
python3 --version
pip --version
pip freeze | head
```

### Tests / Lint (wenn im Projekt vorhanden)
```bash
python3 -m pytest -q
ruff check .
# mypy .   # optional
```

### Basic Secret Scan (wenn Tools installiert)
```bash
gitleaks detect --no-git --redact
detect-secrets scan --all-files
pip-audit
```

### Quick Grep für Live-Risiko-Flags
```bash
rg -n "live\s*=\s*true|LIVE|api_key|secret|private_key|clientOrderId|kill\s*switch" -S src/ scripts/ docs/
```

---

## 8) Cursor Multi-Agent: Orchestrator Prompt (Copy/Paste)

**Wo einsetzen:** Cursor → Multi-Agent / Agent Chat (Orchestrator)

> Ziel: Agenten parallel arbeiten lassen (Inventory, CI/Quality, Security, Risk, Execution, Ops).  
> Jeder Agent liefert Evidence-Links/Paths und schreibt Findings in `docs/audit/findings/`.

```text
Du bist der Audit-Orchestrator für das Repo „Peak_Trade“. Arbeite strikt evidenzbasiert.

0) Lege folgende Dateien an (falls noch nicht vorhanden):
- docs/audit/AUDIT_REPORT.md
- docs/audit/EVIDENCE_INDEX.md
- docs/audit/RISK_REGISTER.md
- docs/audit/GO_NO_GO.md
- docs/audit/findings/ (Ordner)

1) Teile die Arbeit in 6 Agenten auf:
A) Inventory & Architektur
B) Build/CI/Repro
C) Backtest Correctness
D) Risk Layer & Governance
E) Execution & Order Lifecycle
F) Security & Secrets + Ops Readiness (Runbooks/Monitoring)

2) Jeder Agent:
- Sammelt Evidence (konkrete Dateipfade, Logs, grep Ergebnisse, CI Artefakte).
- Identifiziert Findings (P0–P3) und erstellt pro Finding eine Datei docs/audit/findings/FND-XXXX.md.
- Trägt Evidence Items in docs/audit/EVIDENCE_INDEX.md ein.
- Aktualisiert docs/audit/RISK_REGISTER.md (nur risks, nicht findings).

3) Abschluss:
- Synthese in docs/audit/AUDIT_REPORT.md (Executive Summary, System Overview, Findings Summary, Remediation Plan).
- Entscheidungsvorlage in docs/audit/GO_NO_GO.md mit klaren Kriterien und Status (GO/NO-GO).
- Keine Vermutungen: Wenn etwas nicht auffindbar ist, als Gap dokumentieren.

Wichtig:
- Keine Secrets in Outputs (redact).
- Keine Live-Trades oder Live-API Calls ausführen.
```

---

## 9) Template: AUDIT_REPORT.md (Skeleton)

Datei: `docs/audit/AUDIT_REPORT.md`

```md
# Peak_Trade Audit Report

## Executive Summary
- Audit Baseline (Commit):
- Scope:
- Ergebnis (GO/NO-GO):
- P0/P1 Findings Count:

## System Overview
- Architektur (Subsysteme, Datenfluss):
- Live-kritische Pfade:

## Evidence Summary
- Verweis auf EVIDENCE_INDEX.md

## Findings Summary
### P0 Blockers
- FND-XXXX: ...
### P1 High
- ...
### P2 Medium
- ...
### P3 Low
- ...

## Remediation Plan
- Priorisierte Maßnahmen (Owner, ETA)

## Residual Risk & Acceptance
- akzeptierte Risiken (Begründung, Ablaufdatum)

## Appendix
- Commands executed
- CI runs
- Snapshots
```

---

## 10) Template: GO_NO_GO.md (Skeleton)

```md
# Go/No-Go Decision – Peak_Trade

## Preconditions
- Alle P0 geschlossen: [ ]
- P1 entweder geschlossen oder akzeptiert mit Kompensation: [ ]
- Secrets Scan clean: [ ]
- Risk Gates aktiv (Killswitch, manual_only default, limits): [ ]
- Dry-run drill durchgeführt und dokumentiert: [ ]

## Decision
- Status: GO / NO-GO
- Datum:
- Verantwortliche:
- Kommentare:

## Outstanding Items
- ...
```

---

## 11) Optional: Automatisches Audit Snapshot Script (Pure Python)

Wenn du das automatisieren willst: `scripts/audit/run_audit_snapshot.py` soll
- Repo-Baum grob erfassen (counts pro Ordner)
- Quick keyword scan (nur patterns, keine Secrets ausgeben)
- Outputs unter `docs/audit/evidence/snapshots/` schreiben

(Implementierung bewusst ausgelassen, damit du sie passend zu deinem Repo-Layout erzeugen kannst.)

---

### Nächster Schritt (praktisch)
1) Lege `docs/audit/` an und committe das Audit-Paket (docs-only).
2) Lass Cursor Multi-Agent die 6 Audit-Stränge parallel abarbeiten.
3) Reviewe P0/P1 Findings und entscheide, ob wir ein Remediation-Sprint planen oder direkt ins Go/No-Go gehen.
