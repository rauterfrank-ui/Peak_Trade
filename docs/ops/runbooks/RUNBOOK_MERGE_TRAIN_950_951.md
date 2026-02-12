# RUNBOOK — Merge Train: PR #950 → PR #951 (Guarded, Single-Shot)

## Purpose
Deterministisch, snapshot-only per Default. Merge wird **nur** ausgeführt, wenn `DO_MERGE=1` gesetzt ist.

## Scope / Safety
- Dieses Runbook betrifft nur PR-Orchestrierung (gh CLI).
- **Kein Merge** ohne explizites Enable (`DO_MERGE=1`).
- Single-shot Guardrails via `--match-head-commit` (exakte SHA).

## Preconditions (Operator)
- PR #950: required checks PASS, `mergeStateStatus=CLEAN`, `headRefOid` matches `EXPECT_950_SHA`
- PR #951: ist initial stacked auf #950 (base != main) — ok; merge erst nach #950 merge und Retarget auf `main`.

## Dry-Run (NO MERGE)

```bash
DO_MERGE=0 bash scripts/ops/merge_train_950_951.sh
```

## Merge Mode (explicit enable)

```bash
DO_MERGE=1 \
EXPECT_950_SHA="6a83edafac7103b6f52dbef38c0e9a992111408d" \
EXPECT_951_SHA="225d9de12c6e80badff98aa3ec8984ac7cce6e33" \
bash scripts/ops/merge_train_950_951.sh
```

## Incident Note: Stacked PRs + base branch deletion
Wenn PR #951 (oder andere PRs) als stacked PR auf dem Head-Branch von #950 basieren, kann `--delete-branch` beim Merge von #950 dazu führen, dass dependents automatisch geschlossen werden.

Mit `merge_train_950_951.sh` gilt daher:
- Default: **Base-Branch wird NICHT gelöscht**, wenn offene dependents existieren (`ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS=0`).
- Override (nur wenn du sicher bist, dass keine dependents mehr existieren oder du das Schließen bewusst in Kauf nimmst):

```bash
DO_MERGE=1 \
ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS=1 \
EXPECT_950_SHA="..." \
EXPECT_951_SHA="..." \
bash scripts/ops/merge_train_950_951.sh
```

## What the script does
- Snapshot PR #950 + #951 (state, base/head, mergeability) + `gh pr checks`
- Wenn `DO_MERGE=1`:
  - merge #950 (guarded)
  - guard: #950 muss `MERGED` sein
  - retarget #951 base → `main`
  - snapshot #951
  - merge #951 (guarded)
  - post-merge snapshots

## Notes
- Retarget von #951 auf `main` ist nur sinnvoll **nachdem** #950 gemerged wurde, damit der Diff sauber kollabiert.
