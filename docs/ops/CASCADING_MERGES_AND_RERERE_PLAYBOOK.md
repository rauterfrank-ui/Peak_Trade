# Cascading Merges & git rerere — Operator Playbook

## When to Use This Playbook

### ✅ Use when:
- **≥5 PRs** in merge queue gleichzeitig
- **Fast-moving main**: >10 commits/day
- **Recurring conflicts**: Gleiche Files (z.B. TOCs, logs, indexes) in mehreren PRs
- **Cascading updates**: Jeder Merge macht andere PRs BEHIND

### ❌ Skip when:
- Einzelne PR, keine Cascade-Gefahr
- PRs ändern komplett verschiedene Bereiche (kein Konfliktrisiko)
- Code-intensive PRs (Logic-Konflikte brauchen manuelle Review, kein rerere)

### Decision Tree
```
Habe ich >5 PRs gleichzeitig?
  ├─ Nein → Standard Merge-Workflow
  └─ Ja → Konflikte zu erwarten?
      ├─ Nein (verschiedene Dirs) → Standard Workflow, Auto-Merge OK
      └─ Ja (gleiche Files) → ✅ DIESES PLAYBOOK
```

---

## Enable rerere (One-Time Setup)
```bash
git config --global rerere.enabled true
git config --global rerere.autoupdate true
```

## Workflow

### 1. Erste PR (etabliert rerere-Pattern)
```bash
PR_NUM=365

# Update branch (wird BEHIND nach vorherigem Merge)
gh api repos/:owner/:repo/pulls/$PR_NUM/update-branch -X PUT

# Lokal pullen & Konflikt auflösen
git checkout branch-name
git pull origin branch-name
# Konflikt-Marker erscheinen → manuell editieren
git add .
git commit -m "Resolve merge conflict"
git push

# rerere hat Resolution gespeichert ✅
# Auto-merge aktivieren
gh pr merge $PR_NUM --auto --squash --delete-branch
```

### 2. Folge-PRs (rerere auto-resolves)
```bash
PR_NUM=345

# Update branch → rerere wendet gespeicherte Lösung an
gh api repos/:owner/:repo/pulls/$PR_NUM/update-branch -X PUT

# Checks watchen (sollten grün werden)
gh pr checks $PR_NUM --watch

# Auto-merge wurde bereits gesetzt → merges automatisch
```

### 3. Neue Konfliktmuster
- Lösen → rerere lernt hinzu
- Nächste ähnliche Konflikte: automatisch resolved

## Commands (Quick Reference)

### Rerere-Status & Debugging
```bash
# Welche Konflikte hat rerere resolved?
git rerere status

# Zeige gespeicherte Lösungen
git rerere diff

# Rerere-Cache inspizieren
ls -la .git/rr-cache/

# Spezifisches File aus rerere-Cache entfernen
git rerere forget path/to/file.md

# Kompletten rerere-Cache löschen (Nuclear Option)
rm -rf .git/rr-cache
```

### PR Update & Auto-Merge (via gh CLI)
```bash
PR_NUM=365

# Branch updaten (API call)
gh api repos/:owner/:repo/pulls/$PR_NUM/update-branch -X PUT

# Oder: via gh pr checkout + git merge (lokaler Approach)
gh pr checkout $PR_NUM
git merge origin/main

# Auto-merge Status prüfen
gh pr view $PR_NUM --json autoMergeRequest

# Auto-merge setzen (idempotent)
gh pr merge $PR_NUM --auto --squash --delete-branch
```

## Best Practices

### 1. Erste Konfliktlösung ist kritisch
- **rerere ist nur so gut wie die erste Lösung**
- Bei erster Resolution: Extra sorgfältig reviewen
- Tests lokal laufen lassen: `python3 -m pytest -xvs`
- Commit-Message dokumentiert Resolution-Strategy

### 2. Immer verifizieren nach rerere auto-resolve
```bash
# Nach "Update branch" mit rerere:
git log -1 --stat          # Was wurde geändert?
git show HEAD              # Diff reviewen
gh pr checks $PR --watch   # CI gibt finales OK
```

### 3. CI als Safety Net
- Linters fangen Syntax-Errors (falsch geklammerte Markdown-Listen)
- Tests fangen Logic-Errors (broken imports, missing files)
- **Niemals Auto-Merge setzen bei roten Checks**

