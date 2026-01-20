# WP4A — Live Readiness & Governance-Lock Packet

**Phase:** 4 (Manual-Only Live Readiness)  
**Status:** Active  
**Version:** 1.0  
**Last Updated:** 2026-01-01  
**Owner:** Operator / Governance

---

## 1. Purpose & Non-Goals

### Purpose

Dieses Dokument definiert den **Governance-gestützten Prozess** für den Übergang von Shadow/Testnet zu hypothetischem Live-Trading. Es handelt sich um ein **Operator-Handbuch** für manuelle, strikt gegatete Verfahren — **NICHT** um eine technische Aktivierungsanleitung.

**Kernziele:**
- Definiere **Pre-Flight Requirements** und **Readiness Gates**
- Dokumentiere **Evidence Requirements** (Artefakte, Nachweise, Audits)
- Spezifiziere **Governance-Lock Semantik** (wer, was, wie)
- Etabliere **Go/No-Go Decision Framework**
- Definiere **Rollback & Abort Criteria**
- Beschreibe **Drill-Prozeduren** (ohne Live-Aktivierung)

### Non-Goals

**Was dieses Dokument NICHT ist:**
- ❌ Keine Schritt-für-Schritt Aktivierungsanleitung für Live-Trading
- ❌ Keine technischen Konfigurationsbeispiele mit aktivierten Live-Flags
- ❌ Keine Credentials, Secrets oder API-Key Management
- ❌ Keine automatischen Aktivierungsskripte oder "One-Click-Deploy"

**Sicherheitsrichtlinie:**
- Keine Beispiele mit `enable_*=true` Semantik für Live-Aktivierung
- Nur `BLOCKED&#47;SHADOW&#47;PAPER` Beispiele (siehe `docs/ops/POLICY_SAFE_DOCUMENTATION_GUIDE.md`)
- Fokus auf **Gating, Verantwortlichkeiten, Nachweise, Drills**

---

## 2. Definitions

| Begriff | Definition |
|---------|------------|
| **Shadow Mode** | Execution-Pipeline läuft gegen Live-Daten, Orders werden simuliert (nicht gesendet) |
| **Testnet** | Execution gegen Testnet-API (z.B. Binance Testnet); echte API-Calls, aber kein echtes Geld |
| **LIVE_BLOCKED** | System ist technisch ready, aber durch Governance-Gates blockiert |
| **Manual-Only** | Keine automatisierten Aktivierungspfade; jede Stufe erfordert manuelles Sign-off |
| **Governance-Lock** | Explizite Kontrolle durch Governance-Rolle; Unlock nur nach formaler Review |
| **Sign-off** | Formale Zustimmung durch definierte Rolle (dokumentiert mit Datum + Unterschrift/Login) |
| **Gate** | Technischer oder prozessualer Checkpoint; muss PASS sein für Fortschritt |
| **Evidence** | Dokumentierter Nachweis (Log, Report, Audit, Test-Ergebnis) mit eindeutiger ID |
| **Drill** | Simulierte Prozedur (z.B. Rollback-Drill) ohne Änderung am Live-System |
| **Go/No-Go** | Formales Meeting mit binärer Entscheidung: Fortfahren (GO) oder Abbrechen (NO-GO) |

---

## 3. Roles & RACI

### Rollen

| Rolle | Verantwortlichkeiten |
|-------|---------------------|
| **Operator** | Führt Pre-Flight Checks aus, sammelt Evidence, moderiert Go/No-Go Meeting |
| **Reviewer** | Peer-Review von Checklisten, Code, Config; validiert Evidence-Pack |
| **Risk** | Validiert Risk-Limits, Kill-Switch, Monitoring; Sign-off für Risk-Gates |
| **Governance/Policy Critic** | Final Sign-off für Governance-Lock Unlock; prüft Policy-Compliance |

### RACI Matrix

