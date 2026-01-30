# Cursor Multi-Agent Runbook (Phasen) — V2

Status: Active (Docs-only)
Last updated: 2026-01-02
Owner: Ops / Operator Tooling

## 1. Zweck
Dieses Dokument ist der **zentrale Phasen-Runbook-Leitfaden** für den Cursor Multi-Agent Workflow:
- reproduzierbarer Start (Frontdoor)
- klare Rollen & Verantwortlichkeiten
- Phasen 0 → Final Live Trade als **Runbook-Phasen**
- CI-sichere Dokumentations-Regeln (keine kaputten Links)

## 2. Entry Points
- Frontdoor (Start hier): [CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md](CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md)
- Roadmap (Execution Live Track): [PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md](../execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md)

## 3. Rollen (Standard)
### 3.1 Orchestrator
- zerlegt Arbeit in kleine Work Packages (WP)
- kontrolliert Scope: Docs-only vs Code
- definiert Acceptance Criteria + Verification Commands

### 3.2 Implementer
- erstellt/ändert Dateien strikt nach Anweisung
- minimiert Diff-Fläche
- achtet auf Repo-Policies (z.B. keine kaputten Links)

### 3.3 Reviewer
- prüft Struktur, Klarheit, Konsistenz, Referenzen
- "policy-aware" Review: insbesondere docs-reference-targets-gate

### 3.4 Release/PR Driver
- Commit Message / PR Body
- Auto-merge nur wenn alle required checks grün

## 4. Protokoll (immer gleich)
1) **Scope Declaration**
   - "Docs-only" oder "Code+Docs"
2) **WP-Plan**
   - WPs nummeriert, je WP: Dateien, ACs, Risiken
3) **Implement**
4) **Review**
5) **Verification**
   - Commands (nicht ausführen, nur angeben, außer Operator will)
6) **PR Hygiene**
   - klare PR Description, Risiken, Rollback

## 5. Phasen (Runbook-Phasen)
Hinweis: Die inhaltlichen Details hängen an der Live-Execution-Roadmap. Dieses Runbook beschreibt den Operator-Flow in Cursor.

### Phase 0 — Foundation / Contracts / Docs-First
**Ziel:** stabile Docs-Grundlage, Contracts, Safety-Semantik.
**Gate:** Docs-Policies grün, keine broken links.
**Outputs (typisch):**
- Contracts/Interfaces docs
- Ops Runbooks Entry Points
**AC:**
- Neue Docs sind verlinkbar (nur existierende Targets)
- CI Docs Gates grün

### Phase 1 — Shadow Trading (Dry / OfflineRealtimeFeed)
**Ziel:** end-to-end pipeline im Shadow-Mode, keine echten Trades.
**Gate:** Execution bleibt "blocked" / "shadow"; Governance-Checks bestehen.
**Outputs (typisch):**
- Shadow session logs
- Recon/Audit evidence

### Phase 2 — Paper / Simulated Live (Exchange sandbox falls vorhanden)
**Ziel:** realistische Ausführung ohne Kapitalrisiko.
**Gate:** Risk runtime + recon/audit gates vor jeder Session.
**Operator Checklist:**
- Config: live flags bleiben aus
- Session correlation ids aktiv
- Post-run recon/audit summary erzeugen

### Phase 3 — Bounded Auto (Strictly Bounded, Manual Override)
**Ziel:** begrenzte Automatisierung mit harten Limits.
**Gate (Beispiele, nicht implementieren):**
- Max order size / max daily loss / max exposure
- Manual "Go/No-Go" vor Start
**Outputs:**
- Boundaries evidence
- Incident drill readiness

### Phase 4 — Live Readiness / Pre-Live
**Ziel:** vollständige Betriebsfähigkeit, aber Live weiterhin gesperrt bis finaler Go.
**Gate:**
- vollständige Runbooks (start/stop/incident)
- dashboards / operator visibility
- recon/audit gates stabil

### Phase 5 — Final Live Trade (Manual-Only)

#### Intent
Phase 5 ist die initiale Live-Trading-Phase unter strenger manueller Kontrolle. Jede Trading-Session wird explizit vom Operator genehmigt, überwacht und nachträglich auditiert. Das Ziel ist nicht Automatisierung, sondern kontrollierter Echtbetrieb mit vollständiger Nachvollziehbarkeit und sofortiger Stop-Fähigkeit. Der Default-Zustand bleibt "blocked" – Live-Trading muss für jede Session explizit freigegeben werden.

#### Deliverables
- **Pre-Trade Go/No-Go Checklist** — Pflicht vor jeder Live-Session (Risk Limits, Market Conditions, System Health)
- **Live Session Runlog Template** — Strukturiertes Log-Format (Start/Stop Times, Operator, Parameters, Observations)
- **Post-Trade Recon/Audit Report** — Automatisierte Reconciliation + manuelle Review-Checkliste
- **Kill-Switch Runbook** — Sofort-Stop-Prozedur (Trigger-Kriterien, Eskalation, Rollback)
- **Incident Response Playbook** — Kategorisierte Failure-Modes mit Operator-Aktionen
- **Evidence Pack Standard** — Strukturierte Ablage aller Session-Artefakte (Logs, Metrics, Fills, Rejects)

