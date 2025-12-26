# CI Required Checks: Naming Contract (Matrix-Jobs)

**Status:** ✅ Production (seit 2025-12-26)  
**Problem gelöst:** PR #361 blockiert → Matrix-Jobs nicht erstellt → Auto-Merge funktioniert nicht  
**Lösung:** PR #362 (gemerged 2025-12-26T23:10:03Z)

---

## Problem (klassisch)

Branch Protection kann explizite Check-Namen verlangen, z.B.:
- `tests (3.9)`
- `tests (3.10)`
- `tests (3.11)`
- `strategy-smoke`

Wenn ein Matrix-Job per **job-level `if:`** komplett übersprungen wird (z.B. Docs-only PR),
dann werden die Matrix-Check-Runs **gar nicht erzeugt** → GitHub meldet:

> ❌ required check is missing (z.B. `tests (3.11)`)

**Konsequenz:**
- PR zeigt `mergeStateStatus: BLOCKED`
- Auto-Merge wartet ewig
- Auch wenn alle *ausgeführten* Checks erfolgreich sind!

### Symptome

```bash
$ gh pr view 361 --json mergeStateStatus,mergeable
{
  "mergeStateStatus": "BLOCKED",  # ❌ Blockiert!
  "mergeable": "MERGEABLE"        # ✅ Aber eigentlich mergeable
}

$ gh pr checks 361
tests           skipping    # ❌ Kein "tests (3.11)" Check!
strategy-smoke  skipping    # ❌ Kein "strategy-smoke" Check!
```

**Root Cause:**

```yaml
# ❌ FALSCH: Job-level if überspringt den gesamten Job
tests:
  if: |
    github.event_name != 'pull_request' ||
    needs.changes.outputs.code_changed == 'true'
  strategy:
    matrix:
      python-version: ['3.9', '3.10', '3.11']
```

Bei docs-only PRs:
- Job wird **komplett übersprungen**
- GitHub erstellt **keine** Check-Runs
- Branch Protection findet `tests (3.11)` nicht → **BLOCKED**

---

## Lösung (stabil)

**Matrix-Jobs müssen immer entstehen**, damit die Check-Runs reportet werden.
Für Docs-only PRs wird **nicht der Job**, sondern die **Steps** "no-op/skip" gemacht.

### Contract

#### 1. Tests-Matrix muss Check-Namen pro Python-Version reporten

```yaml
tests:
  name: tests (${{ matrix.python-version }})  # ✅ Expliziter Name!
  needs: changes
  runs-on: ubuntu-latest
  strategy:
    fail-fast: false
    matrix:
      python-version: ['3.9', '3.10', '3.11']

  # ✅ KEIN job-level if: → Job wird immer erstellt

  steps:
    - name: Docs-only PR — skip tests
      if: ${{ github.event_name == 'pull_request' && needs.changes.outputs.code_changed != 'true' }}
      run: echo "Docs-only PR detected - skipping tests for Python ${{ matrix.python-version }}"

    - name: Checkout
      if: ${{ github.event_name != 'pull_request' || needs.changes.outputs.code_changed == 'true' }}
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      if: ${{ github.event_name != 'pull_request' || needs.changes.outputs.code_changed == 'true' }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    # ... alle weiteren Steps mit dem gleichen if: guard
```

**Ergebnis:**
- Matrix-Jobs werden **immer** erstellt: `tests (3.9)`, `tests (3.10)`, `tests (3.11)`
- Bei docs-only PRs: Nur der erste Step läuft (echo), dann SUCCESS ✅
- Bei Code-Änderungen: Alle Steps laufen wie gewohnt

#### 2. Non-Matrix Jobs brauchen ebenfalls explizite Namen

