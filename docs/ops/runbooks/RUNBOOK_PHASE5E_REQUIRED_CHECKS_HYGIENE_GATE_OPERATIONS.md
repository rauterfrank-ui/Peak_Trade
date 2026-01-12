# RUNBOOK — Phase 5E — Required Checks Hygiene Gate: Operations

**Status:** ACTIVE  
**Scope:** Ops / CI Governance / Branch Protection Hygiene  
**Risk:** LOW (Docs) — Operational impact HIGH if misused  
**Primary Guards:** `dispatch-guard` (always-run) + `Required Checks Hygiene Gate`

## 0) Purpose & Non-Goals

### Purpose
Dieses Runbook standardisiert alle Operator-Aktionen rund um **Required Status Checks** (Branch Protection auf `main`) und stellt sicher, dass:
- keine "absent check" Szenarien entstehen (z.B. durch workflow-level `paths` Filter bei required checks),
- die **Repo-Quelle der Wahrheit** für erwartete Required Checks gepflegt bleibt:
  - `config/ci/required_status_checks.json`
- Änderungen an Branch Protection / Required Checks **auditierbar** (Evidence-first) und **rollback-ready** erfolgen.

### Non-Goals
- Kein automatisches Ändern von Branch Protection durch CI.
- Kein autonomes "self-healing" von required checks.
- Keine Änderungen am Gate selbst (Code/Workflows). Dieses Runbook beschreibt nur Betrieb.

## 1) System Overview (Current State)

### Required Checks (high-level)
- `dispatch-guard` ist required und läuft immer (always-run), um Workflow-Dispatch Policies durchzusetzen.
- `Required Checks Hygiene Gate` verhindert, dass required checks *fehlen* oder inkonsistent werden (z.B. wenn ein required check wegen Pfadfilter nicht erscheint).

### Source of Truth
- Erwartete Required-Check-Contexts: `config/ci/required_status_checks.json`
- Gate/Validator: `scripts/ci/validate_required_checks_hygiene.py`
- Test-Suite: `tests/ci/test_required_checks_hygiene.py`
- Workflow: `.github/workflows/required-checks-hygiene-gate.yml`

## 2) Operator Preconditions

### Required Access
- Repo Admin (für Branch Protection Änderungen)
- Fähigkeit PRs zu erstellen/mergen (normaler Contributor reicht für docs-only PR)

### Local Tooling (empfohlen)
- `gh` CLI (GitHub)
- `uv` (Python runner) — nur falls Operator lokal Tests reproduzieren will

## 3) Standard Workflow (A–G)

## A) Pre-Flight (No-Op Safety)
**Ziel:** Klarheit über Ausgangslage und Scope.

Checklist:
- [ ] Ist die Änderung wirklich notwendig (neuer required check, rename, entfernen)?
- [ ] Handelt es sich um eine *konfig-/policy-Änderung* oder nur Doku?
- [ ] Wird dadurch Branch Protection berührt? (Admin required)

## B) Discovery (Truth Capture)
**Ziel:** Beweise sammeln, was aktuell enforced ist.

Erhebung (als Operator-Kommandos; Ausführung optional):
- Required checks aus Branch Protection erfassen (GitHub UI Screenshot oder `gh api` Output).
- CI Job / Check Names verifizieren (exakte Context Strings).
- Relevante Dateien im Repo gegenprüfen:
  - `config/ci/required_status_checks.json`
  - `.github/workflows/required-checks-hygiene-gate.yml`

**Evidence Artifact (Minimum):**
- Datum/Uhrzeit
- Branch/PR Kontext
- Liste required contexts (Ist)
- Liste required contexts laut `config/ci/required_status_checks.json` (Soll)

## C) Change Plan (Design)
**Ziel:** Änderung so planen, dass kein absent-check entsteht.

Plan-Constraints:
- Required checks dürfen **nicht** auf workflow-level `paths` hängen.
- Wenn ein Check künftig required wird, muss er **immer** erscheinen:
  - Entweder always-run Workflow
  - oder gate-konformes Change-Detection, aber Workflow muss laufen