#### Entry Criteria
- Phase 4 Gate bestanden (Live Readiness Review komplett)
- Kill-Switch getestet und dokumentiert
- Operator Drill erfolgreich durchgeführt (mindestens 1x end-to-end)
- Monitoring/Alerting Baseline aktiv
- Risk Limits finalisiert und in Config versioniert
- Go/No-Go Packet von Governance genehmigt
- Two-Person Rule etabliert (Operator + Reviewer/Approver)

#### Exit Criteria
- Mindestens 5 erfolgreiche Live-Sessions ohne kritische Incidents
- Post-Trade Recon/Audit in allen Sessions grün (keine unklaren Findings)
- Kill-Switch mindestens 1x erfolgreich getestet (in Live-Session oder Drill)
- Incident Response Playbook mindestens 1x angewendet (auch bei Minor-Incidents)
- Operator Confidence erreicht (dokumentierte Selbsteinschätzung)
- Entscheidung: Übergang zu Phase 6 (Monitored Auto) ODER Verbleib in Manual-Only

#### Operator How-To
1. **Vorbereitung (T-1 Tag)**
   - Pre-Trade Checklist ausfüllen (Risk Limits, Market Outlook, System Status)
   - Change Window definieren (Start/Stop-Zeit, Duration)
   - Reviewer/Approver identifizieren (Two-Person Rule)
   - Session Runlog aus Template erstellen

2. **Go/No-Go Gate (T-0)**
   - Checklist Review mit Approver
   - Explizites "Go" erforderlich (dokumentiert im Runlog)
   - Falls "No-Go": Gründe dokumentieren, Session verschieben

3. **Live Session (T-0 bis T+Duration)**
   - Session Runlog kontinuierlich pflegen (Observations, Anomalies)
   - Monitoring Dashboard beobachten (Alerts, Latencies, Reject Rates)
   - Kill-Switch bereithalten (bei Red-Flag sofort nutzen)

4. **Post-Session (T+Duration)**
   - Trading stoppen (expliziter Stop-Command)
   - Post-Trade Recon/Audit ausführen (automatisiert + manuelle Review)
   - Findings klassifizieren (Green/Yellow/Red)
   - Session Summary im Runlog vervollständigen

5. **Evidence Pack (T+1 Tag)**
   - Alle Artefakte konsolidieren (Logs, Metrics, Fills, Runlog, Recon Report)
   - Evidence Pack in standardisiertem Format ablegen
   - Lessons Learned dokumentieren (auch bei erfolgreichen Sessions)

#### Evidence Pack
Jede Live-Session muss folgende Artefakte erzeugen und ablegen:
- **Session Runlog** (Markdown) — vollständig ausgefüllt, signiert von Operator + Reviewer
- **Pre-Trade Checklist** (ausgefüllt, mit Go/No-Go Entscheidung)
- **Execution Logs** (all orders, fills, rejects mit Timestamps und ReasonCodes)
- **Post-Trade Recon Report** (JSON + Summary Markdown)
- **Metrics Snapshot** (Latenzen, Throughput, Error Rates für Session-Duration)
- **Alert Log** (alle Alerts während Session, auch cleared)
- **Incident Log** (falls Incidents auftraten, auch Minor)
- **Lessons Learned** (1-3 bullets, auch bei "grünen" Sessions)

Ablage-Standard: `reports&#47;live_sessions&#47;YYYYMMDD_HHMMSS_<session_id>&#47;` (nicht ins Repo committen)

#### Risk Notes
- **Residual Risk Hoch:** Menschlicher Fehler bei manueller Freigabe (Mitigation: Two-Person Rule, Checklist-Disziplin)
- **Operational Risk:** Kill-Switch-Verzögerung in High-Stress-Situation (Mitigation: regelmäßige Drills)
- **Data Risk:** Unvollständige Recon/Audit-Daten bei System-Ausfall (Mitigation: redundante Log-Capture)
- **Governance Risk:** "Checklist Fatigue" nach mehreren Sessions (Mitigation: Lessons-Learned-Loop, Prozess-Optimierung erst in Phase 6)
- **Policy-Safe Framing:** Alle Dokumentation muss "manual-only" Semantik bewahren; kein Wording, das autonome Execution impliziert

---

### Phase 6 — Monitored Auto (Conditional Enablement)

#### Intent
Phase 6 erweitert Phase 5 um kontrollierte Automatisierung unter strikten Bedingungen. Der Operator aktiviert Automatisierung nur für definierte Szenarien (z.B. "low-volatility window", "bounded replay mode") und behält jederzeit Override- und Stop-Fähigkeit. Ziel ist Effizienzgewinn ohne Kontrollverlust. Der Übergang von Phase 5 zu Phase 6 ist optional und erfordert explizite Governance-Freigabe.

#### Deliverables
- **Auto-Enablement Policy** — Definiert Bedingungen für automatisierten Betrieb (Market Regime, Risk Metrics, Time Windows)
- **Conditional Gating Logic** — Runtime-Checks die Auto-Mode deaktivieren bei Policy-Violation
- **Enhanced Monitoring Dashboards** — Real-Time Visibility in Auto-Decisions (Order Intent, Risk Checks, Rejections)
- **Auto-Override Runbook** — Wie Operator Auto-Mode stoppt und zu Manual-Only zurückkehrt
- **Elevated Alerting** — Schärfere Thresholds für Auto-Mode (schnellere Eskalation)
- **Session Classification** — Klare Unterscheidung Auto vs Manual Sessions in Evidence Packs

