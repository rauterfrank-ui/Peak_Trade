# CI Trigger Runbook (PR checks starten nicht)

## Symptom
- PR zeigt "Expected — Waiting for status to be reported" / fehlende Checks
- Oder in UI sind nur sehr wenige Checks sichtbar ("Rollup symptom")

## Regeln
1) **Niemals** mehrfach hintereinander retriggern, wenn Jobs bereits `pending/in_progress` sind → dann nur warten.
2) Retrigger **nur**, wenn Checks offensichtlich fehlen / nicht gestartet sind.
3) Bei `failed` → Code fixen, normal commit+push (kein empty commit).

## Vorgehen

### A) Schnell prüfen (UI)
- PR → **Checks** Tab:
  - **Pending/In progress**: warten
  - **Missing/Expected**: einmal retriggern
  - **Failed**: fix + commit + push

### B) Retrigger (safe)
```bash
cd /Users/frnkhrz/Peak_Trade
git status -sb
./scripts/ops/ci_pr_checks_retrigger_v1.sh
```

Evidenz wird in `out/ops/ci_pr_retrigger_<branch>_<timestamp>/` geschrieben.

### C) GitHub-Maßnahmen (Branch Protection / Required Checks)

Falls Checks dauerhaft fehlen oder Branch Protection inkonsistent wirkt:

1. **Required Checks prüfen**
   ```bash
   gh api -H "Accept: application/vnd.github+json" \
     "/repos/rauterfrank-ui/Peak_Trade/branches/main/protection/required_status_checks" \
     | jq -r '.contexts[]' | nl -ba
   ```

2. **Dokumentation**
   - [docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md](../BRANCH_PROTECTION_REQUIRED_CHECKS.md)
   - [config/ci/required_status_checks.json](../../../config/ci/required_status_checks.json) (Pragmatic Flow: nur "PR Gate" als required)

3. **Drift Guard (falls vorhanden)**
   ```bash
   scripts/ops/verify_required_checks_drift.sh
   ```

---

## Referenzen
- [ci_pragmatic_flow_pr_body.md](../ci_pragmatic_flow_pr_body.md)
- [ci_pragmatic_flow_meta_gate.md](../ci_pragmatic_flow_meta_gate.md)
- [GATES_OVERVIEW.md](../GATES_OVERVIEW.md)