| Task | Operator | Reviewer | Risk | Governance |
|------|----------|----------|------|------------|
| Pre-Flight Checklisten erstellen | R | A | C | I |
| Evidence Pack sammeln | R | C | C | I |
| Go/No-Go Meeting moderieren | R | C | C | A |
| Risk-Gate Sign-off | I | C | R/A | C |
| Governance-Lock Unlock | I | C | C | R/A |
| Drill Execution | R | C | C | I |
| Rollback Execution (falls nötig) | R | A | C | I |

**Legende:** R=Responsible, A=Accountable, C=Consulted, I=Informed

---

## 4. Pre-Flight Requirements

Vor Beginn des Gate-Prozesses müssen folgende **Baseline-Anforderungen** erfüllt sein:

### 4.1 Repository Cleanliness

- [ ] Main Branch ist clean (keine uncommitted changes)
- [ ] Alle CI-Checks auf Main sind grün
- [ ] Kein P0/P1 Linter Error in kritischen Modulen (`src/live/`, `src/risk/`, `src/execution/`)
- [ ] Secrets-Scan ist clean (keine hardcoded API-Keys, Credentials)
- [ ] `.gitignore` blockiert sensitive Files (`.env`, `*.key`, `credentials.json`)

**Verification Commands:**
```bash
git status                                    # Muss "working tree clean" sein
make test-policy-ci                           # Policy-Pack CI muss PASS sein
rg -n "sk_live|api_key.*=.*[a-zA-Z0-9]{20}" src/ || echo "Clean"
```

### 4.2 Audit & Documentation

- [ ] Vollständiges Audit durchgeführt (siehe `docs/audit/AUDIT_MASTER_PLAN.md`)
- [ ] Go/No-Go Dokument ausgefüllt (`docs/audit/GO_NO_GO.md`)
- [ ] Evidence Index aktualisiert (`docs/audit/EVIDENCE_INDEX.md`)
- [ ] Alle Findings (P0/P1) sind RESOLVED oder ACCEPTED_RISK
- [ ] Runbooks vollständig und getestet (siehe `docs/runbooks/`)

### 4.3 Recon Gate

- [ ] Reconciliation-Pipeline ist implementiert (`src/execution/reconciliation.py`)
- [ ] Ledger-Mapper Tests sind grün (`tests&#47;execution&#47;test_ledger_mapper.py`)
- [ ] Recon-Diffs Runbook existiert (`docs/execution/RUNBOOK_RECON_DIFFS.md`)
- [ ] Dry-Run Recon erfolgreich getestet (Shadow-Mode)

### 4.4 Incident Posture

- [ ] Kill-Switch implementiert und getestet (100+ Tests)
- [ ] Rollback-Procedure dokumentiert (`docs/runbooks/ROLLBACK_PROCEDURE.md`)
- [ ] Incident Drill durchgeführt (siehe `docs/INCIDENT_DRILL_LOG.md`)
- [ ] Disaster Recovery Runbook existiert (`docs/DISASTER_RECOVERY_RUNBOOK.md`)
- [ ] On-Call Rotation definiert (falls zutreffend)

---

## 5. Readiness Gates (G0..G6)

Jedes Gate hat:
- **Gate ID** (G0, G1, ...)
- **Name**
- **Owner** (Rolle, die Sign-off gibt)
- **Checklist** (konkrete Prüfpunkte)
- **Evidence Requirements** (welche Artefakte nötig)
- **Pass Criteria** (wann gilt Gate als bestanden)

### G0: Code & CI Gate

**Owner:** Operator + Reviewer  
**Pass Criteria:** Alle Checks grün, keine P0/P1 Blocker

**Checklist:**
- [ ] Main Branch CI ist grün (Policy-Packs: ci.yml, live_adjacent.yml, research.yml)
- [ ] Test-Suite läuft durch (>5,000 Tests)
- [ ] Keine P0/P1 Linter-Errors in kritischen Modulen
- [ ] Code Coverage >80% für Execution & Risk Paths
- [ ] Secrets-Scan clean

**Evidence:**
- CI-Log (Link zu letztem CI-Run)
- Test-Coverage Report (`reports&#47;coverage_*.html`)
- Secrets-Scan Output (`make audit-secrets`)