#### Entry Criteria
- Phase 5 Exit Criteria erfüllt
- Mindestens 10 erfolgreiche Manual-Only Sessions
- Operator Team ausdrücklich bereit für Auto-Transition (dokumentiert)
- Auto-Enablement Policy finalisiert und genehmigt
- Enhanced Monitoring/Alerting getestet
- Kill-Switch funktioniert auch im Auto-Mode (verifiziert durch Drill)

#### Exit Criteria
- Mindestens 20 Auto-Sessions ohne kritische Incidents
- Auto-Override mindestens 2x erfolgreich genutzt (auch Drills zählen)
- Conditional Gating hat mindestens 1x korrekt Auto-Mode deaktiviert (Policy-Violation detected)
- Post-Trade Recon/Audit in Auto-Sessions gleiche Qualität wie Manual-Sessions
- Entscheidung: Übergang zu Phase 7 (Full Operations) ODER Rückkehr zu Phase 5 bei erhöhtem Risk-Profil

#### Operator How-To
1. **Auto-Enablement Review**
   - Auto-Enablement Policy prüfen (Bedingungen aktuell erfüllt?)
   - Market Regime Check (Volatility, Liquidity innerhalb Safe-Bounds?)
   - System Health Check (Latencies, Error Rates, Data Quality grün?)

2. **Auto-Session Start**
   - Explizite Auto-Mode Aktivierung (Flag + Logging)
   - Conditional Gates verifizieren (Runtime-Checks aktiv?)
   - Enhanced Monitoring Dashboard öffnen
   - Auto-Override Runbook griffbereit

3. **Während Auto-Session**
   - Dashboard kontinuierlich beobachten
   - Bei Yellow-Alerts: erhöhte Aufmerksamkeit
   - Bei Red-Alerts oder Intuition: sofort Auto-Override nutzen
   - Alle Operator-Interventionen im Runlog dokumentieren

4. **Auto-Session Stop**
   - Auto-Mode deaktivieren (expliziter Stop-Command)
   - Post-Trade Recon/Audit (gleicher Standard wie Phase 5)
   - Session klassifizieren (Auto-Duration, Manual-Overrides, Incidents)

#### Evidence Pack
Gleicher Standard wie Phase 5, plus:
- **Auto-Enablement Log** — Wann/Warum Auto-Mode aktiviert/deaktiviert
- **Conditional Gate Log** — Alle Runtime-Policy-Checks mit Outcomes
- **Auto-Override Log** — Alle manuellen Interventionen (auch präventive)
- **Session Classification** — Auto vs Manual Duration, Transition-Events

#### Risk Notes
- **Automation Risk:** "Set-and-Forget" Mentalität (Mitigation: Enhanced Alerting zwingt zu aktiver Überwachung)
- **Policy Drift Risk:** Conditional Gates werden zu permissive angepasst (Mitigation: Policy-Änderungen erfordern Governance-Review)
- **Complexity Risk:** Mehr Moving Parts = mehr Failure-Modes (Mitigation: Schrittweise Rollout, robuste Fallback zu Manual-Only)

---

### Phase 7 — Continuous Operations & Optimization

#### Intent
Phase 7 ist die "steady state" Operations-Phase. Trading läuft kontinuierlich (auto oder manual je nach Kontext), Operator-Fokus verschiebt sich von Session-by-Session-Control zu strategischer Überwachung, Policy-Refinement und Performance-Optimierung. Incident-Response ist etabliert, Post-Mortems werden systematisch durchgeführt, Lessons-Learned fließen in Policy-Updates und Runbook-Verbesserungen.

#### Deliverables
- **Ops Runbook Suite** — Konsolidierte Runbooks für alle Standard-Szenarien (Start/Stop, Incident, Policy-Update, Config-Change)
- **Performance Baselines** — Etablierte Benchmarks (Latencies, Fill Rates, Slippage, P&L Attribution)
- **Continuous Monitoring Dashboards** — Multi-Timeframe Views (Intraday, Daily, Weekly Trends)
- **Policy Refinement Log** — Systematisches Tracking aller Policy-Änderungen mit Begründungen
- **Incident Post-Mortem Template** — Strukturierte Root-Cause-Analysis + Corrective Actions
- **Operator Rotation Plan** — Handoff-Procedures, Knowledge-Transfer, Backup-Operator-Readiness

#### Entry Criteria
- Phase 6 Exit Criteria erfüllt
- Mindestens 50 kombinierte Sessions (Auto + Manual) ohne kritische Incidents
- Operator Team kann vollständig autonom operieren (keine externe Eskalation nötig)
- Performance Baselines etabliert (mindestens 4 Wochen Daten)
- Incident Response Playbook mindestens 3x erfolgreich angewendet
- Post-Mortem Kultur etabliert (auch für Near-Misses)

