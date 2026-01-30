# RUNBOOK: Docs-Only PR Lifecycle — Branch to Post-Merge (Cursor Multi-Agent)

**Version:** 1.0  
**Status:** ACTIVE  
**Risk Level:** LOW–MEDIUM  
**Audience:** Operators, Cursor Agent, Human-in-the-Loop  
**Scope:** Documentation-only PRs (no code changes)  
**Out-of-Scope:** Code changes, infrastructure changes, live system modifications

---

## Table of Contents

1. [Phase 0 — Preconditions & Scope](#phase-0--preconditions--scope)
2. [Phase 1 — Pre-Flight (Repo + Continuation-Guard)](#phase-1--pre-flight-repo--continuation-guard)
3. [Phase 2 — Branch erstellen](#phase-2--branch-erstellen)
4. [Phase 3 — Changes (Docs-only) + Self-Check](#phase-3--changes-docs-only--self-check)
5. [Phase 4 — Local Docs Gates Snapshot (ohne Watch)](#phase-4--local-docs-gates-snapshot-ohne-watch)
6. [Phase 5 — Commit (docs-only, additive)](#phase-5--commit-docs-only-additive)
7. [Phase 6 — Push + PR öffnen](#phase-6--push--pr-öffnen)
8. [Phase 7 — CI Snapshot (ohne Watch) + Merge](#phase-7--ci-snapshot-ohne-watch--merge)
9. [Phase 8 — Post-Merge Verify (main)](#phase-8--post-merge-verify-main)
10. [Phase 9 — Cleanup + Recovery Notes](#phase-9--cleanup--recovery-notes)

---

## Phase 0 — Preconditions & Scope

### Wann dieses Runbook gilt

Dieses Runbook gilt für **docs-only Pull Requests**, d.h. Änderungen, die ausschließlich Dokumentationsdateien betreffen.

### Was "docs-only" bedeutet

**Policy:**
- **ERLAUBT:** Änderungen an Dateien in docs/, README-Dateien, OPERATOR_*-Dateien, PHASE_*-Dateien, Markdown-Dateien
- **NICHT ERLAUBT:** Änderungen an Python-Code (src/, scripts/), Config-Dateien (config.toml, pyproject.toml), CI-Workflows (.github/), Tests (tests/)
- **ADDITIVE PREFERRED:** Neue Dateien anlegen ist sicherer als Bestehende zu modifizieren (siehe "KEEP EVERYTHING" Principle)

### Stop Conditions

**Breche dieses Runbook ab und eskaliere, wenn:**
- Dirty working tree vor Start (uncommitted changes auf main)
- Branch-Status unklar (detached HEAD, untracked state)
- Terminal in continuation mode hängt (siehe Phase 1 Preflight)
- Merge conflicts während Branch-Sync
- Required CI checks fehlen oder werden nicht ausgeführt

**Hinweis:** Bei Stop Condition NICHT automatisch weiter machen. Operator informieren, Status klären, dann entscheiden.

---

## Phase 1 — Pre-Flight (Repo + Continuation-Guard)

### Ziel

Stelle sicher, dass Terminal und Repo in einem bekannten, sauberen Zustand sind.

### Continuation-Guard

**WICHTIG:** Wenn dein Terminal-Prompt in einem der folgenden Modi hängt, musst du zuerst Ctrl-C drücken:

- `dquote>` (offene double-quote)
- `cmdsubst>` (offene command substitution)
- `heredoc>` (offenes heredoc)
- `>` (offene continuation)

**Symptom:** Du siehst keinen normalen Prompt, sondern einen continuation marker.

**Action:** Drücke Ctrl-C, dann verifiziere Prompt ist normal (z.B. `user@host:~$` oder `%`).

### Standard Preflight Commands

Führe diese Commands aus, um den Repo-Zustand zu verifizieren:

```bash
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
```

```bash
pwd
```

**Expected Output:**

```
/Users/frnkhrz/Peak_Trade
```

**Falls Output anders:** Stop. Navigiere manuell zum richtigen Verzeichnis oder kläre Workspace-Pfad.

```bash
git rev-parse --show-toplevel
```

**Expected Output:**

```
/Users/frnkhrz/Peak_Trade
```

**Falls Fehler:** Stop. Du bist nicht in einem Git-Repository.

```bash
git status -sb
```

**Expected Output (clean main):**

```
## main...origin/main
```

**Falls Output zeigt untracked/modified files:** Stop. Tree ist dirty. Entscheide: Commit? Stash? Discard?

**Falls auf anderem Branch:** Notiere Branch-Name. Entscheide: Switch zu main? Oder von aktuellem Branch arbeiten?

### Checklist Phase 1

- [ ] Terminal Prompt ist normal (kein continuation mode)
- [ ] pwd zeigt korrektes Repo-Verzeichnis
- [ ] git rev-parse funktioniert
- [ ] git status zeigt clean tree oder bekannte Änderungen
- [ ] Branch-Status ist klar (auf main oder bekannter Feature-Branch)

---

## Phase 2 — Branch erstellen

### Ziel

Erstelle einen neuen Feature-Branch für die docs-only Änderungen.

### Branch Naming Konvention

**Format:** Verwende einen aussagekräftigen Namen, der den Zweck klar macht.

**Beispiele:**
- docs-ops-runbook-pr-lifecycle
- docs-update-operator-checklist-phase8
- docs-add-salvage-pattern-guide

**Pattern:** Präfix `docs-` macht sofort klar, dass es sich um docs-only handelt.

### Commands

**Schritt 1:** Wechsle zu main und hole neueste Änderungen:

```bash
git switch main
```

```bash
git pull --ff-only
```

**Expected Output:**

```
Already up to date.
```

oder

```
Updating 1234abc..5678def
Fast-forward
 ...
```

**Falls Fehler (non-fast-forward):** Stop. Main hat diverged. Kläre Zustand mit `git log --oneline --graph -10`.

**Schritt 2:** Erstelle neuen Branch:

```bash
git switch -c docs-ops-runbook-pr-lifecycle
```

**Expected Output:**

```
Switched to a new branch 'docs-ops-runbook-pr-lifecycle'
```

**Verify:**

```bash
git status -sb
```

**Expected Output:**

```
## docs-ops-runbook-pr-lifecycle
```

### Checklist Phase 2

- [ ] git pull auf main war erfolgreich (fast-forward oder already up-to-date)
- [ ] Neuer Branch wurde erstellt
- [ ] git status zeigt neuen Branch-Namen
- [ ] Working tree ist clean

---

## Phase 3 — Changes (Docs-only) + Self-Check

### Ziel

Führe die dokumentarischen Änderungen durch und verifiziere, dass keine unbeabsichtigten Dateien verändert wurden.

### Operator Steps

**Schritt 1:** Erstelle oder modifiziere die Dokumentationsdateien gemäß Aufgabenstellung.

**Beispiel (neue Datei):**

```bash
touch docs/ops/runbooks/RUNBOOK_NEW_FEATURE.md
```

Öffne Datei in Editor, füge Inhalt hinzu, speichere.

**Beispiel (bestehende Datei ändern):**

Öffne Datei in Editor, nehme Änderungen vor, speichere.

**WICHTIG:** Wenn möglich, bevorzuge ADDITIVE Änderungen (neue Dateien) statt Modifikationen.

### Self-Check: No Accidental Edits

**Nach Änderungen ausführen:**

```bash
git status -sb
```

**Expected Output (neue Datei):**

```
## docs-ops-runbook-pr-lifecycle
?? docs/ops/runbooks/RUNBOOK_NEW_FEATURE.md
```

**Expected Output (geänderte Datei):**

```
## docs-ops-runbook-pr-lifecycle
 M docs/ops/runbooks/RUNBOOK_EXISTING.md
```

**Inspect Changes:**

```bash
git diff --stat
```

**Expected Output:**

```
 docs/ops/runbooks/RUNBOOK_NEW_FEATURE.md | 150 +++++++++++++++++++
 1 file changed, 150 insertions(+)
```

**STOP CONDITIONS:**
- Wenn `git diff --stat` zeigt Änderungen außerhalb von docs/, README, OPERATOR_, PHASE_ Dateien → **STOP**
- Wenn Python-Dateien (src/, scripts/), Config (config.toml, pyproject.toml), CI (.github/) geändert → **STOP**
- Dann: Revert unbeabsichtigte Änderungen mit `git checkout -- <file>` oder `git restore <file>`

### Optional: Format/Lint (falls repo-üblich)

Falls das Repo Format- oder Lint-Tools für Markdown hat, führe Snapshot aus (nur Snapshot, kein auto-fix ohne Review):

```bash
# Beispiel: markdownlint (falls vorhanden)
markdownlint docs/ops/runbooks/RUNBOOK_NEW_FEATURE.md
```

**Expected Output:**

```
(no output = pass)
```

oder

```
docs/ops/runbooks/RUNBOOK_NEW_FEATURE.md:10 MD013/line-length Line length
```

**Action bei Lint-Fehler:** Entscheide: Fix manuell? Ignorieren? (LOW risk bei docs-only, aber sauber ist besser)

### Checklist Phase 3

- [ ] Dokumentations-Änderungen sind vollständig
- [ ] git status zeigt nur erwartete Dateien (docs/, README, etc.)
- [ ] git diff --stat zeigt keine unbeabsichtigten Änderungen (kein src/, config/, .github/)
- [ ] Optional: Lint/Format check durchgeführt (falls repo-üblich)

---

## Phase 4 — Local Docs Gates Snapshot (ohne Watch)

### Ziel

Führe lokale Docs-Gates-Checks durch, um sicherzustellen, dass die Änderungen die Repo-Policy erfüllen. **Snapshot only** (kein Watch-Loop, keine Endlos-Wartezeit).

### Primary: Snapshot Script (falls vorhanden)

Falls das Repo ein zentrales Snapshot-Script hat:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Expected Output:**

```
[INFO] Running docs gates snapshot for changed files...
[PASS] Token-Policy Gate: 0 violations
[PASS] Reference-Targets Gate: 0 broken links
[PASS] Diff-Guard Gate: No unexpected changes
[INFO] All gates passed.
```

**Falls Script nicht existiert:** Weiter zu Fallback Einzelchecks.

### Fallback: Einzelchecks (Snapshots)

Falls kein zentrales Script vorhanden, führe die folgenden Checks einzeln aus:

#### Check 1: Reference-Targets Gate

Verifiziere, dass alle Markdown-Links auf existierende Ziele zeigen:

```bash
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

**Expected Output:**

```
Checking changed files for broken reference targets...
[PASS] All reference targets valid.
```

**Failure Output:**

```
[FAIL] docs/ops/runbooks/RUNBOOK_NEW_FEATURE.md:45
  Link target does not exist: docs/ops/non-existent-file.md
```

**Ursache:** Markdown-Link verweist auf nicht-existierende Datei.

**Fix Pattern:**
1. Öffne Datei, gehe zu Zeile 45
2. Optionen:
   - Korrigiere Pfad zum richtigen Ziel
   - Entferne Link, nutze plain text
   - Erstelle die fehlende Ziel-Datei (falls sinnvoll)
3. Re-run check

#### Check 2: Token-Policy Gate

Verifiziere, dass keine verbotenen Token-Patterns vorhanden sind (z.B. Inline-Backticks mit Slashes):

```bash
python3 scripts/ops/validate_docs_token_policy.py --changed
```

**Expected Output:**

```
Validating token policy for changed files...
[PASS] No violations detected.
```

**Failure Output:**

```
[FAIL] docs/ops/runbooks/RUNBOOK_NEW_FEATURE.md:67
  Inline backtick with slash detected: `docs/ops/file.md`
  Policy: Use plain text or fenced code blocks instead.
```

**Ursache:** Inline-Backtick mit Slash-Inhalt (triggert Policy-Gate).

**Fix Pattern:**
1. Öffne Datei, gehe zu Zeile 67
2. Optionen:
   - Ersetze Inline-Backtick mit plain text (ohne Backticks) oder nutze HTML entity: `path&#47;to&#47;file.md`
   - Oder nutze fenced code block, falls es ein Command/Path-Snippet ist

3. Re-run check

#### Check 3: Docs Diff-Guard (falls vorhanden)

Falls das Repo einen Diff-Guard für docs hat, der z.B. prüft, ob versehentlich große Blöcke entfernt wurden:

```bash
# Beispiel-Command (nur wenn Script existiert)
bash scripts/ops/verify_docs_diff_guard.sh --changed
```

**Expected Output:**

```
[PASS] No large deletions detected.
```

**Falls Script nicht existiert:** Überspringe diesen Check (nicht kritisch für additive Änderungen).

### Erwartete Signale + Typische Ursachen

| Signal | Bedeutung | Typische Ursache | Fix |
|--------|-----------|------------------|-----|
| PASS (all) | Alle Gates grün | Änderungen policy-konform | Weiter zu Phase 5 |
| FAIL Token-Policy | Inline-Backticks mit Slashes | Markdown-Syntax ungünstig | Plain text oder fenced block |
| FAIL Reference-Targets | Broken link | Tippfehler, Datei fehlt | Korrigiere Link oder erstelle Datei |
| FAIL Diff-Guard | Große Löschung | Versehentlich Inhalt entfernt | Prüfe Diff, restore falls nötig |

### Minimal-Invasive Fix-Patterns

**Pattern 1: Token-Policy Fix**
- Identifiziere Zeile mit Inline-Backtick + Slash
- Ersetze mit plain text ODER fenced code block
- Re-run check

**Pattern 2: Reference-Targets Fix**
- Identifiziere broken link
- Verifiziere, ob Ziel-Datei existieren sollte
- Falls ja: Erstelle Datei (minimal stub) oder korrigiere Pfad
- Falls nein: Entferne Link, nutze plain text
- Re-run check

**Pattern 3: Diff-Guard Fix**
- Inspect `git diff` für große Löschungen
- Verifiziere Intent: War Löschung beabsichtigt?
- Falls nein: `git restore` betroffene Datei, re-apply nur gewollte Änderungen
- Re-run check

### Checklist Phase 4

- [ ] Primary Snapshot Script ausgeführt (falls vorhanden) ODER Fallback Einzelchecks
- [ ] Token-Policy Gate: PASS (keine Inline-Backticks mit Slashes)
- [ ] Reference-Targets Gate: PASS (keine broken links)
- [ ] Optional Diff-Guard: PASS oder N/A (nicht vorhanden)
- [ ] Bei FAIL: Fix applied, Re-run, erneut PASS erreicht

---

## Phase 5 — Commit (docs-only, additive)

### Ziel

Committe die Änderungen mit aussagekräftiger Message und Body.

### Staging

**Stage alle docs-only Änderungen:**

```bash
git add docs/
```

Falls auch README oder OPERATOR/PHASE Dateien geändert:

```bash
git add README*.md OPERATOR_*.md PHASE_*.md
```

**Verify Staging:**

```bash
git status -sb
```

**Expected Output:**

```
## docs-ops-runbook-pr-lifecycle
A  docs/ops/runbooks/RUNBOOK_NEW_FEATURE.md
```

oder

```
## docs-ops-runbook-pr-lifecycle
M  docs/ops/runbooks/RUNBOOK_EXISTING.md
```

**STOP CONDITION:** Falls `git status` zeigt staged Dateien außerhalb von docs/, README, OPERATOR_, PHASE_ → **STOP**. Unstage mit `git restore --staged <file>`.

### Commit Message Template

**Format:**

```
docs: <Kurzbeschreibung (max 72 chars)>

<Body mit Details>
```

**Beispiel Commit Message:**

```
docs: Add Runbook for docs-only PR lifecycle

- New file: docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md
- Scope: Standardisiert docs-only PR flow von Branch bis Post-Merge
- Includes: Preflight, Gates Snapshot, CI Snapshot, Recovery Patterns
- Risk: LOW (docs-only, additive)
- Verification: Local docs gates snapshot passed (Token-Policy, Reference-Targets)
```

### Commit Command

```bash
git commit -m "docs: Add Runbook for docs-only PR lifecycle" -m "- New file: docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md
- Scope: Standardisiert docs-only PR flow von Branch bis Post-Merge
- Includes: Preflight, Gates Snapshot, CI Snapshot, Recovery Patterns
- Risk: LOW (docs-only, additive)
- Verification: Local docs gates snapshot passed (Token-Policy, Reference-Targets)"
```

**Expected Output:**

```
[docs-ops-runbook-pr-lifecycle 1234abc] docs: Add Runbook for docs-only PR lifecycle
 1 file changed, 150 insertions(+)
 create mode 100644 docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md
```

### Verify Commit

```bash
git log -1 --stat
```

**Expected Output:**

```
commit 1234abc...
Author: ...
Date: ...

    docs: Add Runbook for docs-only PR lifecycle

    - New file: docs/ops/runbooks/...
    - Scope: ...

 docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md | 150 ++++++++++
 1 file changed, 150 insertions(+)
```

### Checklist Phase 5

- [ ] git add für alle gewollten Änderungen (docs-only)
- [ ] git status zeigt nur docs/, README, OPERATOR_, PHASE_ Files als staged
- [ ] Commit Message ist aussagekräftig (Subject + Body)
- [ ] git commit erfolgreich
- [ ] git log -1 zeigt korrekten Commit

---

## Phase 6 — Push + PR öffnen

### Ziel

Pushe den Branch und erstelle einen Pull Request über GitHub CLI.

### Push Commands

**Push Branch zu origin:**

```bash
git push -u origin docs-ops-runbook-pr-lifecycle
```

**Expected Output:**

```
Enumerating objects: 5, done.
...
To https://github.com/USER/Peak_Trade.git
 * [new branch]      docs-ops-runbook-pr-lifecycle -> docs-ops-runbook-pr-lifecycle
Branch 'docs-ops-runbook-pr-lifecycle' set up to track remote branch 'docs-ops-runbook-pr-lifecycle' from 'origin'.
```

**Falls Fehler (permission denied, etc.):** Stop. Prüfe GitHub-Auth: `gh auth status`.

### PR Create via gh

**Titel Template:**

```
docs: Add Runbook for docs-only PR lifecycle (Cursor Multi-Agent)
```

**Body Template:**

```
## Summary

Adds comprehensive operator-friendly Runbook for docs-only PR lifecycle, from branch creation to post-merge verification.

## Changes

- **New File:** `docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md`

## Scope

- **Type:** Documentation-only (additive)
- **Risk:** LOW–MEDIUM
- **Audience:** Operators, Cursor Agent, Human-in-the-Loop

## Verification

- [x] Local docs gates snapshot passed (Token-Policy, Reference-Targets)
- [x] No code changes (src/, scripts/, config/, .github/)
- [x] Clean git diff (only docs/)

## Risk Assessment

- **Code Risk:** NONE (docs-only)
- **Operational Risk:** LOW (no live system impact)
- **Gate Risk:** LOW (passed local snapshot)

## Reviewers

@operator-team @docs-maintainers
```

**PR Create Command:**

```bash
gh pr create \
  --title "docs: Add Runbook for docs-only PR lifecycle (Cursor Multi-Agent)" \
  --body "## Summary

Adds comprehensive operator-friendly Runbook for docs-only PR lifecycle, from branch creation to post-merge verification.

## Changes

- **New File:** docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md

## Scope

- **Type:** Documentation-only (additive)
- **Risk:** LOW–MEDIUM
- **Audience:** Operators, Cursor Agent, Human-in-the-Loop

## Verification

- [x] Local docs gates snapshot passed (Token-Policy, Reference-Targets)
- [x] No code changes (src/, scripts/, config/, .github/)
- [x] Clean git diff (only docs/)

## Risk Assessment

- **Code Risk:** NONE (docs-only)
- **Operational Risk:** LOW (no live system impact)
- **Gate Risk:** LOW (passed local snapshot)

## Reviewers

@operator-team @docs-maintainers" \
  --base main
```

**Expected Output:**

```
Creating pull request for docs-ops-runbook-pr-lifecycle into main in USER/Peak_Trade

https://github.com/USER/Peak_Trade/pull/123
```

**Capture PR Number:**

```
PR_NUMBER=123
```

### Docs-Only Kennzeichnung

**WICHTIG:** Der PR Body sollte klar machen:
- **Type:** Documentation-only
- **Risk:** LOW–MEDIUM
- **No code changes** explizit erwähnt

Dies hilft Reviewern und CI, den PR korrekt zu kategorisieren.

### Checklist Phase 6

- [ ] git push erfolgreich (branch auf origin)
- [ ] gh pr create erfolgreich (PR URL erhalten)
- [ ] PR Nummer notiert (z.B. 123)
- [ ] PR Body enthält "docs-only" Kennzeichnung und Risk-Level

---

## Phase 7 — CI Snapshot (ohne Watch) + Merge

### Ziel

Überprüfe CI-Status über Snapshot-Commands (kein Watch-Loop), dann merge falls alle Checks grün.

### Checks Snapshot Commands

**View PR Metadata:**

```bash
gh pr view 123 --json number,state,mergeable,headRefName
```

**Expected Output:**

```json
{
  "number": 123,
  "state": "OPEN",
  "mergeable": "MERGEABLE",
  "headRefName": "docs-ops-runbook-pr-lifecycle"
}
```

**Falls mergeable: CONFLICTING:** Stop. Es gibt Merge-Konflikte. Siehe unten "Failure Modes".

**View PR Checks:**

```bash
gh pr checks 123
```

**Expected Output (alle checks grün):**

```
All checks passed
✓  CI / docs-gates       1m23s
✓  CI / lint-markdown    45s
✓  CI / reference-check  32s
```

**Falls Checks noch laufen:**

```
Some checks are still pending
○  CI / docs-gates       (pending)
○  CI / lint-markdown    (pending)
```

**Action:** Warte 1-2 Minuten, dann re-run `gh pr checks 123` (Snapshot, kein Watch).

**Falls Checks failed:**

```
Some checks failed
✗  CI / docs-gates       1m23s
✓  CI / lint-markdown    45s
```

**Action:** Siehe unten "Failure Modes".

### Merge Commands (falls alle Checks grün)

**Auto-Merge mit Squash:**

```bash
gh pr merge 123 --squash --auto --delete-branch
```

**Expected Output:**

```
✓ Enabled auto-merge on pull request #123
✓ Pull request #123 will be automatically merged via squash when all requirements are met
✓ Pull request #123 will delete branch docs-ops-runbook-pr-lifecycle when merged
```

**Hinweis:** `--auto` bedeutet, der PR wird gemerged, sobald alle required checks grün sind. Du musst nicht warten.

**Falls du lieber manuell mergen möchtest (nachdem Checks grün sind):**

```bash
gh pr merge 123 --squash --delete-branch
```

**Expected Output:**

```
✓ Merged pull request #123 (docs: Add Runbook for docs-only PR lifecycle)
✓ Deleted branch docs-ops-runbook-pr-lifecycle
```

### Failure Modes

| Failure | Ursache | Mitigation |
|---------|---------|------------|
| Required check missing | CI-Config nicht vollständig | Verifiziere .github/workflows/, eskaliere falls missing |
| Docs gates fail | Token-Policy oder Reference-Targets Violation | Review CI logs, fix lokal, force-push |
| Branch protection edge case | Main branch protection rule | Prüfe Settings, eskaliere an Admin falls nötig |
| Merge conflict | Main hat sich verändert seit Branch-Create | Siehe "Mitigation: Minimal Branch-Sync" unten |

### Mitigation: Re-Run Checks

Falls CI-Check failed, aber du vermutest Flaky-Test oder Infra-Issue:

```bash
gh pr checks 123 --watch
```

**ACHTUNG:** `--watch` ist ein Watch-Loop. Nutze nur, wenn du bereit bist zu warten. Andernfalls: Snapshot mit `gh pr checks 123`, warte 1-2 Min, repeat.

**Re-Run via Web:**
- Öffne PR in Browser: `gh pr view 123 --web`
- Klicke "Re-run failed jobs"

### Mitigation: Fix-Forward

Falls Docs-Gates failed (z.B. Token-Policy Violation im CI, aber nicht lokal gefangen):

1. Review CI logs:

```bash
gh pr view 123 --json statusCheckRollup
```

oder öffne PR in Browser: `gh pr view 123 --web`.

2. Identifiziere Ursache (Zeile, Datei).

3. Fixe lokal:

```bash
git switch docs-ops-runbook-pr-lifecycle
# Edit Datei, fix Violation
git add <file>
git commit -m "docs: Fix Token-Policy violation"
git push
```

4. CI wird automatisch neu laufen. Re-run Snapshot: `gh pr checks 123`.

### Mitigation: Minimal Branch-Sync

Falls PR hat Merge-Conflict, weil main sich geändert hat:

**Option 1: Rebase (sauber, aber riskanter):**

```bash
git switch docs-ops-runbook-pr-lifecycle
git fetch origin
git rebase origin/main
```

Falls Konflikte: Resolve manuell, dann:

```bash
git rebase --continue
git push --force-with-lease
```

**Option 2: Merge (einfacher, aber "merge commit"):**

```bash
git switch docs-ops-runbook-pr-lifecycle
git fetch origin
git merge origin/main
```

Resolve Konflikte, dann:

```bash
git add <resolved-files>
git commit
git push
```

**Empfehlung:** Option 2 (merge) ist sicherer für docs-only PRs (LOW risk).

### Checklist Phase 7

- [ ] gh pr view zeigt mergeable: MERGEABLE
- [ ] gh pr checks zeigt alle required checks grün
- [ ] gh pr merge ausgeführt (auto oder manuell)
- [ ] PR Status: MERGED (verifiziere mit `gh pr view 123`)

---

## Phase 8 — Post-Merge Verify (main)

### Ziel

Verifiziere, dass die Änderungen korrekt auf main gelandet sind.

### Commands

**Schritt 1: Switch zu main und pull:**

```bash
git switch main
```

```bash
git pull --ff-only
```

**Expected Output:**

```
Updating 1234abc..5678def
Fast-forward
 docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md | 150 ++++++++++
 1 file changed, 150 insertions(+)
```

**Falls Fehler (non-fast-forward):** Stop. Main hat diverged (sollte nicht passieren nach squash-merge). Prüfe `git log --oneline --graph -10`.

**Schritt 2: Verify Status:**

```bash
git status -sb
```

**Expected Output:**

```
## main...origin/main
```

(Clean tree, up-to-date)

**Schritt 3: Test — Datei existiert:**

```bash
ls docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md
```

**Expected Output:**

```
docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md
```

**Falls Datei nicht existiert:** FAIL. Merge hat nicht funktioniert. Eskaliere.

**Schritt 4: Inspect Content (optional):**

```bash
head -n 20 docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md
```

**Expected Output:** Erste 20 Zeilen der neuen Datei (Header, Title, etc.)

### Optional: Local Docs Gates Snapshot auf main

Falls du extra vorsichtig sein möchtest, führe die Docs-Gates erneut auf main aus:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

oder

```bash
bash scripts/ops/verify_docs_reference_targets.sh --changed
python3 scripts/ops/validate_docs_token_policy.py --changed
```

**Expected Output:**

```
[PASS] All gates passed.
```

**Hinweis:** Dies sollte green sein, da die Checks bereits vor Commit/Push/CI grün waren. Aber defensiv ist gut.

### Checklist Phase 8

- [ ] git switch main erfolgreich
- [ ] git pull --ff-only erfolgreich (fast-forward)
- [ ] git status zeigt clean tree
- [ ] ls zeigt neue/geänderte Datei existiert
- [ ] Optional: Docs gates snapshot auf main grün

---

## Phase 9 — Cleanup + Recovery Notes

### Ziel

Räume lokale Branches auf und dokumentiere Recovery-Patterns für Edge-Cases.

### Local Branch Cleanup

Nach erfolgreichem Merge und Verify ist der lokale Feature-Branch nicht mehr nötig.

**List Local Branches:**

```bash
git branch -v
```

**Expected Output:**

```
* main                         5678def [ahead 0, behind 0] docs: Add Runbook...
  docs-ops-runbook-pr-lifecycle 1234abc docs: Add Runbook...
```

**Delete Local Branch:**

```bash
git branch -d docs-ops-runbook-pr-lifecycle
```

**Expected Output:**

```
Deleted branch docs-ops-runbook-pr-lifecycle (was 1234abc).
```

**Falls Branch nicht deleted werden kann (unmerged warning):**

```bash
git branch -D docs-ops-runbook-pr-lifecycle
```

(Force-delete. Nutze nur, wenn du sicher bist, dass Commits in main sind.)

**Verify:**

```bash
git branch -v
```

**Expected Output:**

```
* main  5678def [ahead 0, behind 0] docs: Add Runbook...
```

(Feature-Branch ist weg.)

### Reflog Recovery Primer

Falls du versehentlich Commits verloren hast (z.B. force-push gone wrong, branch deleted vor merge), nutze `git reflog`:

**View Reflog:**

```bash
git reflog
```

**Expected Output:**

```
5678def (HEAD -> main, origin/main) HEAD@{0}: pull --ff-only: Fast-forward
1234abc HEAD@{1}: commit: docs: Add Runbook for docs-only PR lifecycle
...
```

**Recovery Pattern:**

Falls du Commit 1234abc verloren hast:

```bash
git cherry-pick 1234abc
```

oder

```bash
git reset --hard 1234abc
```

(Vorsicht: `reset --hard` überschreibt HEAD. Nutze nur wenn du weißt was du tust.)

**Hinweis:** Reflog hält Commits ca. 30-90 Tage (default Git config). Du hast also Zeit.

### Salvage Pattern (Squash/Branch Diverged)

Falls nach Squash-Merge dein lokaler Branch diverged ist (sollte nicht passieren mit `--delete-branch`, aber Edge-Case):

**Symptom:**

```bash
git status -sb
```

Output:

```
## docs-ops-runbook-pr-lifecycle...origin/docs-ops-runbook-pr-lifecycle [ahead 1, behind 3]
```

**Ursache:** Squash hat Commits neu geschrieben, Branch auf origin wurde deleted, aber lokal noch da.

**What to Check:**

1. Ist Branch auf origin noch da?

```bash
git fetch --prune
git branch -r | grep docs-ops-runbook-pr-lifecycle
```

Falls keine Ausgabe: Branch ist auf origin weg (gut).

2. Sind meine Commits in main?

```bash
git log --oneline main | grep "docs: Add Runbook"
```

Falls ja: Commits sind in main (gut).

**How to Reset Safely:**

```bash
git switch main
git branch -D docs-ops-runbook-pr-lifecycle
```

(Force-delete lokaler Branch, da Commits sicher in main sind.)

**Verify:**

```bash
git branch -v
```

Nur main sollte übrig sein.

### Recovery Scenarios — Summary

| Scenario | What to Check | How to Recover |
|----------|---------------|----------------|
| Lost commit (pre-push) | `git reflog` | `git cherry-pick <sha>` oder `git reset --hard <sha>` |
| Branch diverged post-merge | `git log main`, `git branch -r` | Verify commits in main, dann `git branch -D <branch>` |
| Accidental force-push | `git reflog`, `gh pr view <PR>` | Restore from reflog, re-push |
| Merge conflict unresolved | `git status`, `git diff` | Resolve manually, `git add`, `git commit` |

**General Principle:** Reflog ist dein Freund. Bei Unsicherheit: Stop, inspect reflog, dann entscheiden.

### Checklist Phase 9

- [ ] Lokaler Feature-Branch deleted (git branch -d oder -D)
- [ ] Reflog-Recovery-Pattern verstanden (optional read, falls nötig)
- [ ] Salvage-Pattern bekannt (falls squash/diverged Edge-Case)
- [ ] Repo-Zustand clean: Nur main Branch, up-to-date mit origin

---

## Appendix A: Quick Reference — All Commands in Order

```bash
# Phase 1: Preflight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb

# Phase 2: Branch
git switch main
git pull --ff-only
git switch -c docs-ops-runbook-pr-lifecycle
git status -sb

# Phase 3: Changes (manual edits)
# ... edit files ...
git status -sb
git diff --stat

# Phase 4: Local Docs Gates
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
# or fallback:
bash scripts/ops/verify_docs_reference_targets.sh --changed
python3 scripts/ops/validate_docs_token_policy.py --changed

# Phase 5: Commit
git add docs/
git status -sb
git commit -m "docs: Add Runbook for docs-only PR lifecycle" -m "<body>"
git log -1 --stat

# Phase 6: Push + PR
git push -u origin docs-ops-runbook-pr-lifecycle
gh pr create --title "..." --body "..." --base main
# Capture PR number (e.g. 123)

# Phase 7: CI Snapshot + Merge
gh pr view 123 --json number,state,mergeable,headRefName
gh pr checks 123
gh pr merge 123 --squash --auto --delete-branch

# Phase 8: Post-Merge Verify
git switch main
git pull --ff-only
git status -sb
ls docs/ops/runbooks/RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md

# Phase 9: Cleanup
git branch -v
git branch -d docs-ops-runbook-pr-lifecycle
git branch -v
```

---

## Appendix B: Expected Outputs Cheat Sheet

| Command | Expected Output Snippet | Failure Indicator |
|---------|------------------------|-------------------|
| `pwd` | `/Users/frnkhrz/Peak_Trade` | Different path |
| `git status -sb` (clean) | `## main...origin&#47;main` | Untracked/modified files |
| `git pull --ff-only` | `Already up to date` or `Fast-forward` | `fatal: Not possible to fast-forward` |
| `git switch -c <branch>` | `Switched to a new branch` | `fatal: A branch named ... already exists` |
| `git push -u origin <branch>` | `* [new branch] ... -> ...` | `error: failed to push` |
| `gh pr create` | `https://github.com/.../pull/123` | `error: ...` |
| `gh pr checks <PR>` | `All checks passed` | `Some checks failed` |
| `gh pr merge <PR>` | `✓ Merged pull request` | `error: ...` |
| `git pull --ff-only` (post-merge) | `Fast-forward` | `fatal: Not possible to fast-forward` |
| `git branch -d <branch>` | `Deleted branch` | `error: The branch ... is not fully merged` |

---

## Appendix C: Risk Matrix — Failure Impact

| Phase | Failure Type | Impact | Recovery Cost |
|-------|--------------|--------|---------------|
| Phase 1 (Preflight) | Dirty tree | LOW (caught early) | LOW (stash/commit) |
| Phase 2 (Branch) | Non-fast-forward pull | LOW (caught early) | LOW (rebase/reset) |
| Phase 3 (Changes) | Accidental code edit | MEDIUM (policy violation) | LOW (restore file) |
| Phase 4 (Local Gates) | Token-Policy violation | MEDIUM (would fail CI) | LOW (fix syntax) |
| Phase 4 (Local Gates) | Broken link | LOW (docs-only) | LOW (fix link) |
| Phase 5 (Commit) | Wrong files staged | MEDIUM (policy violation) | LOW (restore --staged) |
| Phase 6 (Push) | Push failed (auth) | LOW (no remote impact) | LOW (fix auth) |
| Phase 7 (CI) | Docs gates fail | MEDIUM (PR blocked) | MEDIUM (fix-forward) |
| Phase 7 (Merge) | Merge conflict | MEDIUM (manual resolve) | MEDIUM (sync branch) |
| Phase 8 (Verify) | File missing on main | HIGH (merge failed) | HIGH (investigate, salvage) |
| Phase 9 (Cleanup) | Branch force-deleted | LOW (commits in main) | ZERO (no-op) |

**Key Takeaway:** Failures in Phase 1-4 sind LOW cost (lokal, kein Remote-Impact). Failures in Phase 7-8 sind MEDIUM-HIGH cost (Remote, erfordert Investigation).

---

## Appendix D: Stop Conditions Summary

**STOP und eskaliere, wenn:**

1. **Phase 1:** Dirty tree, detached HEAD, terminal continuation mode hängt
2. **Phase 2:** Non-fast-forward pull (main diverged)
3. **Phase 3:** git diff zeigt Änderungen außerhalb docs/, README, OPERATOR_, PHASE_
4. **Phase 4:** Docs gates FAIL und fix nicht offensichtlich
5. **Phase 5:** Falsche Dateien staged (code statt docs)
6. **Phase 6:** Push failed (auth, permissions)
7. **Phase 7:** Required CI checks fehlen oder unbekannter Failure-Grund
8. **Phase 7:** Merge conflict und unsicher wie resolven
9. **Phase 8:** Datei missing on main nach Merge

**Bei Stop:** Informiere Operator, beschreibe Zustand (git status, git log), warte auf Entscheidung. **Nicht automatisch weiter machen.**

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-14 | Cursor Agent | Initial version (docs-only PR lifecycle, 9 phases) |

---

**END OF RUNBOOK**