### 4. Rerere-Cache monitoren
```bash
# Periodisch prüfen: Wächst der Cache stark?
du -sh .git/rr-cache/
ls -l .git/rr-cache/ | wc -l

# Bei >50 Einträgen: Alte Patterns cleanen
git rerere gc  # entfernt alte, ungenutzte Lösungen
```

### 5. Team Communication
- **Announce Merge-Waves**: "Merging 10 PRs, main wird sich schnell bewegen"
- **Freeze non-essential commits**: Reduziert Update-Runden
- **Share rerere-Cache** (optional): `.git&#47;rr-cache&#47;` kann committet werden für Team-weite Patterns

## Konflikt-Strategie (Field-Tested)

### Docs/Merge-Logs (additive changes)
```bash
# Beide Seiten behalten, chronologisch sortieren
<<<<<<< HEAD
- PR #365: docs(ops): feature A
=======
- PR #366: docs(ops): feature B
>>>>>>> branch

# ✅ Resolution:
- PR #365: docs(ops): feature A
- PR #366: docs(ops): feature B
```

### Index-Dateien / TOCs (list merges)
- **Strategie**: Union merge (beide Einträge behalten)
- **Sortierung**: Alphabetisch oder nach Datum
- **Duplikate**: Prüfen & deduplizieren

### Config / Metadata (conflicting values)
```bash
# Neuere Version bevorzugen (commit timestamp prüfen)
git log -1 --format="%ai %s" HEAD
git log -1 --format="%ai %s" origin/main

# Wenn unklar: manuell reviewen
```

### Code / Scripts (logic conflicts)
- **Niemals blind auto-resolven**
- **Immer manuell reviewen**
- **Tests laufen lassen nach Resolution**

## Troubleshooting

### "Conflict resolution failed" (rerere applied wrong solution)
```bash
# Diagnose
git rerere status
git rerere diff  # zeigt was rerere gemacht hat

# Fix: rerere-Lösung für File verwerfen
git rerere forget path/to/conflicted/file.md

# Konflikt neu resolven
git checkout --conflict=merge path/to/conflicted/file.md
# Manuell editieren
git add path/to/conflicted/file.md
git commit -m "Resolve conflict correctly"

# rerere lernt neue Lösung ✅
```

### "Auto-merge not triggering" (Checks grün, aber kein Merge)
```bash
# Diagnose
gh pr view $PR_NUM --json statusCheckRollup,autoMergeRequest

# Häufige Ursachen:
# 1) Required checks drift → .github/workflows/*.yml geändert
bash scripts/ops/verify_required_checks_drift.sh

# 2) Auto-merge wurde nie gesetzt
gh pr merge $PR_NUM --auto --squash --delete-branch

# 3) PR nicht approved
gh pr review $PR_NUM --approve
```

### "Too many merge conflicts" (>5 Files betroffen)
```bash
# Diagnose
git diff --name-only HEAD origin/main | wc -l

# Fix: Batch verkleinern
# - Merge nur 2-3 PRs gleichzeitig
# - Oder: PRs ohne Overlap zuerst (verschiedene Verzeichnisse)
```

### "Cascading updates in a loop" (PRs update sich gegenseitig)
```bash
# Root Cause: Commits während Merge-Wave auf main

# Fix: Freeze main für Merge-Wave Duration
# - Kommunizieren: "Merging 10 docs PRs, bitte warten"
# - Alternativ: Update-Branch erst bei letzten 2-3 PRs
```

## Example: Merge-Log Conflicts (mit rerere)

### Erste PR (PR #365) — Manual Resolution
```bash
# Konflikt erscheint in docs/ops/merge_logs/2025-12-27.md
<<<<<<< HEAD
- PR #344: docs(ops): daily ship log 2025-12-25
=======
- PR #365: docs(ops): index remote stash archives
>>>>>>> docs/ops-index-stash

# Manuell lösen (beide behalten, sortiert)
- PR #344: docs(ops): daily ship log 2025-12-25
- PR #365: docs(ops): index remote stash archives

git add docs/ops/merge_logs/2025-12-27.md
git commit -m "Resolve merge conflict"

# ✅ rerere hat diese Lösung gespeichert
```

### Zweite PR (PR #345) — rerere Auto-Resolves
```bash
# Update branch → gleicher Konflikt in gleichem File
gh api repos/:owner/:repo/pulls/345/update-branch -X PUT

# rerere wendet automatisch an:
# - PR #344: docs(ops): daily ship log 2025-12-25
# - PR #345: docs(ops): define merge-log amendment policy
# - PR #365: docs(ops): index remote stash archives

# Kein manuelles Eingreifen nötig! ✅
# CI checks laufen → grün → Auto-merge triggert
```

