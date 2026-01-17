# Drill Backlog — AI Autonomy 4B M2

**Last Updated:** 2026-01-09  
**Owner:** Ops / AI Autonomy Team

---

## Overview

This backlog tracks **candidate drills** (D03+) for future execution. Each entry includes:
- **Problem Statement**
- **Operator Value**
- **Risk/Blast Radius**
- **Prereqs**
- **Messbare Success Criteria**
- **Estimated Time-to-Run**

---

## Prioritized Backlog

### **Priority 1: Selected for D03**

#### **D03A: CI Monitoring ohne "watch"-Timeouts — Deterministic Polling Drill** ✅ SELECTED

**Status:** SELECTED (2026-01-09, D02 Meta-Drill)  
**Estimated Execution:** Next Session (within 48h)

**Problem Statement:**  
`gh pr checks --watch` und ähnliche long-running Commands führen zu Timeouts (>5 min), blockieren Operator-Workflows und erzeugen non-deterministische Ergebnisse.

**Operator-Value:**  
Ermöglicht zuverlässige, wiederholbare CI-Status-Beobachtung ohne Manual-Retry-Loops. Spart 10–15 min pro PR-Monitoring-Session.

**Risk/Blast Radius:** LOW (docs-only)

**Prereqs:**
- `gh` CLI authenticated
- At least 1 open PR für Polling-Tests
- Runbooks: `RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md`

**Success Criteria:**
1. Polling-Methode dokumentiert (<60s PR-Status abrufbar)
2. Intervall ≤30s (rate-limit safe)
3. "3-Step CI Status Check" How-To (max. 12 Zeilen)
4. 3 erfolgreiche Polling-Runs (Evidence)
5. CI gates pass (docs-reference-targets + lint)
6. Runbook-Integration (bestehende Runbooks verlinkt)

**Time-to-Run:** <60 min

**Artifacts:**
- `docs/ops/drills/runs/DRILL_RUN_<DATE>_D03A_CI_POLLING.md`
- `docs/ops/runbooks/RUNBOOK_CI_STATUS_POLLING_HOWTO.md` (new) OR integrated section <!-- pt:ref-target-ignore -->

**References:**
- D02 Selection: `docs/ops/drills/D02_NEXT_DRILL_SELECTION_20260109.md`
- Scoring: Weighted Score 62/70 (highest)

---

### **Priority 2: High-Value Candidates**

#### **D03B: Docs Reference Targets Gate Triage Drill — Fast-Path Fix**

**Status:** BACKLOG  
**Estimated Execution:** Q1 2026 (after D03A)

**Problem Statement:**  
Docs Reference Targets Gate failures sind häufig (118 baseline debt), aber der schnellste Pfad von Failure → minimaler Fix → CI-Verifikation → Merge ist nicht standardisiert.

**Operator-Value:**  
Reduziert Triage-Zeit von "Gate failed, was nun?" auf <10 Minuten (Detection → Fix → Re-Check). Minimiert PR-Friction.

**Risk/Blast Radius:** LOW (docs-only)

**Prereqs:**
- `scripts/ops/verify_docs_reference_targets.sh`
- `docs/ops/DOCS_REFERENCE_TARGETS_DEBT_GUIDE.md`
- Simulierter Failure oder echtes PR mit Gate-Failure

**Success Criteria:**
1. Broken link identifiziert in <2 min
2. Fix angewendet in <5 min (inline-ignore oder target-korrektur)
3. Lokal verifiziert: `verify_docs_reference_targets.sh --changed` pass
4. CI re-run: Gate grün
5. Run-Doc: Schritt-für-Schritt nachvollziehbar

**Time-to-Run:** <60 min

**Artifacts:**
- `docs/ops/drills/runs/DRILL_RUN_<DATE>_D03B_DOCS_REF_TRIAGE.md`
- Optional: `docs/ops/DOCS_REFERENCE_TARGETS_QUICK_TRIAGE.md` (cheat-sheet) <!-- pt:ref-target-ignore -->

**References:**
- D02 Scoring: Weighted Score 54/70 (2nd place)

---

#### **D03C: Incident Micro-Drill — Timeout Handling (D07 aus Drill Pack)**

**Status:** BACKLOG  
**Estimated Execution:** Q1 2026

**Problem Statement:**  
D07 im Drill Pack definiert, aber noch nicht ausgeführt. Timeout-Handling ist wiederkehrendes Pain Point (siehe 4 Runbook-References).