```yaml
strategy-smoke:
  name: strategy-smoke  # ✅ Expliziter Name!
  needs: [changes, tests]
  runs-on: ubuntu-latest

  # ✅ KEIN job-level if: → Job wird immer erstellt

  steps:
    - name: Docs-only PR — skip strategy smoke tests
      if: ${{ github.event_name == 'pull_request' && needs.changes.outputs.code_changed != 'true' }}
      run: echo "Docs-only PR detected - skipping strategy smoke tests"

    - name: Checkout
      if: ${{ github.event_name != 'pull_request' || needs.changes.outputs.code_changed == 'true' }}
      uses: actions/checkout@v4

    # ... alle weiteren Steps mit if: guard
```

---

## Verifikation

### Branch Protection Settings

```bash
$ gh api repos/rauterfrank-ui/Peak_Trade/branches/main/protection/required_status_checks \
  --jq '.contexts'
[
  "CI Health Gate (weekly_core)",
  "Guard tracked files in reports directories",
  "audit",
  "tests (3.11)",          # ← Explizit erforderlich!
  "strategy-smoke",        # ← Explizit erforderlich!
  "Policy Critic Gate",
  "Lint Gate",
  "Docs Diff Guard Policy Gate",
  "docs-reference-targets-gate"
]
```

### Docs-only PR (z.B. PR #361 nach dem Fix)

```bash
$ gh pr checks 361
✓ tests (3.9)       in 3s     # ✅ Erstellt!
✓ tests (3.10)      in 3s     # ✅ Erstellt!
✓ tests (3.11)      in 4s     # ✅ Erstellt! (war vorher das Problem)
✓ strategy-smoke    in 4s     # ✅ Erstellt! (war vorher das Problem)
✓ audit             in 2m46s
✓ (alle anderen gates)
```

**mergeStateStatus:**

```bash
$ gh pr view 361 --json mergeStateStatus,mergeable
{
  "mergeStateStatus": "UNKNOWN",  # ✅ Oder "CLEAN" nach merge
  "mergeable": "MERGEABLE"         # ✅ Mergeable!
}
```

### Code-Change PR

```bash
$ gh pr checks <pr-with-code-changes>
✓ tests (3.9)       in 3m5s   # ✅ Full test suite
✓ tests (3.10)      in 3m1s   # ✅ Full test suite
✓ tests (3.11)      in 5m5s   # ✅ Full test suite
✓ strategy-smoke    in 1m5s   # ✅ Full smoke tests
```

---

## Checklist: Neuer Required Check

Wenn du einen neuen Check zu Branch Protection hinzufügst:

1. **Expliziter `name:`-Feld im Job definieren**
   ```yaml
   my-new-check:
     name: my-new-check  # ✅ Must match Branch Protection context!
   ```

2. **Kein job-level `if:` für required checks**
   - Job muss immer entstehen
   - Skip-Logik in Steps verschieben

3. **Matrix-Jobs: Template-Variable im Namen verwenden**
   ```yaml
   name: tests (${{ matrix.python-version }})
   ```

4. **Docs-only Skip-Marker als ersten Step**
   ```yaml
   steps:
     - name: Docs-only PR — skip <check-name>
       if: ${{ github.event_name == 'pull_request' && needs.changes.outputs.code_changed != 'true' }}
       run: echo "Docs-only PR detected - skipping <check-name>"
   ```

5. **Alle weiteren Steps mit if: guard versehen**
   ```yaml
   - name: Actual Work
     if: ${{ github.event_name != 'pull_request' || needs.changes.outputs.code_changed == 'true' }}
     run: ...
   ```

6. **Branch Protection aktualisieren**
   ```bash
   gh api -X PUT repos/OWNER/REPO/branches/main/protection/required_status_checks \
     -f contexts[]="my-new-check" \
     -F strict=true
   ```

7. **Testen mit docs-only PR**
   - Check wird erstellt? ✅
   - Check meldet SUCCESS? ✅
   - Auto-Merge funktioniert? ✅

---

## Implementation Referenz