**Sign-off:**
- Operator: ___________ Datum: ___________
- Reviewer: ___________ Datum: ___________

---

### G1: Risk Limits Gate

**Owner:** Risk  
**Pass Criteria:** Risk-Limits definiert, getestet, aktiviert

**Checklist:**
- [ ] `config/risk/` vollständig konfiguriert
- [ ] Position Size Limits definiert (`max_position_size`, `max_portfolio_value`)
- [ ] Drawdown Limits definiert (`max_daily_drawdown`, `max_total_drawdown`)
- [ ] Kill-Switch konfiguriert (`config&#47;kill_switch&#47;`)
- [ ] Risk-Layer Tests grün (`tests/risk/`)
- [ ] LiveRiskLimits implementiert (`"src\&#47;risk\&#47;live_risk_limits.py" (future; placeholder target — not in repo yet)`)
- [ ] Pre-Trade & Runtime Checks aktiv

**Evidence:**
- Risk Config Files (`config&#47;risk&#47;*.toml`)
- Kill-Switch Test Log (`pytest tests&#47;risk_layer&#47;kill_switch&#47; -v`)
- Live Risk Limits Documentation (`docs/LIVE_RISK_LIMITS.md`)

**Sign-off:**
- Risk: ___________ Datum: ___________

---

### G2: Execution Pipeline Gate

**Owner:** Operator  
**Pass Criteria:** Execution-Pipeline läuft stabil in Shadow/Testnet

**Checklist:**
- [ ] Shadow-Mode erfolgreich getestet (min. 7 Tage)
- [ ] Testnet-Mode erfolgreich getestet (falls implementiert)
- [ ] Order-Pipeline Tests grün (`tests/execution/`)
- [ ] Ledger-Mapper & Reconciliation getestet
- [ ] Execution-Telemetry aktiv (siehe `docs/execution/EXECUTION_TELEMETRY_LIVE_TRACK_V1.md`)
- [ ] Keine Order-Rejections (außer durch Risk-Gates)

**Evidence:**
- Shadow Session Logs (`live_runs&#47;*&#47;session.log`)
- Testnet Session Logs (falls vorhanden)
- Reconciliation Reports (`reports&#47;recon_*.json`)
- Telemetry Dashboard Screenshot (oder Log-Auszug)

**Sign-off:**
- Operator: ___________ Datum: ___________
- Reviewer: ___________ Datum: ___________

---

### G3: Observability & Telemetry Gate

**Owner:** Operator  
**Pass Criteria:** Monitoring, Alerting, Dashboards operational

**Checklist:**
- [ ] Live-Track Dashboard verfügbar (`templates/peak_trade_dashboard/`)
- [ ] Alert-Pipeline aktiv (`src&#47;live&#47;alerts&#47;`)
- [ ] Telemetry-Logs strukturiert und querybar (`logs/telemetry_health_snapshots.jsonl`)
- [ ] Incident-Alerts konfiguriert (Slack, Email, etc.)
- [ ] Runbook für Alert-Handling existiert (`docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md`)
- [ ] Health-Check Endpoints verfügbar (falls API vorhanden)

**Evidence:**
- Dashboard Access (URL oder Screenshot)
- Alert Test Log (`"scripts\&#47;live\&#47;test_alert_dispatch.py" (future; placeholder target — not in repo yet)`)
- Telemetry Sample Log (letzte 24h)

**Sign-off:**
- Operator: ___________ Datum: ___________

---

### G4: Incident & Runbook Gate

**Owner:** Risk + Operator  
**Pass Criteria:** Incident-Prozeduren getestet, Runbooks vollständig

**Checklist:**
- [ ] Rollback-Procedure dokumentiert (`docs/runbooks/ROLLBACK_PROCEDURE.md`)
- [ ] Kill-Switch Drill durchgeführt (siehe `docs/INCIDENT_DRILL_LOG.md`)
- [ ] Disaster-Recovery Drill durchgeführt (siehe `docs/DISASTER_RECOVERY_RUNBOOK.md`)
- [ ] Runbooks für häufige Failure-Modes existieren
- [ ] On-Call Eskalation definiert (falls zutreffend)
- [ ] Postmortem-Template existiert

