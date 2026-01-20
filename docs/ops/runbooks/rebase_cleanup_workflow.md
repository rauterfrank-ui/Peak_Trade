# Rebase + Conflict Triage + Cleanup (Worktrees/Branches)

## Zweck

Dieses Runbook beschreibt einen wiederverwendbaren, audit-stabilen Operator-Workflow für:

- **Rebase** eines Feature-Branch auf aktuellen `main` (mit Konflikt-Resolution)
- **Verification** (Tests, Linting, CI-Checks)
- **Merge** via GitHub CLI (nur bei grüner CI)
- **Cleanup** von Worktrees und Branches (safe-by-default, reachability-checked)
- **Restore-Demo** (Branch-Pointer rekonstruieren aus SHA)

**Wann benutzen:**
- Feature-Branch muss vor Merge auf aktuellen `main` rebased werden
- Worktrees/Branches nach erfolgreichem Merge aufräumen
- Demonstration, dass Branch = Pointer, Commits bleiben in main

**Wann NICHT benutzen:**
- Bei shared/collaborative Branches (rebase ändert History)
- Bei bereits gemergten PRs ohne lokale Cleanup-Notwendigkeit
- Wenn keine Force-Push-Rechte für Feature-Branch vorhanden

## Geltungsbereich

- Repository: `rauterfrank-ui&#47;Peak_Trade` (analog für andere Repos)
- Branches: Feature-Branches (eigene), `main` (protected)
- Tools: `git`, `gh` CLI, `ruff`, `pytest`

## Preconditions

### Repository-Status

```bash
# Working Tree muss clean sein
git status -sb

# Auf main, fetch/prune durchgeführt
git checkout main
git fetch origin --prune
git pull --ff-only
```

### Shell-Awareness

**⚠️ WICHTIG: Shell-Continuation und Heredoc**

Wenn dein Terminal-Prompt `>`, `dquote>`, oder `heredoc>` zeigt:
- **Sofort `Ctrl-C` drücken** (Shell-Continuation beenden)
- Dann erneut `Ctrl-C` falls notwendig
- Siehe: [Terminal Hang Diagnostics](../PAGER_HOOK_HANG_TRIAGE.md)

### Force-Push Policy

- **Nur bei Feature-Branches** (niemals `main`/`master`)
- **Immer `--force-with-lease`** statt `--force` (Safety-Check)
- **Nur NACH Rebase** und lokaler Verification

## Workflow-Schritte

### 1) Pre-Flight Check

**Zweck:** Sicherstellen, dass wir im richtigen Repo, auf clean state, und mit aktuellem `main` arbeiten.

```bash
# Working Directory anzeigen
pwd

# Repo-Root verifizieren
git rev-parse --show-toplevel

# Status-Check (muss clean sein)
git status -sb

# Main aktualisieren
git checkout main
git fetch origin --prune
git pull --ff-only
```

**Erwartetes Ergebnis:**
- Working Tree clean (keine untracked/modified files)
- `main` ist up-to-date mit `origin&#47;main`

### 2) Rebase (Interactive oder Normal)

**Zweck:** Feature-Branch auf aktuellen `main` rebased.

```bash
# Auf Feature-Branch wechseln
git checkout <feature-branch>

# Rebase (normal)
git rebase main

# Oder: Interactive Rebase (für squash/edit)
git rebase -i main
```

**Bei Konflikten:**

```bash
# 1) Konflikt-Marker in Dateien finden und resolven
#    Achtung: Unterscheide echte Konflikt-Marker von Beispiel-Code in Docs!
#    Echte Marker: <<<<<<< HEAD ... ======= ... >>>>>>> <commit-msg>
#    Beispiel-Marker in Docs: oft eingerückt, in Codeblöcken, oder escaped

# 2) Resolved files stagen
git add <resolved-file>

# 3) Rebase fortsetzen
git rebase --continue

# Falls zu komplex oder Fehler:
git rebase --abort
# → Dann: manuell merge statt rebase, oder Operator kontaktieren
```

