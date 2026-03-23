# Workflow Officer v0 Rollout Runbook

**Scope:** MVP-Implementierung des Workflow Officers. Kein Scope-Creep.

---

## Phase 1: Design Freeze (aktuell)

- [x] `WORKFLOW_OFFICER_V0_PLAN.md` erstellt
- [x] `WORKFLOW_OFFICER_FAILURE_TAXONOMY_V0.md` erstellt
- [x] `WORKFLOW_OFFICER_REPORT_SCHEMA_V0.md` erstellt
- [x] `WORKFLOW_OFFICER_EXISTING_BUILDING_BLOCKS_MAP.md` erstellt
- [x] Rollout-Runbook erstellt
- [ ] Review durch Ops-Owner
- [ ] Merge nach main (nur docs)

**Keine Änderungen an:** `src/`, `scripts/`, `config/`

---

## Phase 2: Minimaler Python-Orchestrator-Wrapper

**Ziel:** Einziges neues Modul <!-- pt:ref-target-ignore --> `src&#47;ops&#47;workflow_officer.py` *(planned module; not implemented in v0 docs-only phase)* mit:

- CLI via `argparse` (--mode, --profile, --json)
- Keine eigenen Checks; nur Aufruf von bestehenden Modulen
- Output nach `out&#47;ops&#47;workflow_officer&#47;<ts>&#47;` gemäß Report-Schema

**Dateiplan:**
```
src&#47;ops&#47;workflow_officer.py   # Neues Modul
```

**Dependencies:** Keine neuen; nutzt `src.ops.doctor`, subprocess für Shell-Scripts.

**Testplan:**
- `python -m src.ops.workflow_officer --mode advise` → Exit 0, kein Output in out/
- `python -m src.ops.workflow_officer --mode audit --profile default --json` → JSON mit Doctor-Checks
- Keine Änderung an bestehenden Doctor-/Preflight-Tests

**Verify-Plan:**
- `./scripts&#47;ops&#47;ops_doctor.sh --json` weiterhin unverändert
- Keine Regression in CI (Doctor wird nicht durch Workflow Officer ersetzt)

---

## Phase 3: Adapterization für Profile

**Ziel:** Profile `docs_only_pr`, `ops_local_env`, `live_pilot_preflight` mit konkreten Check-Adaptern.

**Adapter-Konzept:** Jedes Profil = Liste von (check_id, invoke_fn). invoke_fn ruft bestehendes Script/Modul auf und liefert {status, message, evidence}.

**Dateiplan:**
```
src&#47;ops&#47;workflow_officer.py   # Erweiterung: Profile + Adapter
<!-- pt:ref-target-ignore -->
src&#47;ops&#47;workflow_officer_profiles.py   # Optional: Profil-Definitionen
```

**Keine neuen Scripts.** Nur Aufruf von:
- `scripts&#47;ops&#47;validate_docs_token_policy.py`
- `scripts&#47;ops&#47;docker_desktop_preflight_readonly.sh`
- `scripts/ops/run_live_pilot_preflight.sh` (oder Einzelchecks)
- etc.

**Testplan:**
- Jedes Profil einzeln durchlaufen
- JSON-Report validieren gegen Schema

**Verify-Plan:**
- Bestehende produktive Pfade unverändert
- Keine Paper-/Shadow-/Evidence-Runs beeinflusst

---

## Rollback

Falls Probleme:
- Workflow Officer nicht in CI integrieren; nur manuell nutzbar
- <!-- pt:ref-target-ignore --> `src&#47;ops&#47;workflow_officer.py` *(planned module; not implemented in v0 docs-only phase)* kann ohne Auswirkung auf Doctor/Preflight entfernt werden (keine Abhängigkeiten von außen)

---

## Safety Checklist (Agent 6)

- [ ] Kein Auto-Remediation
- [ ] Keine Änderung an Live-Gates
- [ ] Keine Evidence-Mutation
- [ ] Kein Paper-/Shadow-Run-Kontakt
- [ ] Doctor bleibt unverändert als primärer Ops-Inspector