**Evidence:**
- Drill Execution Logs (`docs/INCIDENT_DRILL_LOG.md`)
- Runbook Index (`docs/runbooks/`)
- Kill-Switch Test Output (`make test-kill-switch`)

**Sign-off:**
- Risk: ___________ Datum: ___________
- Operator: ___________ Datum: ___________

---

### G5: Data Integrity & Reconciliation Gate

**Owner:** Operator + Reviewer  
**Pass Criteria:** Data-Integrity sichergestellt, Recon-Pipeline operational

**Checklist:**
- [ ] Market-Data-Pipeline stabil (keine Gaps, Outliers gefiltert)
- [ ] Regime-Detection läuft (falls zutreffend)
- [ ] Reconciliation-Pipeline implementiert (`src/execution/reconciliation.py`)
- [ ] Ledger-Diffs werden automatisch erkannt und geloggt
- [ ] Recon-Diffs Runbook getestet (`docs/execution/RUNBOOK_RECON_DIFFS.md`)
- [ ] Data-QC Tests grün (`tests/data/`)

**Evidence:**
- Market-Data Quality Report (`"scripts\&#47;data\&#47;quality_check.py" (future; placeholder target — not in repo yet)`)
- Reconciliation Test Log (`pytest tests&#47;execution&#47;test_reconciliation.py`)
- Recon-Diffs Runbook Walkthrough (dokumentierter Test)

**Sign-off:**
- Operator: ___________ Datum: ___________
- Reviewer: ___________ Datum: ___________

---

### G6: Governance & Policy Compliance Gate

**Owner:** Governance/Policy Critic  
**Pass Criteria:** Policy-Compliance validiert, formales Sign-off

**Checklist:**
- [ ] Policy-Packs getestet (`policy_packs&#47;*.yml`)
- [ ] Keine Policy-Violations in kritischen Files
- [ ] Live-Aktivierung ist manual-only (keine automatischen Trigger)
- [ ] Execution-Mode Default ist SHADOW oder PAPER (nicht LIVE)
- [ ] Dokumentation ist policy-safe (siehe `docs/ops/POLICY_SAFE_DOCUMENTATION_GUIDE.md`)
- [ ] Go/No-Go Dokument finalisiert (`docs/audit/GO_NO_GO.md`)

**Evidence:**
- Policy Test Log (`make test-policy-ci`)
- Config Audit (`rg "execution_mode" config/ -A 2`)
- Documentation Scan (keine Live-Enable-Patterns)

**Sign-off:**
- Governance/Policy Critic: ___________ Datum: ___________

---

## 6. Evidence Pack

Das **Evidence Pack** ist eine strukturierte Sammlung aller Nachweise, die während des Gate-Prozesses erzeugt wurden.

### 6.1 Evidence Index Pattern

Alle Artefakte erhalten eine eindeutige **Evidence ID** nach dem Schema `EV-XXXX` (siehe `docs/audit/EVIDENCE_INDEX.md`).

**Kategorien:**
- **EV-0XXX:** Baseline & Setup
- **EV-1XXX:** Architecture & Inventory
- **EV-2XXX:** Build & CI
- **EV-3XXX:** Backtest Correctness
- **EV-4XXX:** Risk Layer
- **EV-5XXX:** Execution Pipeline
- **EV-6XXX:** Secrets & Security
- **EV-7XXX:** Monitoring & Alerts
- **EV-8XXX:** Drills & Runbooks
- **EV-9XXX:** Phase-Specific Evidence

### 6.2 Required Evidence für WP4A