**Operator-Value:**  
Validiert Operator-Kompetenz in Timeout-Triage (Detection → Action → Evidence → Resolution). Schließt D07-Gap im Drill-Coverage.

**Risk/Blast Radius:** LOW (docs-only, training-drill)

**Prereqs:**
- Simuliertes Timeout-Szenario (z.B. stuck CI check)
- `docs/ops/CURSOR_TIMEOUT_TRIAGE.md` (falls vorhanden)
- `gh` CLI für manual status checks

**Success Criteria:**
1. Timeout-Symptom erkannt (<2 min)
2. Immediate Action: Ctrl-C + manual status check ausgeführt
3. Triage: Failure Mode klassifiziert (4 Kategorien)
4. Operator Action bestimmt: RETRY / SKIP / ESCALATE / MANUAL
5. Evidence-Log erstellt: `incident_log_D03C.md`
6. Runbook-Coverage geprüft: Gap identified (YES/NO)

**Time-to-Run:** 60–75 min

**Artifacts:**
- `docs/ops/drills/runs/DRILL_RUN_<DATE>_D03C_INCIDENT_TIMEOUT.md`
- `docs/ops/incidents/incident_log_<DATE>_D03C.md`

**References:**
- D02 Scoring: Weighted Score 51/70
- Drill Pack: `docs/ops/drills/OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md` (D07 section)

---

### **Priority 3: Lower Priority / Longer Time-to-Run**

#### **D03D: Evidence Pack Completeness Audit Drill**

**Status:** BACKLOG  
**Estimated Execution:** Q2 2026 (lower priority, longer time-to-run)

**Problem Statement:**  
D01 produzierte ein Evidence Pack (8 Pointers: E01–E08). Gibt es ein standardisiertes Schema/Validator für Evidence Pack Vollständigkeit?

**Operator-Value:**  
Schafft reproduzierbaren "Evidence Pack Quality Gate": Operator weiß vor PR-Closeout, ob alle Artefakte audit-stabil sind.

**Risk/Blast Radius:** MEDIUM (docs-only, aber Scope-Creep-Risk: neue Schema-Definition)

**Prereqs:**
- D01 Evidence Pack als Baseline
- `docs/ops/EVIDENCE_SCHEMA.md` (falls vorhanden)
- JSON-Schema oder Checklist-Template

**Success Criteria:**
1. Evidence Pack Schema definiert (min. 5 Felder)
2. Validator-Checklist erstellt
3. D01 Evidence Pack gegen Schema geprüft: PASS/FAIL + Gap-Report
4. Template aktualisiert: `SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md` enthält Schema-Referenz
5. CI gates pass

**Time-to-Run:** >90 min (requires schema definition + iteration)

**Artifacts:**
- `docs/ops/drills/runs/DRILL_RUN_<DATE>_D03D_EVIDENCE_AUDIT.md`
- `docs/ops/EVIDENCE_PACK_SCHEMA_V1.md` (new) <!-- pt:ref-target-ignore -->
- `docs/ops/EVIDENCE_PACK_VALIDATOR_CHECKLIST.md` (new) <!-- pt:ref-target-ignore -->

**References:**
- D02 Scoring: Weighted Score 37/70 (lowest, due to long time-to-run + scope-creep risk)

---

## Backlog Maintenance

### How to Add New Candidates

1. **Discovery:** Identify pain points via runbook TODOs, CI failures, operator friction
2. **D02 Process:** Run D02 Meta-Drill to score and prioritize
3. **Document:** Add entry to this backlog with all required fields
4. **Review:** Quarterly review with Ops team (adjust priorities)

### How to Promote Candidate to D03

1. **D02 Selection:** Run D02 Meta-Drill scoring
2. **Update Status:** Change status from BACKLOG to SELECTED
3. **Set Execution Date:** Within 48h (or next session)
4. **Create Charter:** Full charter in D02 output doc

---

## Historical Context

**D02 Meta-Drill Run:**
- **Date:** 2026-01-09
- **Outcome:** D03A selected (CI Polling)
- **Scoring Method:** 6 criteria, weighted (Operator Value ×3, Risk Reduction ×3, Frequency ×2, Time-to-Run ×2, Determinism ×2, Dependency Load ×1)
- **Evidence:** 4 candidates scored (D03A: 62, D03B: 54, D03C: 51, D03D: 37)

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-09  
**Maintained By:** Peak_Trade Ops Team