**Datei:** `.github/workflows/ci.yml`  
**PR:** #362  
**Commit:** `a358b8c` (2025-12-26)  
**Merged:** `42a7d07` (2025-12-26T23:10:03Z)

**Diff:**
```diff
  tests:
+   name: tests (${{ matrix.python-version }})
    needs: changes
    runs-on: ubuntu-latest
-   if: |
-     github.event_name != 'pull_request' ||
-     needs.changes.outputs.code_changed == 'true'

    steps:
+     - name: Docs-only PR — skip tests
+       if: ${{ github.event_name == 'pull_request' && needs.changes.outputs.code_changed != 'true' }}
+       run: echo "Docs-only PR detected - skipping tests for Python ${{ matrix.python-version }}"
+  
      - name: Checkout
+       if: ${{ github.event_name != 'pull_request' || needs.changes.outputs.code_changed == 'true' }}
        uses: actions/checkout@v4
```

---

## Troubleshooting

### PR bleibt BLOCKED trotz erfolgreicher Checks

**Symptom:**
```bash
$ gh pr view <pr> --json mergeStateStatus
{"mergeStateStatus": "BLOCKED"}
```

**Diagnose:**
```bash
# 1. Welche Checks sind erforderlich?
gh api repos/OWNER/REPO/branches/main/protection/required_status_checks \
  --jq '.contexts'

# 2. Welche Checks wurden gemeldet?
gh pr checks <pr>

# 3. Vergleich: Fehlt ein erforderlicher Check?
```

**Lösung:**
- Fehlender Check ist wahrscheinlich ein Matrix-Job oder hat job-level `if:`
- Check-Name in `.github/workflows/*.yml` prüfen
- `name:`-Feld mit Branch Protection vergleichen (case-sensitive!)
- Job-level `if:` entfernen, zu step-level verschieben

### Matrix-Job-Namen stimmen nicht

**Problem:** Branch Protection erwartet `tests (3.11)`, aber Workflow meldet nur `tests`

**Lösung:**
```yaml
tests:
  name: tests (${{ matrix.python-version }})  # ← Matrix-Variable!
```

### Check wird "pending" für immer

**Problem:** Job wartet auf `needs:` dependency, die nie kommt

**Diagnose:**
```bash
gh pr checks <pr> --watch
# Schau, welcher Job "pending" bleibt und welche needs: er hat
```

**Lösung:**
- Dependency-Job hat wahrscheinlich job-level `if:` und wurde übersprungen
- Dependency muss auch immer laufen (oder `needs:` entfernen)

---

## Related Docs

- `.github/workflows/ci.yml` - Aktuelle Implementation
- `docs/ops/merge_logs/2025-12-26_pr-362_ci-matrix-required-checks-fix.md` - Merge-Log (wenn vorhanden)
- GitHub Docs: [About status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- GitHub Docs: [Required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#require-status-checks-before-merging)

---

## History

- **2025-12-26**: Initial implementation (PR #362)
  - Problem: PR #361 blocked by missing `tests (3.11)` and `strategy-smoke` checks
  - Root cause: Job-level `if:` skipped entire matrix jobs on docs-only PRs
  - Solution: Move skip logic to step-level, always create matrix jobs
  - Result: ✅ Auto-merge works, all required checks reported

---

## Operator Notes

**TL;DR für On-Call:**

Wenn ein PR mit Auto-Merge nicht merged, obwohl alle Checks grün sind:

```bash
# Quick check
gh pr view <pr> --json mergeStateStatus,reviewDecision,statusCheckRollup \
  --jq '{merge: .mergeStateStatus, review: .reviewDecision, checks: [.statusCheckRollup[].name]}'

# Vergleich mit required checks
gh api repos/OWNER/REPO/branches/main/protection/required_status_checks --jq '.contexts'

# Fehlt ein Check? → Lies dieses Doc! 📖
```

**Fix:** Job-level `if:` → step-level `if:` + expliziter `name:` im Job.