### Pattern
- **Jede neue PR** fügt eine Zeile hinzu
- **rerere erkennt**: "Ah, liste sortiert einfügen"
- **Spart**: ~5 min manuelles Resolven pro PR × 8 PRs = **40 min**

## Failure Modes (Production-Proven)

### Mode 1: "Silent rerere misapplication"
**Symptom**: CI fails nach rerere auto-resolve
**Diagnosis**:
```bash
git log -1 --stat  # welche Files wurden geändert?
git show HEAD      # diff zeigt falsch gemergten Code
```
**Fix**: `git rerere forget <file>` + manuell neu resolven

**Prevention**: Immer `gh pr checks --watch` nach Update

---

### Mode 2: "Required checks drift during wave"
**Symptom**: Auto-merge triggert nicht trotz grüner Checks
**Diagnosis**:
```bash
bash scripts/ops/verify_required_checks_drift.sh
# Output: "Missing: test-job-xyz" oder "Extra: old-job-abc"
```
**Fix**:
- Wenn Workflow geändert wurde: Drift-PR zuerst mergen
- Wenn fehlerhaft: `.github&#47;workflows&#47;*.yml` korrigieren

**Prevention**: Freeze workflows während Merge-Wave

---

### Mode 3: "Queued runs blocking merge"
**Symptom**: Checks grün, aber Status "Waiting for pending runs"
**Diagnosis**:
```bash
gh pr checks $PR_NUM  # zeigt "Queued" status
gh run list --branch main --limit 5  # zeigt viele laufende Workflows
```
**Fix**: Warten oder low-priority runs canceln

**Prevention**: Merge-Wave außerhalb Peak-CI-Zeiten (nicht nach großen main pushes)

---

### Mode 4: "Conflict marker leaked to main"
**Symptom**: `<<<<<<<` oder `>>>>>>>` in gemergtem Code auf main
**Diagnosis**:
```bash
git grep -n "^<<<<<<< HEAD" main  # sollte leer sein
```
**Fix**:
```bash
git revert <bad-merge-commit>
# Oder: Hotfix-PR mit korrekter Lösung
```

**Prevention**:
- Pre-commit hook: `grep -q "^<<<<<<< HEAD" && exit 1`
- CI grep-Check für Conflict-Marker

---

## Integration mit CI
- **Auto-merge erst aktivieren nach grünen Checks**
- **Rerere-Fehler werden von Linters/Tests gefangen** (z.B. Syntax-Errors, broken imports)
- **Bei CI-Failure nach Update**: Branch neu updaten, manuell resolven, rerere-Cache für File löschen

## Metrics (2025-12-27 Closeout)
| Metric | Value | Notes |
|--------|-------|-------|
| **PRs merged** | 10/10 | 100% success rate |
| **Update rounds/PR** | ~4–5 | Cascading effect due to fast-moving main |
| **Conflict rate** | ~30% | Mostly in `docs/ops/merge_logs/` |
| **Rerere success** | ~90% | Auto-resolved recurring patterns |
| **Manual review** | 3 PRs | Complex conflicts needing operator judgment |
| **CI failures** | 0 | All post-rerere updates passed checks |
| **Total duration** | ~2h | Including monitoring & verification |

**Key Insight**: rerere saved ~60% of manual conflict resolution time

## References

### Internal
- **Closeout Log**: `docs/ops/merge_logs/2025-12-27_mass_docs_pr_closeout.md`
- **Merge Logs Archive**: `docs/ops/merge_logs/` (alle Closeouts)
- **Ops Center Doctor**: `scripts&#47;ops&#47;ops_center.sh doctor`
- **Drift Guard**: `scripts/ops/verify_required_checks_drift.sh`

### External
- **Git rerere Docs**: https://git-scm.com/docs/git-rerere
- **GitHub Auto-Merge**: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request
- **gh CLI PR Commands**: `gh pr --help`

### Related Playbooks
- **Merge-Log Workflow**: `docs/ops/MERGE_LOG_WORKFLOW.md`
- **Merge-Log Template**: `docs/ops/MERGE_LOG_TEMPLATE_COMPACT.md`
- **Ops Script Guide**: `docs/ops/OPS_SCRIPT_TEMPLATE_GUIDE.md`
