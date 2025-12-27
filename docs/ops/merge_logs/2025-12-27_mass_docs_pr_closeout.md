# Ops Closeout — Mass Docs PR Wave (Cascading Merges) — 2025-12-27

## Summary
- **10/10 Dokumentations-PRs** erfolgreich gemerged (Auto-Merge nach grünen Checks)
- **4–5 Update-Runden** wegen *cascading merges* in einem hochdynamischen Repo
- **git rerere** aktiviert & genutzt → wiederkehrende Konflikte automatisch re-applied
- CI & lokale Safety Gates haben zuverlässig abgesichert

## Merged PRs (final)
- PR #365: docs(ops): index remote stash archives
- PR #345: docs(ops): define merge-log amendment policy
- PR #244: docs(ops): add PR #243 merge log
- PR #135: docs(ops): add stability & resilience plan v1
- PR #366: docs(ops): repo cleanup inventory + plan
- PR #344: docs(ops): daily ship log 2025-12-25
- PR #306: docs(ops): merge log for PR #304
- PR #140: docs(stability): Wave A+B deployment runbook
- PR #141: docs(dev): canonical runner index
- PR #238: chore(ops): ops script template

## What made it work
### Cascading merges (Root Cause)
- Jeder Merge verschiebt `main` → offene PRs werden **BEHIND** → brauchen "Update branch" → laufen CI erneut.

### Battle-tested techniques
- **Auto-Merge**: zuverlässig, spart Operator-Zeit, reduziert Race Conditions.
- **git rerere**: unverzichtbar bei wiederholten Konflikten (speichert/rekonstruiert Lösungs-Hunks).
- **Konfliktstrategie**: *"merge both changes when safe; prefer newer truth when conflicting"*.
- **Robuste CI**: keine Falsch-Positiven → Vertrauen in Gate-Signale.

## Verification (post-merge)
```bash
git checkout main && git pull --ff-only
bash scripts/ops/ops_center.sh doctor        # 9/9 ✅
bash scripts/ops/verify_required_checks_drift.sh  # No drift ✅
uv run ruff check .                          # All passed ✅
uv run ruff format --check .                 # No changes needed ✅
```

## Operator Checklist (copy/paste)

### Per PR (während Merge-Wave)
```bash
PR_NUM=365  # anpassen

# 1) Update branch (wenn BEHIND)
gh pr view $PR_NUM --json mergeStateStatus -q .mergeStateStatus | grep -q BEHIND && \
  gh api repos/:owner/:repo/pulls/$PR_NUM/update-branch -X PUT

# 2) Auto-merge setzen (idempotent)
gh pr merge $PR_NUM --auto --squash --delete-branch || true

# 3) Checks watchen
gh pr checks $PR_NUM --watch
```

### Post-Merge Verification
```bash
git checkout main && git pull --ff-only
bash scripts/ops/ops_center.sh doctor
bash scripts/ops/verify_required_checks_drift.sh
uv run ruff check . && uv run ruff format --check .
uv run pytest tests/ops/ -q
```

## Failure Modes & Diagnosis

### "Auto-merge not enabled"
```bash
# Diagnose
gh pr view $PR_NUM --json autoMergeRequest

# Fix: PR muss approvable sein + Checks grün
gh pr review $PR_NUM --approve
gh pr merge $PR_NUM --auto --squash --delete-branch
```

### "Required checks drift detected"
```bash
# Diagnose
bash scripts/ops/verify_required_checks_drift.sh

# Fix: Drift-PR mergen oder .github/workflows/*.yml korrigieren
```

### "Merge conflict persists after rerere"
```bash
# Diagnose
git rerere status
git rerere diff

# Fix: rerere-Cache für File löschen, neu resolven
git rerere forget path/to/file.md
# Konflikt manuell lösen, dann:
git add path/to/file.md && git commit
```

## Follow-ups
- Link in Ops Hub: `docs/ops/README.md` → "Recent Closeouts"
- Playbook dauerhaft abgelegt: `docs/ops/CASCADING_MERGES_AND_RERERE_PLAYBOOK.md`
