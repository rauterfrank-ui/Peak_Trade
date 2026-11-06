# RUNBOOK — AI Autonomy 4B M3 (Cursor Multi-Agent Chat) — Control Center Dashboard/Visual

Status: Draft v0.1  
Scope: AI-Autonomy 4B M3 Workstream + Control Center Dashboard/Visual  
Audience: Operator (Frank), Reviewer, CI-Guardian, Evidence Scribe  
Mode: Evidence-first, Deterministic, No-Live

---

## 0. Purpose & Guardrails

### 0.1 Purpose
Dieses Runbook standardisiert die Arbeit in Cursor Multi-Agent Chat für:
- (A) AI-Autonomy 4B M3 Weiterentwicklung (Orchestrierung/Gates/Policies)
- (B) AI-Autonomy Control Center Dashboard/Visual (Status-, Evidence-, CI- und Run-Übersicht)

Ziel: audit-stabiler, nachvollziehbarer Delivery-Flow mit reproduzierbaren Artefakten.

### 0.2 Non-Negotiables (Guardrails)
- NO-LIVE: keine Live-Trading-Aktivierung, keine Strategie-Switches, keine Order-Execution.
- Evidence-first: Jede Änderung muss Evidenz produzieren (Diffs, Validator-Output, Screenshots/Exports, CI-Links).
- Determinismus: Gleiche Inputs → gleiche Outputs (stabile IDs, Sortierung, Zeitstempel-Handling).
- SoD: Rollen trennen (Scope/CI/Evidence/Risk). Eine Person kann mehrere Rollen spielen, aber die Checks müssen getrennt erfolgen.
- Minimal risk default: bevorzugt docs/visualization-only, keine runtime-kritischen Pfade ohne Gate.

---

## 1. Inputs & Prerequisites

### 1.1 Inputs
- Repo: Peak_Trade (main oder feature branch)
- Referenzdokumente:
  - AI-Autonomy Runbooks (insb. 4B M2 Cursor Multi-Agent)
  - Evidence Pack Schema + Validator (falls vorhanden)
  - CI Gates Liste (Job-Namen + Bedeutung)
- Zielauswahl:
  - M3: Welche Capability/Checks sollen ergänzt werden?
  - Dashboard: Welche Views sind „must-have" für Operator?

### 1.2 Prerequisites (Operator)
- Cursor Projekt ist auf Peak_Trade Repo geöffnet.
- Lokale Toolchain: Python, ruff, tests, ggf. node/uv je nach Setup.
- Zugriff auf GitHub PR/CI (read).

---

## 2. Multi-Agent Role Model

### 2.1 Rollen
1) ORCHESTRATOR  
   - zerlegt Scope in Tickets, koordiniert Agenten, entscheidet Output-Reihenfolge.

2) FACTS_COLLECTOR  
   - liest Repo-Status: existierende Runbooks, Dashboard-Artefakte, Evidence Packs, Scripts, CI-Jobs.

3) SCOPE_KEEPER  
   - hält Scope klein, verhindert „Feature drift", definiert klare Acceptance Criteria.

4) CI_GUARDIAN  
   - mappt Änderungen auf Gates (Docs, Lint, Audit, Evidence Pack Validation etc.), stellt lokal reproduzierbare Checks bereit.

5) EVIDENCE_SCRIBE  
   - baut Evidence Pack / Evidence Index Einträge, sorgt für audit-fähige Nachweise.

6) RISK_OFFICER  
   - bewertet Risiko (docs-only vs code), definiert Rollback und Failure Modes.

### 2.2 Kommunikationsregeln
- Jede Rolle liefert in einem festen Format:
  - Findings → Implications → Recommended Next Actions → Evidence to capture
- Konflikte: ORCHESTRATOR entscheidet, RISK_OFFICER hat Veto bei unsafe scope.

---

## 3. Required Artifacts (Evidence Pack)

Minimum-Set für jede M3/Dashboard-Lieferung:
- Run Manifest (Was/Warum/Scope/Out-of-Scope)
- Diff Summary (Dateien + Risiko)
- Validator Report(s) (lokal + CI)
- Operator Notes (Repro steps, known limitations)
- Optional: Screenshots / Export (Dashboard HTML)

Ablage:
- bevorzugt unter `docs/ops/` (oder bestehendem Evidence-Verzeichnis)

---

## 4. Standardized Workflow (A–H)

### A) Pre-Flight (Operator)
**Ziel:** sicherstellen, dass wir im richtigen Repo sind, keine Terminal-Continuation, sauberer Git-Status.

Checklist:
- Falls Prompt zeigt `>` / `dquote>` / heredoc → Ctrl-C
- `pwd` + `git rev-parse --show-toplevel` + `git status -sb`
- Branch-Strategie: neuer Branch für M3/Dashboard

Evidence:
- Terminal-Output (Snippet in Operator Notes)

### B) Discovery (FACTS_COLLECTOR)
**Ziel:** Ist-Stand erfassen.
- Welche Runbooks existieren (4B M2, Templates)?
- Gibt es bereits Dashboard-Artefakte? (HTML, md, scripts)
- Welche CI Gates sind relevant / schlagen häufig an?
- Wo liegt Evidence Index? Wie werden neue Evidence IDs vergeben?

Output:
- „Discovery Memo" (bullets) + Pfade + relevante Dateien

Evidence:
- Links auf Dateien + ggf. Ausschnitt (keine langen Zitate)