| Evidence ID | Beschreibung | Location | Gate |
|-------------|--------------|----------|------|
| EV-9100 | WP4A Pre-Flight Checklist (ausgefüllt) | `docs/execution/phase4/evidence/WP4A_PREFLIGHT_CHECKLIST.md` | G0-G6 |
| EV-9101 | CI Green Snapshot (Main Branch) | `reports&#47;ci_snapshot_[date].log` | G0 |
| EV-9102 | Risk Limits Config Snapshot | `config/risk/` (commit hash) | G1 |
| EV-9103 | Shadow Session Log (7 Tage) | `live_runs&#47;shadow_[date]&#47;` | G2 |
| EV-9104 | Recon Test Results | `reports&#47;recon_test_[date].json` | G5 |
| EV-9105 | Kill-Switch Drill Log | `docs/INCIDENT_DRILL_LOG.md` | G4 |
| EV-9106 | Policy Test Results | `reports&#47;policy_test_[date].log` | G6 |
| EV-9107 | Go/No-Go Decision (ausgefüllt) | `docs/audit/GO_NO_GO.md` | All |

### 6.3 Evidence Archivierung

- Alle Evidence-Artefakte werden in `docs/execution/phase4/evidence/` abgelegt
- Commit-Hash des finalen Zustands wird dokumentiert
- Evidence Index wird aktualisiert (`docs/audit/EVIDENCE_INDEX.md`)

---

## 7. Governance-Lock Semantics

### 7.1 Was ist Governance-Lock?

**Governance-Lock** bedeutet:
- System ist technisch ready, aber durch **prozessuale Gates** blockiert
- Unlock erfordert **formales Sign-off** durch Governance-Rolle
- Jede Unlock-Aktion wird **dokumentiert** (Wer, Wann, Warum)

### 7.2 Lock-Zustände

| Zustand | Beschreibung | Unlock-Berechtigung |
|---------|--------------|---------------------|
| **LOCKED** | Default-Zustand; keine Live-Aktivierung möglich | N/A |
| **UNDER_REVIEW** | Gates werden durchlaufen; Evidence wird gesammelt | Operator |
| **APPROVED** | Alle Gates PASS; Go/No-Go Decision ist GO | Governance |
| **UNLOCKED** | Live-Aktivierung ist prozessual erlaubt (technisch weiterhin manuell) | N/A |

### 7.3 Unlock-Prozedur

**Wer darf unlocken?**  
Nur **Governance/Policy Critic** nach formalem Sign-off von:
- Operator (G0, G2, G3, G5)
- Reviewer (G0, G2, G5)
- Risk (G1, G4)
- Governance (G6)

**Unlock-Dokumentation:**
- Datum & Uhrzeit
- Governance-Login/Name
- Referenz zu Go/No-Go Decision (`docs/audit/GO_NO_GO.md`)
- Commit-Hash des Repo-Zustands

**Unlock wird dokumentiert in:**
- `docs/execution/phase4/GOVERNANCE_LOCK_LOG.md` (zu erstellen bei Unlock)

---

## 8. Drill Plan

**Ziel:** Validierung der Prozeduren ohne Änderung am Live-System.

### 8.1 Dry-Run Drills

| Drill ID | Name | Beschreibung | Häufigkeit |
|----------|------|--------------|-----------|
| DRILL-1 | Kill-Switch Activation | Trigger Kill-Switch in Shadow-Mode; validiere, dass alle Orders gestoppt werden | 1x vor Go/No-Go |
| DRILL-2 | Rollback Procedure | Führe Rollback-Prozedur durch (ohne Live-Impact); dokumentiere Dauer | 1x vor Go/No-Go |
| DRILL-3 | Recon-Diff Handling | Simuliere Ledger-Diff; validiere, dass Alert ausgelöst wird | 1x vor Go/No-Go |
| DRILL-4 | Disaster Recovery | Simuliere kompletten System-Ausfall; validiere Recovery-Prozedur | 1x vor Go/No-Go |
| DRILL-5 | Policy-Violation Injection | Provoziere Policy-Violation; validiere, dass System blockiert | 1x vor Go/No-Go |

### 8.2 Shadow Sessions

