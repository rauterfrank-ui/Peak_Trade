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

## 7. Maintenance
Update triggers:
- Cursor workflow changes (roles/protocol)
- Roadmap version bumps
- CI policy changes affecting docs linking
Owner: Ops