#### Exit Criteria
Phase 7 ist "steady state" — kein definiertes Exit. Evolution erfolgt durch:
- **Policy-Updates** (basierend auf Lessons-Learned)
- **Strategy-Changes** (neue Signale, Markets, Instruments)
- **Platform-Upgrades** (Infra-Migrations, API-Updates)
- **Scale-Ups** (höhere Limits, mehr Strategies)
Jede größere Änderung kann temporär Rückkehr zu Phase 5/6 erfordern (Re-Gating).

#### Operator How-To
1. **Daily Operations**
   - Morning: System Health Check, Market Regime Check
   - Intraday: Dashboard Monitoring, Alert Response
   - Evening: Daily Recon/Audit Review, Performance vs Baseline
   - End-of-Week: Trend Analysis, Policy Drift Check

2. **Incident Response**
   - Immediate: Kill-Switch bei kritischen Problemen
   - Short-Term: Incident Runbook befolgen, Session-Logs sichern
   - Post-Incident: Post-Mortem innerhalb 48h, Corrective Actions definieren
   - Follow-Up: Corrective Actions umsetzen, Effectiveness verifizieren

3. **Policy Refinement**
   - Trigger: Lessons-Learned aus Incidents oder Near-Misses
   - Process: Policy-Change-Proposal, Governance-Review, Testing, Rollout
   - Documentation: Policy Refinement Log aktualisieren

4. **Knowledge Transfer**
   - Onboarding neuer Operatoren: Runbook-Walkthrough, Shadow-Sessions
   - Handoffs: Strukturierte Übergabe mit Status-Summary
   - Backup-Readiness: Regelmäßige Drills für Backup-Operatoren

#### Evidence Pack
- **Daily Recon Reports** (aggregiert)
- **Weekly Performance Reviews** (vs Baselines)
- **Incident Post-Mortems** (alle Severity-Levels)
- **Policy Refinement Log** (Change-History mit Rationales)
- **Operator Rotation Logs** (Handoffs, Backup-Activations)

#### Risk Notes
- **Complacency Risk:** Routine führt zu reduzierter Wachsamkeit (Mitigation: regelmäßige Drills, Rotation)
- **Knowledge Concentration Risk:** Single-Point-of-Knowledge bei Operator (Mitigation: Rotation Plan, Documentation)
- **Policy Ossification Risk:** Policies veralten, werden aber nicht aktualisiert (Mitigation: mandatory Post-Mortem Culture)
- **Scope Creep Risk:** Unbedachte Strategy-/Platform-Changes ohne Re-Gating (Mitigation: Change-Management-Discipline)

## 6. Verification Commands (Docs-only)
- `rg -n "CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2|CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR" docs/ops`
- `rg -n "\]\(docs/" docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md`  (check links)
- Repo Standard: run lint/doc gates as per existing CI, if available locally.

---

## 7. bg_job Execution Pattern (Standard)

### 7.1 Wann verwenden

Nutze bg_job für Multi-Agent Workflow Steps mit:
- **Langer Laufzeit** (> 5 Minuten): Backtests, Sweeps, VaR-Suites, Trainings
- **Timeout-Risiko**: normale Cursor/Shell-Sessions brechen bei langen Tasks ab
- **CI-ähnliche Robustheit**: saubere Exit-Code-Erfassung, PID-Tracking, Log-Capture
- **Nachverfolgung erforderlich**: Operator muss Status/Logs später prüfen können

### 7.2 Discovery-first Einstieg

**Starte immer mit:**
```bash
bash 'scripts'/'ops'/'bg_job.sh' --help || bash 'scripts'/'ops'/'bg_job.sh' help
```

Spekuliere nicht über Subcommands oder Flags. Nutze die Help-Ausgabe und die Referenzdokumentation.

**Referenz (vollständig):** `docs/ops/RUNBOOK_BACKGROUND_JOBS.md`

### 7.3 Operator-Notizen Standard

Jeder bg_job Run im Multi-Agent Workflow muss mindestens dokumentieren:

1. **Zweck / Step-ID**: Welcher Phase/WP-Step (z.B. "WP0B Risk Suite", "Phase 1 Backtest")
2. **Startzeit**: ISO-Format oder Operator-Timestamp
3. **Status/Logs Location**: Wo findet Operator die Outputs (ohne konkrete Subcommands zu erfinden; verweise auf Help + RUNBOOK_BACKGROUND_JOBS.md)
4. **Exit-Code erwartung**: Was bedeutet Success (typisch: `0`)

**Beispiel (Template für Session Runlog):**
```markdown
### bg_job Run — [Step-ID]

- **Zweck:** [kurze Beschreibung]
- **Start:** [YYYY-MM-DD HH:MM:SS]
- **Command:** [discovery-first: siehe Help]
- **Status/Logs:** [prüfe via Runner-Mechanik, siehe RUNBOOK_BACKGROUND_JOBS.md]
- **Exit-Code:** [erwartet: 0]
```

### 7.4 Troubleshooting-Minimum

**Bei Problemen:**

1. **Erst Help/Usage prüfen:**
   ```bash
   bash 'scripts'/'ops'/'bg_job.sh' --help
   ```

2. **Logs/Status via Runner-Mechanik nachschlagen:**
   - Keine Spekulation über interne Flags
   - Folge der Dokumentation in `docs/ops/RUNBOOK_BACKGROUND_JOBS.md`