### C) Scope Freeze (SCOPE_KEEPER + RISK_OFFICER)
**Ziel:** 1-2 Iterationen, klar messbare Acceptance Criteria.
Beispiele für Dashboard-AC:
- AC1: „Single-Page HTML" generierbar, zeigt:
  - letzte N Runs (oder letzte N Evidence Packs)
  - Gate-Status (lokal/CI verlinkbar)
  - Go/No-Go Summary
- AC2: deterministische Sortierung + stable rendering (keine zufälligen IDs)
- AC3: docs-reference-targets gate bleibt grün

Output:
- „Scope Contract" (In/Out, ACs, Risiken)

### D) Design (ORCHESTRATOR)
**Ziel:** Minimaler Architekturentwurf.
Dashboard-Optionen (priorisiert):
1) Static HTML Report (no runtime) — generiert aus JSON/MD Artefakten  
2) Markdown-Dashboard (docs-only) — verlinkt Evidence, CI, Runbooks  
3) Lightweight Local Web (nur dev) — nur wenn zwingend

Output:
- Design Notes + Dateipfade + Datenquellen

### E) Implementation (ORCHESTRATOR + ggf. FACTS_COLLECTOR)
**Ziel:** Änderungen durchführen.
- Neue Runbook-Datei / Dashboard-Doc / Script hinzufügen
- Links/Index aktualisieren (ops README, Evidence Index)

Evidence:
- Git diff (oder File list) + rationale

### F) Validation (CI_GUARDIAN)
**Ziel:** lokal reproduzierbare Checks + CI readiness.
Minimum:
- docs reference targets validation (falls vorhanden)
- lint/format (falls code berührt)
- audit (falls deps berührt)
- evidence pack validation (falls relevant)

Output:
- Validator Report (lokale Kommandos + Output)

### G) Evidence Finalize (EVIDENCE_SCRIBE)
**Ziel:** audit-stabile Dokumentation.
- Evidence Index Eintrag(e)
- Operator Notes „How to reproduce"
- Optional: Dashboard Screenshot / export hash

### H) Sign-Off (RISK_OFFICER + Operator)
**Ziel:** Merge-Ready oder klare Next Steps.
- Risiko: minimal/low/medium/high
- Rollback: „revert commit" oder „delete doc file"
- Offene Punkte: klar getrennt als Follow-Ups

---

## 5. Pass/Fail Criteria

PASS wenn:
- Scope Contract erfüllt (alle ACs)
- Keine Guardrail-Violation (NO-LIVE etc.)
- Relevante Gates lokal reproduzierbar grün (oder begründete Ausnahme)
- Evidence Pack vollständig (Minimum-Set)

FAIL wenn:
- Unklare Datenquellen (Dashboard zeigt nicht nachvollziehbare Werte)
- Nicht-deterministisches Rendering (unstable ordering/IDs)
- Gate breakage ohne Fix/Plan
- Scope drift / unreviewable diff

---

## 6. Troubleshooting (Cursor Multi-Agent)

### 6.1 Agent Drift
Symptom: Agent baut neue Features statt ACs.  
Fix: SCOPE_KEEPER erzwingt „AC-only" und schneidet Out-of-Scope raus.

### 6.2 Determinismus
Symptom: Zeitstempel / random IDs ändern Outputs.  
Fix: „Build time" als Input injizieren oder weglassen; sortierte Listen; stable hashing.

### 6.3 Docs Gates
Symptom: docs-reference-targets / link-debt gate failt.  
Fix: keine pseudo-links (branch names) in Listen; To-Do Pfade als Code block oder plain text ohne link semantics.

---

## 7. Operator Output Template (Copy/Paste)

### 7.1 Run Manifest
- Goal:
- Scope (In):
- Out-of-scope:
- Files touched:
- Risks:
- Repro steps:

### 7.2 Validator Report
- Command(s):
- Result:
- Notes:

### 7.3 Evidence Summary
- Evidence IDs:
- Links:
- Artifacts produced:

---

## 8. Cursor Multi-Agent Prompt Pack

### 8.1 ORCHESTRATOR Prompt
You are ORCHESTRATOR. Enforce guardrails (NO-LIVE, evidence-first, determinism, SoD).
Produce a 2-iteration plan with acceptance criteria and artifact list. Keep diffs minimal.

### 8.2 FACTS_COLLECTOR Prompt
You are FACTS_COLLECTOR. Inspect repo paths for existing AI autonomy runbooks, evidence packs, dashboards, and CI gate scripts.
Return exact file paths + short findings.

### 8.3 SCOPE_KEEPER Prompt
You are SCOPE_KEEPER. Freeze scope to 1-2 deliverables with measurable ACs. Reject additions.
Return a Scope Contract.

### 8.4 CI_GUARDIAN Prompt
You are CI_GUARDIAN. Map changes to CI gates and give a minimal local verification command set.
Return a Validator Report template.

### 8.5 EVIDENCE_SCRIBE Prompt
You are EVIDENCE_SCRIBE. Produce evidence artifacts plan and where to store them. Ensure audit readability.

### 8.6 RISK_OFFICER Prompt
You are RISK_OFFICER. Assess risk, failure modes, and rollback plan. Flag anything that violates guardrails.

---

## 9. Change Log
- v0.1: Initial runbook for 4B M3 + Control Center Dashboard/Visual in Cursor Multi-Agent Chat