**Häufige Troubleshooting-Fälle:**

- **Editor hängt:** `Ctrl-X` (nano) oder `:wq` (vim) oder `Ctrl-C` + `git rebase --abort`
- **Conflict Marker in Docs:** Vorsicht bei Dateien wie `runbooks&#47;*.md` – Docs können Beispiel-Marker enthalten. Prüfe Kontext!
- **Ambiguous argument '+':** Sonderzeichen in Branch-Namen (z.B. `feat&#47;fix+docs`) können Probleme machen. Nutze stattdessen `feat/fix-docs`.

### 3) Verification (Lokal)

**Zweck:** Sicherstellen, dass der rebasede Branch noch funktioniert.

```bash
# Format-Check (ruff)
ruff format --check .

# Lint-Check (ruff)
ruff check .

# Tests (relevant für betroffene Module)
pytest tests/ -q

# Optional: Spezifische Tests für betroffenen Bereich
# pytest tests/ops/ -v
```

**Erwartetes Ergebnis:**
- Keine Format-Violations
- Keine Lint-Errors
- Alle relevanten Tests grün

### 4) Force-Push (mit Lease)

**Zweck:** Rebased Branch nach remote pushen.

```bash
# Force-Push mit Safety-Check
git push origin <feature-branch> --force-with-lease

# Hinweis: --force-with-lease verhindert versehentliches Überschreiben
# fremder Commits (z.B. von Collaborators)
```

**Verification:**

```bash
# PR-Status prüfen
gh pr view <PR-NUMBER> --json mergeable,statusCheckRollup

# Warten bis CI grün (optional mit watch)
gh pr checks <PR-NUMBER> --watch
```

### 5) Merge (nur bei grüner CI)

**Zweck:** PR mergen, nur wenn alle Required Checks grün sind.

```bash
# Preflight: Checks anzeigen
gh pr checks <PR-NUMBER>

# Merge (squash + delete-branch)
gh pr merge <PR-NUMBER> --squash --delete-branch

# Alternative: via Web-UI falls gh CLI keine Permissions hat
# → GitHub PR-Seite öffnen, "Merge pull request" klicken
```

**Erwartetes Ergebnis:**
- PR ist gemerged
- Remote Branch ist gelöscht
- Commits sind in `main` enthalten

### 6) Cleanup (Worktrees/Branches)

**Zweck:** Lokale Worktrees und Branches aufräumen – **nur wenn Commits in main enthalten sind**.

#### 6.1) Reachability-Check (Golden Rule)

**⚠️ KRITISCH:** Niemals Branch löschen, bevor nicht geprüft wurde, dass dessen Commits in `main` sind.

```bash
# Für einzelnen SHA prüfen
git merge-base --is-ancestor <SHA> main && echo "✅ Reachable" || echo "❌ NOT in main"

# Für Branch-Tip prüfen
BRANCH="<feature-branch>"
SHA="$(git rev-parse $BRANCH)"
git merge-base --is-ancestor $SHA main && echo "✅ Safe to delete" || echo "❌ NOT safe"
```

#### 6.2) Worktrees entfernen

```bash
# Liste aller Worktrees anzeigen
git worktree list

# Einzelnen Worktree entfernen (safe: nur pointer, commits bleiben)
git worktree remove <path>

# Falls "worktree is locked":
git worktree unlock <path>
git worktree remove <path>

# Falls "stale worktree refs":
git worktree prune
```

#### 6.3) Branches löschen

```bash
# Remote Branch (normalerweise schon via --delete-branch beim Merge gelöscht)
git push origin --delete <branch-name>

# Lokaler Branch (nur NACH Reachability-Check!)
git branch -d <branch-name>

# Falls "-d" verweigert (not fully merged):
# NUR WENN REACHABILITY CONFIRMED:
git branch -D <branch-name>
```

**Safety-Check nach Cleanup:**

