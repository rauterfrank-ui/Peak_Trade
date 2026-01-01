# Cursor Multi-Agent Runbook (Phasen) — V2

Status: Draft (Docs-only)
Last updated: 2026-01-01
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

### Phase 5 — Final Live Trade (Manual-Only initial)
**Ziel:** Live-Trade nur nach explizitem Operator-Go.
**Non-Negotiables:**
- Default: LIVE bleibt gesperrt (blocked) bis Operator explizit freigibt
- Jede Session: Pre-Trade Gate + Post-Trade Recon/Audit
**Outputs:**
- Live session runlog
- Evidence index / audit trail
- Clear rollback instructions

## 6. Verification Commands (Docs-only)
- `rg -n "CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2|CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR" docs/ops`
- `rg -n "\]\(docs/" docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md`  (check links)
- Repo Standard: run lint/doc gates as per existing CI, if available locally.

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
```

---

## 7. Maintenance
Update triggers:
- Cursor workflow changes (roles/protocol)
- Roadmap version bumps
- CI policy changes affecting docs linking
Owner: Ops