Plan Output:
- Change Summary (1–3 bullets)
- Impact (welche PR-Typen sind betroffen: docs-only, code-only, mixed)
- Rollback Strategy (Break-Glass)

## D) Execution (PR-based)
**Ziel:** Änderungen nur über PRs mit Audit Trail.

Wenn Code/Config betroffen wäre (nicht in diesem Runbook-PR):
- Update `config/ci/required_status_checks.json`
- Update/rename contexts konsistent
- Tests aktualisieren/ausführen
- PR eröffnen + Merge-Log + Evidence

Für reinen Ops-Runbook-Fall:
- docs-only PR, nur Doku

## E) Validation (CI + Policy)
**Ziel:** Sicherstellen, dass Hygiene Gate nicht nur "grün" ist, sondern *sinnvoll* grün.

Validation Checklist:
- [ ] `Required Checks Hygiene Gate` läuft auf PR und ist erfolgreich.
- [ ] docs-only PRs werden nicht durch missing required checks blockiert.
- [ ] `dispatch-guard` erscheint als required context auch bei docs-only PRs.

## F) Finalize (Evidence + Cross-links)
**Ziel:** Audit Trail schließen.

Artifacts:
- Merge Log (wenn relevant)
- Evidence Entry (wenn relevant)
- README Cross-link

## G) Sign-Off (Operator Checklist)
- [ ] Änderung dokumentiert (Was/Warum)
- [ ] Evidence vorhanden
- [ ] Rollback beschrieben
- [ ] Kein "absent check" Risiko verbleibt

## 4) Failure Modes & Triage

### Symptom: Merge blockiert, weil required check "Expected — Waiting for status to be reported"
Likely Causes:
- workflow-level `paths` filter verhindert Run
- rename des Checks ohne Update in Branch Protection
- fork/permissions verhindern Statusreport

Triage Steps:
1) Prüfe, ob Workflow überhaupt getriggert hat.
2) Prüfe, ob Check-Name/Context exakt mit Branch Protection übereinstimmt.
3) Prüfe, ob `config/ci/required_status_checks.json` und Branch Protection auseinanderlaufen.

### Symptom: Hygiene Gate schlägt fehl (Mismatch)
Likely Causes:
- Branch Protection required contexts wurden geändert, aber JSON nicht aktualisiert (oder umgekehrt).
- Check Names enthalten Whitespace/Case-Differenzen.
- Ein Gate wurde entfernt/umbenannt, aber nicht überall konsistent.

## 5) Break-Glass / Rollback (Admin Only)

**Prinzip:** Rollback ist erlaubt, aber nur als zeitlich begrenzte Stabilisierung, danach sofort Follow-up PR.

Break-Glass Optionen:
- Temporär: `Required Checks Hygiene Gate` als required check entfernen, um Merge zu entblocken.
- Danach: Root Cause fixen (Workflow always-run / Context Alignment) und Gate wieder aktivieren.

Rollback Evidence:
- Wer/Warum/Wann
- Screenshot/Export der Branch Protection Änderung
- Follow-up Issue/PR Referenz

## 6) Operator Templates

### A) PR Description Snippet (Required Checks Change)
- Change: <was geändert wurde>
- Why: <warum erforderlich>
- Risk: <merge-block / absent check Risiko>
- Validation: <wie geprüft>
- Rollback: <break-glass plan>
- References: <relevante Dateien>

### B) Evidence Entry Template (optional)
- Evidence-ID: EV-YYYYMMDD-<SHORTNAME>
- Scope: CI Governance / Required Checks
- Claim: <kurzer Claim>
- Proof:
  - Branch Protection snapshot (required contexts)
  - CI run links / run IDs (optional)
  - Repo config snapshot: `config/ci/required_status_checks.json` (hash / commit)
- Result: PASS/FAIL
- Notes: <operator notes>

## 7) References (Repo)
- `.github/workflows/required-checks-hygiene-gate.yml`
- `scripts/ci/validate_required_checks_hygiene.py`
- `tests/ci/test_required_checks_hygiene.py`
- `config/ci/required_status_checks.json`
- Phase 5C Closeout: `docs/ops/PHASE5C_WORKFLOW_DISPATCH_GUARD_ENFORCEMENT_CLOSEOUT.md`