```bash
# Main aktualisieren
git checkout main
git pull --ff-only

# Verbleibende Branches anzeigen
git branch -vv

# Verbleibende Worktrees anzeigen
git worktree list
```

### 7) Restore-Demo (Branch aus SHA rekonstruieren)

**Zweck:** Zeigen, dass Branch = Pointer; Commits bleiben in `main`.

```bash
# SHA identifizieren (z.B. aus Merge-Log oder PR-Diff)
SHA="<commit-sha>"

# Branch-Pointer neu erstellen
git branch <restored-branch-name> $SHA

# Reachability nochmal prüfen (Proof)
git merge-base --is-ancestor $SHA main && echo "✅ SHA is in main"

# Optional: Branch wieder löschen (Demo abgeschlossen)
git branch -D <restored-branch-name>
```

**Anwendungsfall:**
- Nach Merge kann Branch-Pointer gelöscht werden → Commits bleiben in `main`
- Bei Bedarf: Branch-Pointer rekonstruieren via `git branch <name> <sha>`
- Proof: `is-ancestor` zeigt, dass SHA bereits in `main` ist

## Golden Rules

### 1. Branch = Pointer, Commit bleibt

- Branch-Pointer löschen ändert nichts an Commits (solange in `main` enthalten)
- Restore via `git branch <name> <sha>` jederzeit möglich
- Proof via `git merge-base --is-ancestor <sha> main`

### 2. Löschen nur nach Reachability-Check

- **Niemals** Branch löschen, bevor nicht `is-ancestor` confirmed
- Bei Unsicherheit: `git log --all --decorate --oneline --graph` prüfen

### 3. Worktrees zuerst, dann Branches

- Worktree-Pointer zuerst entfernen (`git worktree remove`)
- Dann lokalen Branch löschen (`git branch -d&#47;-D`)
- Dann remote Branch löschen (`git push origin --delete`, meist schon beim Merge)

### 4. Dokumentation (Merge-Log) immer mit Link

- Merge-Log erstellen: `docs&#47;ops&#47;PR_<NUM>_MERGE_LOG.md`
- Link in `docs/ops/README.md` hinzufügen (via Marker `MERGE_LOG_EXAMPLES`)
- Siehe: [MERGE_LOG_WORKFLOW.md](../MERGE_LOG_WORKFLOW.md)

## Troubleshooting

### Rebase hängt / Editor

**Symptom:** Nach `git rebase -i` öffnet sich Editor, aber Terminal reagiert nicht.

**Lösung:**
- Nano: `Ctrl-X` → `Y` → `Enter`
- Vim: `:wq` → `Enter`
- Falls Editor unbekannt: `Ctrl-C` → `git rebase --abort`

**Prevention:**
```bash
# Standard-Editor setzen (einmalig in ~/.gitconfig)
git config --global core.editor "nano"
```

### Conflict Marker vs. Example Docs

**Symptom:** In Runbook/Docs werden Conflict-Marker angezeigt, aber sind nur Beispiele.

**Unterscheidung:**
- **Echte Marker:** `<<<<<<< HEAD` am Anfang der Zeile, gefolgt von tatsächlichen Code-Diffs
- **Beispiel-Marker:** Oft eingerückt, in `` `bash` ``-Codeblöcken, oder escaped (`\<\<\<`)

**Lösung:**
- Nur echte Marker resolven
- Beispiel-Marker belassen

### Ambiguous argument '+' / Sonderzeichen

**Symptom:** `git` Befehle schlagen fehl mit "ambiguous argument '+'".

**Ursache:** Branch-Namen mit Sonderzeichen (`+`, `*`, `?`) können Git verwirren.

**Lösung:**
- Branch-Namen nur mit Alphanumeric + `-` + `/` + `_`
- Bei bestehendem Branch: rename via `git branch -m <old> <new>`

### Worktree is locked

**Symptom:** `git worktree remove` schlägt fehl mit "worktree is locked".