- **Dauer:** Minimum 7 Tage kontinuierlich
- **Scope:** Alle geplanten Trading-Pairs und Strategien
- **Monitoring:** Full Telemetry aktiv, alle Alerts enabled
- **Success Criteria:**
  - Keine unerwarteten Order-Rejections
  - Recon-Diffs im erwarteten Bereich (<1% Abweichung)
  - Keine kritischen Alerts (außer geplanten Drill-Alerts)

### 8.3 Failure Injection

- **Netzwerk-Disconnect:** Simuliere API-Ausfall; validiere Reconnect-Logic
- **Invalid Market Data:** Injecte Outlier; validiere Data-QC
- **Risk-Limit Breach:** Simuliere Drawdown; validiere Kill-Switch
- **Config-Error:** Injecte ungültige Config; validiere Startup-Validation

---

## 9. Go/No-Go Meeting Template

**Ziel:** Binäre Entscheidung: GO (fortfahren) oder NO-GO (abbrechen/verzögern)

### 9.1 Meeting-Agenda

1. **Opening & Roll Call** (5 min)
   - Anwesenheit: Operator, Reviewer, Risk, Governance
   - Status: Alle Teilnehmer sind bereit für Decision

2. **Gate Review** (30 min)
   - G0: Code & CI Gate — Status: _________
   - G1: Risk Limits Gate — Status: _________
   - G2: Execution Pipeline Gate — Status: _________
   - G3: Observability Gate — Status: _________
   - G4: Incident & Runbook Gate — Status: _________
   - G5: Data Integrity Gate — Status: _________
   - G6: Governance & Policy Gate — Status: _________

3. **Evidence Review** (15 min)
   - Evidence Pack vollständig? (Ja/Nein)
   - Alle Evidence IDs dokumentiert? (Ja/Nein)
   - Audit finalisiert? (Ja/Nein)

4. **Risk Assessment** (10 min)
   - Open Issues (P0/P1): _________
   - Accepted Risks: _________
   - Residual Risk Level: [LOW / MEDIUM / HIGH]

5. **Drill Results** (10 min)
   - DRILL-1: _________
   - DRILL-2: _________
   - DRILL-3: _________
   - DRILL-4: _________
   - DRILL-5: _________

6. **Go/No-Go Decision** (10 min)
   - Operator: [GO / NO-GO] — Begründung: _________
   - Reviewer: [GO / NO-GO] — Begründung: _________
   - Risk: [GO / NO-GO] — Begründung: _________
   - Governance: [GO / NO-GO] — Begründung: _________

7. **Final Decision** (5 min)
   - **Entscheidung:** [GO / NO-GO]
   - **Effective Date:** _________
   - **Next Steps:** _________

8. **Closing**
   - Meeting dokumentiert in: `docs/execution/phase4/GO_NO_GO_MEETING_LOG.md`
   - Action Items (falls NO-GO): _________

### 9.2 Sign-off Tabelle

| Rolle | Name | Decision | Datum | Unterschrift/Login |
|-------|------|----------|-------|--------------------|
| Operator | _________ | [GO / NO-GO] | _________ | _________ |
| Reviewer | _________ | [GO / NO-GO] | _________ | _________ |
| Risk | _________ | [GO / NO-GO] | _________ | _________ |
| Governance | _________ | [GO / NO-GO] | _________ | _________ |

**Final Decision:** [GO / NO-GO]  
**Authorized by:** Governance  
**Effective Date:** _________

---

## 10. Rollback & Abort Criteria

### 10.1 Abort Criteria (Stop-Gates)

**Sofortiger Abort (automatisch oder manuell) wenn:**
- [ ] Kill-Switch aktiviert wird
- [ ] Risk-Limit Breach (Drawdown > Threshold)
- [ ] Recon-Diff > 5% über >1h
- [ ] Critical Alert (P0) ausgelöst wird
- [ ] Unerwartetes System-Verhalten (Crashes, Exceptions)
- [ ] Manual Operator Intervention nötig (aber nicht verfügbar)

### 10.2 Rollback-Prozedur

