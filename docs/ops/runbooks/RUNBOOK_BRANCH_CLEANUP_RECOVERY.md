# RUNBOOK — Branch Cleanup Recovery (Tags + Bundles)

Date: [TBD]
Owner: [TBD]
Scope: Git hygiene / local branch cleanup safety-net
Risk: LOW (docs-only)

## Purpose

Dieses Runbook beschreibt, wie du **gelöschte lokale Branches** nach einem Cleanup wiederherstellst – über:
1) **Tags, pinned by SHA** (schnellste Recovery)
2) **Git Bundles** (für Worktree-Branches / portable Recovery)

Zusätzlich dokumentiert es die Cleanup-Taxonomie:
- `cleanup&#47;gone_pending&#47;drop&#47;*` — Branch wurde **gelöscht**, nachdem ein Safety-Tag erstellt wurde
- `cleanup&#47;gone_pending&#47;archive&#47;*` — Branch wurde **archiviert** (Tag) und dann lokal gelöscht
- `cleanup&#47;gone_pending&#47;keep&#47;*` — Branch bleibt lokal (Upstream wurde entfernt, um `: gone` Noise zu vermeiden)
- `cleanup&#47;gone_pending&#47;worktree&#47;*` — Worktree-Branch Snapshot: Tag + optional `.bundle`

## Preconditions

- Du bist im Repo-Root.
- `main` ist clean und up-to-date.

### Pre-flight

```bash
cd &#47;path&#47;to&#47;Peak_Trade
pwd
git rev-parse --show-toplevel
git status -sb
git fetch -p origin
git remote prune origin
```

## Inventory / Evidence

### List cleanup tags

```bash
git tag -l "cleanup&#47;*" | sort
```

### Find the cleanup logs

Beispiel-Pfade (lokal):

- `.local_tmp&#47;gone_branches_cherry_audit_*.txt`
- `.local_tmp&#47;gone_pending_cleanup_*.log`
- `.local_tmp&#47;worktree_pr__observability-compose-only_*.bundle`

## Recovery: restore a branch from a cleanup tag

### Tag naming convention

- Tag-Namespace: `cleanup&#47;...`
- Branch-Namen werden tag-sicher gemacht, indem `/` zu `__` wird.
  - Beispiel: `docs&#47;phase9c-broken-targets-wave5` → `docs__phase9c-broken-targets-wave5`

### Restore (recommended)

```bash
# Create & switch to a restored branch from a tag
git checkout -b <branch> cleanup&#47;gone_pending&#47;archive&#47;<branch__with__slashes>

# Alternative: create branch without switching
git branch <branch> cleanup&#47;gone_pending&#47;archive&#47;<branch__with__slashes>
```

## Recovery: worktree branch from bundle

Wenn ein Worktree-Branch zusätzlich als `.bundle` gesichert wurde, kannst du ihn unabhängig wiederherstellen.

### Verify bundle

```bash
git bundle verify .local_tmp&#47;worktree_pr__observability-compose-only_<STAMP>.bundle
```

### Restore the branch ref from bundle

```bash
# Fetch the branch ref from bundle into a local branch
git fetch .local_tmp&#47;worktree_pr__observability-compose-only_<STAMP>.bundle \
  "refs&#47;heads&#47;pr&#47;observability-compose-only:refs&#47;heads&#47;pr&#47;observability-compose-only"

# Then recreate a worktree (optional)
git worktree add &#47;path&#47;to&#47;Peak_Trade&#47;_worktrees&#47;compose_pr pr&#47;observability-compose-only
```

## Noise reduction: remove `: gone` without deleting a branch

Wenn ein Branch bewusst lokal behalten werden soll, aber der Remote-Upstream weg ist:

```bash
git branch --unset-upstream <branch>
git branch -vv | rg -n ": gone" || true
```

## Optional: make cleanup tags portable (push tags)

Hinweis: Tags sind standardmäßig **lokal**. Wenn du sie als Remote-Sicherungsanker brauchst:

```bash
# Push a single cleanup tag
git push origin "refs&#47;tags&#47;cleanup&#47;gone_pending&#47;keep&#47;<name>"

# Or push all cleanup tags (caution; review first)
git push origin --tags
```

## Risk

LOW — docs-only Runbook. Kein Einfluss auf `src&#47;**` Execution Paths.
