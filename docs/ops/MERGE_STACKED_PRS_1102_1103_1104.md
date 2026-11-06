# Merge stacked PRs #1102 → #1103 → #1104

## 0) Status prüfen

```bash
cd /Users/frnkhrz/Peak_Trade
git fetch origin --prune

gh pr view 1102 --json number,title,headRefName,baseRefName,mergeable,state,statusCheckRollup
gh pr view 1103 --json number,title,headRefName,baseRefName,mergeable,state,statusCheckRollup
gh pr view 1104 --json number,title,headRefName,baseRefName,mergeable,state,statusCheckRollup
```

## 1) CI bis grün beobachten (pro PR)

```bash
gh pr checks 1102 --watch
gh pr checks 1103 --watch
gh pr checks 1104 --watch
```

## 2) PR-04 mergen

```bash
gh pr merge 1102 --merge --delete-branch
```

## 3) PR-05 auf aktualisiertes main rebasen (nach Merge von 1102)

```bash
gh pr checkout 1103
git fetch origin --prune
git rebase origin/main
git push --force-with-lease
```

## 4) PR-05 mergen

```bash
gh pr merge 1103 --merge --delete-branch
```

## 5) PR-08 auf aktualisiertes main rebasen (nur nach Merge von 1103)

```bash
gh pr checkout 1104
git fetch origin --prune
git rebase origin/main
git push --force-with-lease
```

## 6) (optional) PR-08 Base auf main setzen, falls GitHub nicht automatisch aktualisiert hat

```bash
gh pr edit 1104 --base main
```

## 7) PR-08 mergen

```bash
gh pr merge 1104 --merge --delete-branch
```