**Siehe:** `docs/runbooks/ROLLBACK_PROCEDURE.md`

**Kurzfassung:**
1. **Stop all Trading Activity**
   - Trigger Kill-Switch (falls nicht bereits aktiv)
   - Alle offenen Orders canceln

2. **Assess State**
   - Ledger-Snapshot erstellen
   - Recon-Diff prüfen
   - Open Positions inventarisieren

3. **Close Positions** (falls nötig)
   - Risk-gesteuert: Positionen abbauen
   - Falls kein Market-Access: manueller Trade (außerhalb System)

4. **Switch to Safe Mode**
   - Execution-Mode zurück auf SHADOW oder PAPER
   - Config-Rollback (vorheriger Commit)

5. **Incident Documentation**
   - Postmortem erstellen
   - Root-Cause-Analysis
   - Action Items für nächsten Versuch

### 10.3 Rollback-Drill

- **Häufigkeit:** 1x vor Go/No-Go, dann quartalsweise
- **Scope:** Vollständige Rollback-Prozedur (ohne Live-Impact)
- **Dokumentation:** `docs/INCIDENT_DRILL_LOG.md`

---

## 11. Operator Quick Commands (Read-Only)

**Sicherheitshinweis:** Nur sichere, read-only Commands ohne Live-Aktivierung.

### 11.1 System-Status

```bash
# Repo-Zustand prüfen
git status
git log -1 --oneline

# CI-Status prüfen (lokal)
make test-policy-ci

# Secrets-Scan
make audit-secrets
```

### 11.2 Evidence-Sammlung

```bash
# CI-Log sichern
make test-policy-ci > reports/ci_snapshot_$(date +%Y%m%d).log

# Risk-Config Snapshot
git show HEAD:config/risk/ > reports/risk_config_snapshot_$(date +%Y%m%d).txt

# Test-Results
pytest tests/risk/ tests/execution/ --tb=short > reports/test_results_$(date +%Y%m%d).log
```

### 11.3 Gate-Checks

```bash
# G0: CI Check
make test-policy-ci

# G1: Risk-Tests
pytest tests/risk_layer/kill_switch/ -v

# G2: Execution-Tests
pytest tests/execution/ -v

# G5: Recon-Tests
pytest tests/execution/test_reconciliation.py -v

# G6: Policy-Check
rg "execution_mode" config/ -A 2
rg "enable_live_trading.*true|live_mode.*true" docs/ && echo "FAIL" || echo "PASS"
```

### 11.4 Report-Rendering

```bash
# Live-Track Report (read-only)
python scripts/reporting/render_live_track_report.py --session <session_id>

# Recon-Diffs Report
python scripts/execution/report_recon_diffs.py --date <YYYY-MM-DD>

# Telemetry Snapshot
tail -n 100 logs/telemetry_health_snapshots.jsonl
```

---

## 12. Change Log / Versioning

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|------------|
| 1.0 | 2026-01-01 | Operator | Initial Release — WP4A Live Readiness & Governance-Lock Packet |

---

## Related Documentation

- **Phase 4 Runner:** `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md` (Appendix B)
- **Audit Master Plan:** `docs/audit/AUDIT_MASTER_PLAN.md`
- **Go/No-Go Decision:** `docs/audit/GO_NO_GO.md`
- **Evidence Index:** `docs/audit/EVIDENCE_INDEX.md`
- **Live Readiness Checklists:** `docs/LIVE_READINESS_CHECKLISTS.md`
- **Rollback Procedure:** `docs/runbooks/ROLLBACK_PROCEDURE.md`
- **Incident Drills:** `docs/INCIDENT_DRILL_LOG.md`
- **Policy-Safe Documentation:** `docs/ops/POLICY_SAFE_DOCUMENTATION_GUIDE.md`
- **Live Risk Limits:** `docs/LIVE_RISK_LIMITS.md`
- **Execution Telemetry:** `docs/execution/EXECUTION_TELEMETRY_LIVE_TRACK_V1.md`

---

**END OF DOCUMENT**