3. **Exit-Code interpretieren:**
   - `0` = Success
   - Non-zero = siehe Logs und RUNBOOK_BACKGROUND_JOBS.md für Details

4. **Bei fortgesetzten Problemen:**
   - Operator-Review des vollständigen Logs
   - Check: Permissions, Disk Space, Timeout-Settings

### 7.5 Gate-Safety Reminder

**Docs Reference Targets Gate:**
- Schreibe Script-Pfad **niemals** als durchgehenden Pfad (roher Token)
- Verwende **immer** die Maskierung: `'scripts'&#47;'ops'&#47;'bg_job.sh'`
- Grund: verhindert docs-reference-targets-gate Konflikte

---

## Appendix B — Phase 4 Runner — Final Live Trade (Manual-Only, Governance-Lock)

### B.0 Phase-4 Pre-Flight (zusätzlich zu Appendix A / A.0)

**Kontext:**
Phase 4 ist die *Final-Live-Trade* Stufe. Diese Stufe ist **Manual-Only** und setzt einen **Governance-Lock** voraus. Ziel ist maximale Nachvollziehbarkeit, minimale Automatisierung, klare Kill-Switches und belastbare Operator-Readiness.

**Safety Non-Negotiables (Phase 4):**
- **Manual-Only:** Keine autonome Ausführung ohne explizite Operator-Aktion.
- **Governance-Lock:** Live-Freigabe ist ein *separater*, expliziter Go/No-Go Schritt. Dokumentation und Code-Änderungen sind nicht gleichbedeutend mit Freigabe.
- **No Secrets in Repo:** Keine Credentials, Tokens oder Schlüssel in Code/Docs/CI. Nur Platzhalter und Hinweise auf einen secure credential store.
- **Two-Person Rule (empfohlen):** Implementierung und Freigabe/Review getrennt.
- **Kill-Switches verpflichtend:** Sofortige Deaktivierung der Ausführung und klarer Incident-Pfad.
- **Default-Safe:** Standardzustand ist „blocked". Jede Freigabe muss reversibel sein.

**Operator Inputs (vor Start ausfüllen):**
- Change Window (Datum/Uhrzeit, Dauer):
- Operator(s) / Reviewer(s):
- Ziel-Umgebung: (Shadow / Paper / Live-Connectivity-Only / Live-Manual)
- Risikolimits (konkret, versioniert, dokumentiert):
- Kill-Switch Mechanismus (wo/wie ausgelöst):
- Monitoring / Alerting minimal set (welche Signale sind Pflicht):
- Incident Runbook Referenz (Plain-Text-Pfad):

---

### B.1 Phase 4 Runner — Final Live Trade (Manual-Only, Governance-Lock)

#### Ziel / Definition of Done (DoD)
**Ziel:** Ein Live-Setup, das *technisch* robust ist, *operativ* überwacht wird, und *governance-seitig* nur manuell und streng kontrolliert aktiviert werden kann.

**DoD (Phase 4):**
- Live-Connectivity ist verifiziert (authentifiziert, stabil, rate-limit safe), ohne Automatik-Handel zu aktivieren.
- Risk Runtime ist live-tauglich (Limits, Fail-closed Verhalten, saubere ReasonCodes).
- Observability/Telemetry ist ausreichend (Orders, Fills, Rejections, Latenzen, Fehler, Policy Entscheidungen).
- Kill-Switch ist getestet (Stop/Block/Disable Pfad).
- Operator Drill ist dokumentiert und einmal end-to-end durchgespielt.
- Go/No-Go Packet ist erstellt (Docs-only, sign-off ready).

#### Work Packages (Phase 4)
**WP4A — Live Readiness & Governance-Lock Packet (Docs-First)**
- Live-Readiness Checklist (Scope, Risiken, Verantwortlichkeiten)
- Go/No-Go Packet Template (Sign-off, Evidence-Links als Plain-Text-Pfade)
- Change Window Plan + Rollback Plan

