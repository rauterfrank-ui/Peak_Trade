# RUNBOOK — PR #736: CI Snapshot → Auto-Merge (wenn ready) → Post-Merge Verify (main) (Snapshot-only)

**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/736  
**Scope:** docs-only  
**Mode:** Snapshot-only (keine Watch-Loops, kein Polling)  
**Risk:** LOW  

---

## Purpose
Dieses Runbook gibt Operatoren einen **deterministischen, snapshot-only Ablauf** für PR #736:
- CI-Status **einmalig** prüfen (required checks + optional Signals wie Bugbot),
- **wenn merge-ready:** Auto-Merge (squash) + delete-branch aktivieren,
- nach Merge: **Post-Merge Verify** auf `main` (aligned + clean tree) als Snapshot.

## Guardrails
- **Snapshot-only:** Keine `--watch`, keine Polling-Schleifen.
- **KEEP EVERYTHING:** Keine Inhalte kürzen/löschen (insb. Legacy Archive Notes).
- **Token Policy:** Keine URLs in Inline-Code. Inline-Code-Tokens mit “/” nur unescaped, wenn real; sonst `&#47;` oder bash code fence.
- **Reference Targets:** Keine neuen Links auf nicht-existierende Targets.

---

## Phase 1 — Repo Pre-Flight (Snapshot)

```bash
# Continuation-Guard: falls Prompt-Continuation (> / dquote> / heredoc>) → Ctrl-C, dann weiter.
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb
```

---

## Phase 2 — CI Snapshot (PR #736)

```bash
# Continuation-Guard: falls Prompt-Continuation (> / dquote> / heredoc>) → Ctrl-C, dann weiter.
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb

# Required checks (snapshot)
gh pr checks 736 --required

# Optional/full checks (snapshot)
gh pr checks 736

# PR state snapshot
gh pr view 736 --json number,url,state,mergedAt,mergeable,mergeStateStatus,headRefName,baseRefName
```

**Decision (snapshot-only):**
- Wenn **required checks = all successful** und PR state ist OPEN → weiter zu Phase 3.
- Wenn required checks pending/failing → **STOP** (kein Watch). Nächster Schritt: später erneut Snapshot ausführen.

---

## Phase 3 — Auto-Merge aktivieren (wenn merge-ready)

```bash
# Continuation-Guard: falls Prompt-Continuation (> / dquote> / heredoc>) → Ctrl-C, dann weiter.
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb

# Auto-merge (squash) + delete-branch
gh pr merge 736 --auto --squash --delete-branch

# Snapshot: Auto-merge enabled?
gh pr view 736 --json number,state,mergedAt,autoMergeRequest,mergeable,mergeStateStatus
```

---

## Phase 4 — Post-Merge Verify (main) (Snapshot-only)

Nur ausführen, wenn `gh pr view 736` `state: MERGED` und ein `mergedAt` Timestamp zeigt.

```bash
# Continuation-Guard: falls Prompt-Continuation (> / dquote> / heredoc>) → Ctrl-C, dann weiter.
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb

git switch main
git fetch origin
git pull --ff-only origin main
git status -sb
git log -1 --oneline
```

**Expected Snapshot:**
- `## main...origin/main`
- Working tree clean
- HEAD enthält den squash-merge Commit für PR #736 (Commit-Message endet typischerweise mit `(#736)`).

---

## Evidence Block (Copy/Paste)

```text
PR #736 — CI Snapshot → Auto-Merge → Post-Merge Verify (Snapshot)
PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/736
CI Snapshot (required): <paste gh pr checks 736 --required summary>
CI Snapshot (all): <paste gh pr checks 736 summary incl. Bugbot if present>
Auto-Merge: <enabledAt or "not enabled">
Merge State: <OPEN/MERGED + mergedAt if present>
Post-Merge Verify:
- git status -sb: <paste>
- git log -1 --oneline: <paste>
Risk: LOW
```