**Lösung:**
```bash
# Unlock
git worktree unlock <path>

# Dann remove
git worktree remove <path>
```

### Stale Worktree Refs

**Symptom:** `git worktree list` zeigt veraltete Einträge (Pfad existiert nicht mehr).

**Lösung:**
```bash
# Prune veraltete Worktree-Refs
git worktree prune
```

## Copy/Paste Snippets

### Preflight-Block (Beispiel)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Preflight Check ==="
pwd
git rev-parse --show-toplevel
git status -sb

echo "=== Update main ==="
git checkout main
git fetch origin --prune
git pull --ff-only

echo "✅ Preflight OK"
```

### Reachability Loop (Beispiel für mehrere SHAs)

```bash
#!/usr/bin/env bash
set -euo pipefail

# Liste von SHAs (Beispiel)
SHAS=(
  "abc123def456"
  "789fedcba012"
  "345678901abc"
)

echo "=== Checking Reachability in main ==="
for sha in "${SHAS[@]}"; do
  if git merge-base --is-ancestor "$sha" main 2>/dev/null; then
    echo "✅ $sha is in main"
  else
    echo "❌ $sha NOT in main (DO NOT DELETE BRANCH!)"
  fi
done
```

### Worktree Cleanup (Beispiel)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Worktree Cleanup ==="
git worktree list

# Beispiel: Einzelnen Worktree entfernen (anpassen!)
WORKTREE_PATH=".worktrees/feature-branch"

if [[ -d "$WORKTREE_PATH" ]]; then
  git worktree remove "$WORKTREE_PATH"
  echo "✅ Removed worktree: $WORKTREE_PATH"
else
  echo "ℹ️  Worktree not found: $WORKTREE_PATH"
fi

# Stale Refs aufräumen
git worktree prune
echo "✅ Pruned stale worktree refs"
```

## Abschluss-Checkliste ("Done")

Nach erfolgreichem Durchlauf:

- [ ] `main` ist clean und synced mit `origin&#47;main`
- [ ] Feature-Branch ist gemerged (PR closed)
- [ ] Alle Tests/Linting grün (lokal + CI)
- [ ] Merge-Log erstellt und in `docs/ops/README.md` verlinkt
- [ ] Remote Branch gelöscht (via `--delete-branch` beim Merge)
- [ ] Lokaler Branch gelöscht (nur nach Reachability-Check)
- [ ] Worktrees entfernt (falls vorhanden)
- [ ] Optional: `.ops_local&#47;` lokal aufgeräumt (temp files, logs)

**Empfehlung:** Nach größeren Cleanup-Sessions:

```bash
# Optional: Lokale Temp-Ordner aufräumen (falls vorhanden)
# VORSICHT: Nur löschen, wenn keine wichtigen WIP-Daten darin!
rm -rf .ops_local/

# Git GC (Garbage Collection, optional)
git gc --auto
```

## Verwandte Dokumentation

- [Merge-Log Workflow](../MERGE_LOG_WORKFLOW.md) — Standard-Prozess für Post-Merge Docs
- [Stash Hygiene Policy](../STASH_HYGIENE_POLICY.md) — Ähnlicher Safe-by-Default Ansatz für Stashes
- [Terminal Hang Diagnostics](../PAGER_HOOK_HANG_TRIAGE.md) — Troubleshooting für Shell-Hangs
- [Ops Operator Center](../OPS_OPERATOR_CENTER.md) — Zentrale Operator-Workflows

## Report Script

Für automatisierte Reports und Cleanup-Kandidaten siehe:

```bash
# Report-only (keine Löschungen)
scripts/ops/report_worktrees_and_cleanup_candidates.sh
```

Siehe unten für Details zum Report-Script.

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2026-01-03  
**Maintainer:** Peak_Trade Ops Team  
**Basis:** PR #528 (Rebase/Merge + Worktree/Branch Cleanup + Restore-Demo)