**WP4B — Live Connector Hardening (Connectivity-Only first)**
- Stabilität, Retries, Timeouts, Rate Limits, Backoff
- Idempotency / Correlation IDs durchgehend
- Safe error handling (fail closed, keine „silent" Fall-Throughs)

**WP4C — Risk Runtime Live Limits (Fail-Closed)**
- Limits: Notional, Exposure, Max Orders, Throttle, Cooldowns
- Pre-Trade Gate: harte Blockade bei unklarem Zustand
- Deterministische Logs / Audit Events

**WP4D — Observability & Incident Readiness**
- Minimal Dash/CLI Views für Live-Signale
- Alerting Baseline (Fehler, Reject-Spikes, Latenz, Drift)
- Incident Runbook: Trigger → Triage → Mitigation → Postmortem

**WP4E — Operator Drill & Evidence Pack**
- Manual Order Lifecycle Drill (ohne Automatik)
- Kill-Switch Drill
- Evidence Pack: konsolidierte Nachweise als Plain-Text-Pfade

---

## Phase 4 — 6-Step Protocol (Runner Standard)

### Step 1 — Scope (Operator + Lead Agent)
**Output:** Scope Statement + Constraints
- Modus: Manual-Only
- Explizite Nicht-Ziele: keine autonomen Trades, kein Auto-Promotion, kein unattended execution
- Change Window definiert
- Risikoannahmen dokumentiert

**Cursor Multi-Agent Prompt (paste):**
```
You are the Phase 4 Lead Agent for Peak_Trade.
Objective: prepare Final Live Trade as Manual-Only with Governance-Lock.
Constraints:
- Do not introduce any automation that can execute trades without explicit operator action.
- Do not add secrets; use placeholders and reference secure credential store only.
Deliverables:
- WP4A–WP4E plan with clear acceptance criteria
- A Go/No-Go packet outline (docs-only)
- A verification checklist (tests, telemetry, kill-switch)
```

### Step 2 — WP Plan (Lead Agent + Policy Critic)
**Output:** Sequenz + ACs + Risk Notes (pro WP)
- WP4A zuerst (Docs-First)
- WP4B/C als technische Härtung (Connectivity-Only, Fail-Closed)
- WP4D Observability/Incident
- WP4E Drill/Evidence

**Policy Critic Prompt (paste):**
```
You are the governance/policy critic for Phase 4.
Check the WP plan for:
- accidental live-enablement pathways
- missing kill-switch coverage
- missing audit/telemetry evidence
- unsafe defaults (must be blocked by default)
Output:
- Blockers (must-fix)
- Recommendations (should-fix)
- Evidence requirements
```

### Step 3 — Implement (Implementer Agent)
**Output:** Small, reviewable commits per WP
Guidelines:
- Prefer minimal diffs
- Deterministic logging
- Fail-closed behavior
- No implicit toggles; any "unlock" must be explicit, separately governed, and reversible

**Implementer Prompt (paste):**
```
Implement Phase 4 changes in small commits aligned to WP4A–WP4E.
Non-negotiables:
- Manual-Only operation
- Governance-Lock maintained
- No secrets, no credentials, no tokens in repo
For each commit:
- include a short rationale
- list verification commands
- list rollback considerations
```

### Step 4 — Review (Reviewer + Policy Critic)
**Output:** Review Notes + Risk Review + Sign-off readiness
Review dimensions:
- Safety defaults (blocked)
- Idempotency/correlation integrity
- Risk gate semantics (fail-closed)
- Telemetry completeness
- Kill-switch reliability
- No policy-pattern regressions in docs

**Reviewer Prompt (paste):**
```
Review the Phase 4 implementation.
Checklist:
- Manual-only pathway is enforced end-to-end
- No unattended execution path exists
- Risk runtime fails closed on uncertainty
- Telemetry covers critical path (intent→order→event→ledger/audit)
- Kill-switch tested and documented
Output:
- Approve / Request Changes
- Risk notes
- Required evidence list
```

### Step 5 — Verification (Operator)
**Output:** Evidence Pack (logs, screenshots, command outputs) as plain paths
Recommended verification buckets:
- Unit/integration tests relevant to execution/risk/audit
- Smoke verification for connector stability (connectivity-only)
- Telemetry sanity checks
- Kill-switch drill results

**Operator Notes:**
- Store verification artifacts under repo-safe locations if applicable.
- Reference evidence in docs via Plain-Text-Pfade.

### Step 6 — Completion Report (Docs-Only)
**Output:** Phase 4 Completion Report (Docs-only) with:
- scope
- changes
- verification evidence paths
- risk assessment
- explicit statement: "Go/No-Go is separate decision; default remains blocked"

**Completion Report Template (paste):**
```
# Phase 4 Completion Report — Final Live Trade (Manual-Only, Governance-Lock)

## Scope
- Mode: Manual-Only
- Governance: Lock maintained; Go/No-Go is separate

## Changes
- WP4A:
- WP4B:
- WP4C:
- WP4D:
- WP4E:

## Verification
- Tests:
- Connectivity-only checks:
- Telemetry checks:
- Kill-switch drill:
Evidence (Plain-Text-Pfade):
- ...

## Risk Assessment
- Residual risks:
- Mitigations:
- Rollback plan:

## Sign-off Readiness
- Ready for governance Go/No-Go review: YES/NO
- Blocking items:

## Appendix A — Phase Runner Prompt Packs (Phase 0–3)

Zweck: Pro Phase ein **copy/paste** Startprompt für Cursor Multi-Agent.
Konzept: Jeder Prompt erzwingt denselben Ablauf: Scope → WP-Plan → Implement → Review → Verification → PR-Hygiene.

### A.0 Pre-Flight (gilt für alle Phasen)
Bevor du einen Phase-Runner startest:
1) Erstelle ein Session-Runlog aus der Vorlage:
   - `docs/ops/CURSOR_MULTI_AGENT_SESSION_RUNLOG_TEMPLATE.md`
2) Setze **Mode** im Runlog korrekt:
   - Docs-only oder Code+Docs
3) Non-Negotiables (Safety / Governance):
   - Keine Live-Aktivierung in Docs/Code-Beispielen.
   - Default bleibt: **blocked / shadow / simulated** (je nach Phase).
   - Keine Secrets / Credentials / Keys in Repo oder Doku.

---

### A.1 Phase 0 Runner — Foundation / Contracts / Docs-First (Docs-only)

**Wo einfügen:** Cursor Chat (Multi-Agent)
**Ziel:** Runbook/Contracts/Navigation robust machen; minimale Diffs; keine kaputten Links.

```text
ROLE: Cursor Multi-Agent Orchestrator — Phase 0 (Docs-only Foundation)

SCOPE (NON-NEGOTIABLE)
- Docs-only changes. No runtime code modifications.
- Maintain policy: docs-reference-targets-gate. Only link to files that exist.
- If a target might not exist: mention as plain text with (future) and escape slashes (docs\/...).

INPUTS (fill in)
- Roadmap reference (plain text): <name/path if it exists>
- Operator goal (1 sentence):
- Constraints (if any): minimal diff, no renames, etc.

STEP 1 — DISCOVERY (no edits)
- Identify current Phase-0 related docs in:
  - docs/ops/
  - docs/execution/
  - docs/governance/ (if relevant)
- Open key entry points:
  - docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md
  - docs/ops/README.md
  - docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md
- Confirm all referenced files exist before creating links.

STEP 2 — WP PLAN (max 3 WPs, each with AC + risk)
WP0.1 (Docs consolidation / clarity)
- Files:
- Acceptance Criteria:
- Risk:

WP0.2 (Navigation / Frontdoor updates)
- Files:
- Acceptance Criteria:
- Risk:

WP0.3 (Templates / operator workflow polish)
- Files:
- Acceptance Criteria:
- Risk:

STEP 3 — IMPLEMENT (minimal diffs)
- Edit only the files in the WP plan.
- Do not add new speculative links.
- Keep language concise and operational.

STEP 4 — REVIEW (policy-aware)
- Check: no broken links
- Check: no accidental "live enable" examples
- Check: section order and consistency with Frontdoor

STEP 5 — VERIFICATION (list commands, do not run unless asked)
- `rg -n "CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2|SESSION_RUNLOG_TEMPLATE" docs/ops`
- `rg -n "\]\(docs/" docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md`  (should be empty or strictly valid)
- `git diff --stat`

STEP 6 — COMPLETION REPORT (must output)
- Files changed (added/modified)
- Diffstat summary
- Any non-linked (future) refs intentionally left as text
- Suggested PR title + body outline (docs-only)
```

---

### A.2 Phase 1 Runner — Shadow Trading (Dry / OfflineRealtimeFeed)

**Wo einfügen:** Cursor Chat (Multi-Agent)
**Ziel:** End-to-end Shadow-Modus Pipeline ohne echte Trades; Recon/Audit-Handoff; Incident-Readiness.

```text
ROLE: Cursor Multi-Agent Orchestrator — Phase 1 (Shadow Trading)

SCOPE (NON-NEGOTIABLE SAFETY)
- No real-money live trading enablement.
- Shadow/dry/offline simulated execution only.
- No secrets, no credentials, no exchange keys in docs or code.
- Any config examples must keep "live" semantics disabled/blocked.

INPUTS (fill in)
- Shadow target: <what scenario to run or document>
- Data source: <offline feed / recorded session / simulator>
- Definition of "done": <evidence artifacts, runlog, recon summary>

STEP 1 — DISCOVERY (no edits)
- Locate Phase-1 relevant components:
  - execution pipeline entry points
  - recon/audit scripts or runbooks
  - existing shadow runbooks and prior merge logs (if any)
- Identify "operator visible" artifacts:
  - session runlog
  - recon/audit summary output location
  - evidence index references (if used in project)

STEP 2 — WP PLAN (max 4 WPs)
WP1.1 Shadow session protocol
- Files/code areas:
- AC: A full "how to run shadow session" with runlog steps and expected outputs
- Risk: accidental live semantics (must be blocked)

WP1.2 Recon/Audit handoff
- Files/code areas:
- AC: clear post-run recon/audit checks + interpretation
- Risk: fragile assumptions about file paths

WP1.3 Failure modes / incident mini-runbook
- Files:
- AC: known failure modes + operator actions
- Risk: over-prescriptive commands

WP1.4 (Optional) Minimal tooling improvements
- Only if clearly necessary and safe.
- AC: measurable operator value

STEP 3 — IMPLEMENT
- Prioritize operator-facing docs/runbooks + minimal safe code changes if required.
- Ensure "blocked/shadow" semantics remain default.
- Keep diffs tight and testable.

STEP 4 — REVIEW (safety-first)
- Scan for any "enable live" patterns in docs/examples.
- Ensure recon/audit steps are deterministic and do not depend on non-existent paths.

STEP 5 — VERIFICATION (list commands, do not run unless asked)
- `ruff check .` (only if repo standard; otherwise list project's standard lint)
- `python3 -m pytest -q` (or targeted suite if documented)
- `rg -n "live_mode|enable_live|armed" docs/` (ensure docs are safe and wording is blocked)
- `git diff --stat`

STEP 6 — COMPLETION REPORT
- What is now possible end-to-end in shadow mode
- Evidence artifacts produced (names/paths as plain text)
- Remaining gaps to Phase 2
- Suggested PR title/body + risk statement
```

---

### A.3 Phase 2 Runner — Paper / Simulated Live (Exchange sandbox falls vorhanden)

**Wo einfügen:** Cursor Chat (Multi-Agent)
**Ziel:** Realistische Ausführung ohne Kapitalrisiko; klare Mode-Semantik; Operator-Observability; Regression-Safety.

```text
ROLE: Cursor Multi-Agent Orchestrator — Phase 2 (Paper / Simulated Live)

SCOPE (NON-NEGOTIABLE SAFETY)
- No real-money live trading.
- Simulated/paper/sandbox only.
- Default remains blocked unless an explicit safe sandbox mode exists.
- No secrets/credentials in repo.

INPUTS (fill in)
- Simulation mode: paper | sandbox | replay | exchange-testnet (if exists)
- Order execution fidelity goals: <latency, slippage model, fill rules>
- Operator monitoring needs: <dashboards/logs>

STEP 1 — DISCOVERY
- Identify what "paper mode" means in this repo (docs + code).
- Find current execution modes and any gating constructs.
- Locate operator observability (logs/reports/dashboards).

STEP 2 — WP PLAN (max 4 WPs)
WP2.1 Mode semantics + guardrails
- AC: paper/sim mode definition + explicit guardrails that prevent live
- Risk: ambiguous config leading to unsafe assumptions

WP2.2 End-to-end runbook (paper)
- AC: pre-run checklist, run command(s), post-run recon/audit
- Risk: non-deterministic outputs

WP2.3 Observability / operator UX
- AC: clear "what to look at" + where to find outputs
- Risk: too many moving parts

WP2.4 Regression safety
- AC: tests or smoke checks covering paper path
- Risk: slow CI

STEP 3 — IMPLEMENT
- Prefer docs + small safe changes over large refactors.
- Keep mode selection explicit and safe-by-default.

STEP 4 — REVIEW
- Check docs for forbidden "live enable" examples.
- Check all referenced paths exist or are marked (future) as plain text.

STEP 5 — VERIFICATION (list commands)
- Smoke run (if documented): `python -m ...` or `bash scripts&#47;...` (only if known)
- `rg -n "paper|sandbox|simulated" docs/ src/`
- `git diff --stat`

STEP 6 — COMPLETION REPORT
- What an operator can do now in paper/sim mode
- What evidence is generated per session
- Clear delta to Phase 3 (bounded auto)
```

---

### A.4 Phase 3 Runner — Bounded Auto (Strictly Bounded, Manual Override)

**Wo einfügen:** Cursor Chat (Multi-Agent)
**Ziel:** Begrenzte Automatisierung mit strikten Limits, Hard-Stops, Operator-Override; Governance-Gates; Incident-Drill-Readiness.

```text
ROLE: Cursor Multi-Agent Orchestrator — Phase 3 (Bounded Auto)

SCOPE (NON-NEGOTIABLE SAFETY)
- Bounded automation only: strict limits, hard stops, operator override.
- No autonomous live trading without explicit governance gates.
- No secrets in repo; configs must remain safe-by-default.

INPUTS (fill in)
- Proposed boundaries: <max size, max loss/day, max exposure, max orders>
- Override mechanism: <manual stop / kill-switch / go-no-go gate>
- Audit requirements: <what must be logged and reviewed>

STEP 1 — DISCOVERY
- Locate existing risk/runtime controls and any governance go/no-go mechanisms.
- Identify where boundaries are configured and enforced.
- Find incident/stop procedures and operator controls.

STEP 2 — WP PLAN (max 5 WPs)
WP3.1 Boundary spec (single source of truth)
- AC: explicit boundary list + semantics + failure behavior
- Risk: "soft limits" that don't actually stop

WP3.2 Enforcement hooks
- AC: boundaries enforced before order placement
- Risk: bypass paths

WP3.3 Operator override / kill-switch
- AC: immediate stop path documented + tested/smoke checked
- Risk: unclear operational steps

WP3.4 Recon/audit per session
- AC: post-run evidence; findings classification
- Risk: noisy false positives

WP3.5 Runbook + drills
- AC: runbook for start/stop/incident drill
- Risk: documentation drift

STEP 3 — IMPLEMENT
- Make boundaries explicit, centrally defined, and hard-enforced.
- Keep operator controls first-class.
- Avoid broad refactors; favor small, verifiable increments.

STEP 4 — REVIEW (governance-aware)
- Ensure default behavior remains safe/blocked unless properly gated.
- Ensure all docs avoid "enable live" instructions.

STEP 5 — VERIFICATION (list commands)
- Targeted tests/smokes for boundary enforcement (repo standard)
- `rg -n "bounded|limit|max_|kill|go_no_go" src/ docs/`
- `git diff --stat`

STEP 6 — COMPLETION REPORT
- Boundaries implemented + where enforced
- Operator override path (exact steps)
- Evidence generated per session
- Residual risks + recommended next gating to Phase 4
```

---

## 8. Maintenance
Update triggers:
- Cursor workflow changes (roles/protocol)
- Roadmap version bumps
- CI policy changes affecting docs linking
- Phase-Struktur Änderungen (Entry/Exit Criteria, Deliverables)
- Operator Feedback aus Live-Sessions (Phase 5–7)

Owner: Ops / Operator Tooling

**Version History:**
- V2.0 (2026-01-01): Phase 5–7 detailliert ausgebaut (Intent, Deliverables, Entry/Exit Criteria, Operator How-To, Evidence Pack, Risk Notes)
- V1.0 (2025-12-30): Initial version mit Phase 0–5 (rudimentär)
