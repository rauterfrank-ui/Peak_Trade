# RUNBOOK — Finish C5: Controlled Readiness (Live bleibt opt-in)

**Datum:** 2026-01-18  
**Status:** DRAFT  
**Modus:** governance‑safe, deterministisch, evidence‑first, **snapshot‑only**, **NO‑LIVE default**

> **Stop Rules (C5)**  
> - **Default NO‑LIVE** bleibt in Code/Config/Docs bestehen.  
> - Keine realen Broker‑Calls, keine Orders, keine Credentials.  
> - **Snapshot‑only**: keine Watch‑Loops.  
> - Scope‑Drift ⇒ STOP und ORCHESTRATOR re‑scoped.

---

## 0) Zweck

C5 ist eine **Readiness‑Phase ohne Enablement**: wir erzeugen Checklisten/Beweise/Incident‑Pack, die später (unter Operator‑Kontrolle) genutzt werden können, ohne Live freizuschalten.

---

## 1) Entry Point

### Voraussetzungen
- C4 operator dry-run pass.

---

## 2) Exit Point (DoD)

- Readiness Checklist dokumentiert + “Evidence Pack” Template:
  - explicit enable flag semantics
  - allowlist validated
  - audit log reviewed
  - mock E2E stable
  - failure scenarios pass
  - docs gates pass
- “Controlled Live Readiness” ist nur Dokumentation/Guardrails:
  - keine Live-Aktivierung im Code/Config als Default
  - klare Operator Stop/Abort Schritte

---

## 3) Readiness Checklist (High‑Signal, snapshot‑only)

> Diese Checklist ist **notwendig**, aber **nicht hinreichend** für Live. Live bleibt operator‑gated.

- **Governance**
  - [ ] Default NO‑LIVE in allen Konfigs/Entrypoints
  - [ ] explicit enable flag semantics dokumentiert; Default OFF
  - [ ] allowlist validated (syntaktisch + policy-konform; keine echten Broker Endpoints/Keys)
  - [ ] Secrets Policy: keine Keys in Repo/CI/Logs
- **Broker Adapter**
  - [ ] Idempotency getestet (dup place verhindert)
  - [ ] Retry bounded (max attempts; no storms)
- **Orchestrator**
  - [ ] Dry‑Run steps deterministisch
  - [ ] Audit Log reviewed (Events vollständig + redacted)
- **Reconciler/Safety**
  - [ ] Failure Matrix Tests grün
  - [ ] Tripwires aktivieren STOPPING/Operator intervention
- **Observability**
  - [ ] Health Snapshot vorhanden
  - [ ] Order lifecycle counters vorhanden
- **Docs/Evidence**
  - [ ] Evidence Template für „latest run“ ausgefüllt (siehe `TEMPLATES_FINISH_C_EVIDENCE.md`)
  - [ ] Incident Pack Template vorhanden (`TEMPLATES_FINISH_C_INCIDENT_PACK.md`)
  - [ ] docs gates pass (snapshot-only)

---

## 4) Snapshot Checklist (C5)

- [ ] `git status -sb`
- [ ] docs gates snapshot-only (changed scope)
- [ ] CI snapshot (gh) falls PR existiert (kein watch)
- [ ] Artefakte‑Liste final
- [ ] Next steps (optional, operator‑controlled) dokumentiert — ohne enablement

---

## 5) Deliverables

- `docs/ops/runbooks/finish_c/TEMPLATES_FINISH_C_EVIDENCE.md` (inkl. „latest run“ Beispiel-Fill)
- `docs/ops/runbooks/finish_c/TEMPLATES_FINISH_C_INCIDENT_PACK.md`

---

## 6) Snapshot Checks (no watch)

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
git status -sb
git diff --stat

# Docs gates snapshot (changed scope)
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main

# CI snapshot (falls PR existiert; kein watch)
# gh pr view <PR_NUMBER> --json number,title,headRefName,baseRefName,state,mergeable,reviewDecision,statusCheckRollup
# gh pr checks <PR_NUMBER>
```

---

## 7) Operator Stop / Abort (klar, ohne Live)

- Wenn ein Schritt Richtung „Live enable“ driftet ⇒ **STOP** (keine Ausnahme in C5).
- Wenn Output/Logs riskant wirken (PII/Secrets) ⇒ **STOP**, redaction plan, nur dann weiter.
- Wenn Tests/Docs‑Gates failen ⇒ **STOP**, fix-forward in eigenem PR‑Slice.

---

## 8) Artifacts

- Readiness checklist + Evidence templates + final docs (docs‑only)

---

## 9) References

- `../../EVIDENCE_ENTRY_TEMPLATE.md` (evidence conventions)
- `../general.md` (incident response baseline)
- `../execution_error.md` (execution error incident response)
