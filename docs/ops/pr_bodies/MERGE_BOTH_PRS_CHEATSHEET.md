# Merge Both PRs (DOCS → FEATURE) — Cheat-Sheet

**Script:** `scripts/ops/merge_both_prs.sh`  
**Full docs:** `docs/ops/README.md` (Sektion **"Merge both PRs (DOCS → FEATURE) — fail-fast helper"**)

---

## 🚀 Quick Start

```bash
# Standard (alle Defaults)
DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# DRY_RUN (nur Checks)
DRY_RUN=true DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Personal Repo (ohne Approval)
REQUIRE_APPROVAL=false DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Fast (CI schon grün)
WATCH_CHECKS=false RUN_PYTEST=false DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

<!-- BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW -->

### Workflow: DRY_RUN → Real Merge

```bash
# Step 1: Test erst (DRY_RUN)
DRY_RUN=true DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Falls Output: "✅ Done. Both PRs processed."
# → Alle Checks grün!

# Step 2: Echtes Merge
DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
```

**Warum DRY_RUN?**
- ✅ Testet alle Fail-Fast-Checks (state, draft, base, mergeable, reviewDecision)
- ✅ Kein Merge, keine Git-State-Changes
- ✅ Safe-by-default Testing vor echtem Merge

<!-- END MERGE_BOTH_PRS_DRYRUN_WORKFLOW -->
```

---

## 🎛️ Alle Knobs

```bash
REQUIRE_APPROVAL=true|false       # Default: true
FAIL_ON_DRAFT=true|false         # Default: true
WATCH_CHECKS=true|false          # Default: true
DELETE_BRANCH=true|false         # Default: true
UPDATE_MAIN=true|false           # Default: true
RUN_PYTEST=true|false            # Default: true
DRY_RUN=true|false               # Default: false
MERGE_METHOD=squash|merge|rebase # Default: squash
BASE_BRANCH=main                 # Default: main
PYTEST_CMD="python -m pytest -q" # Default: "python -m pytest -q"
```

---

## 🔥 Common Use Cases

### Self-Approve + Merge
```bash
gh pr review 123 --approve
gh pr review 124 --approve
DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
```

### Custom Base-Branch
```bash
BASE_BRANCH=feat/my-branch DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
```

### Rebase statt Squash
```bash
MERGE_METHOD=rebase DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
```

---

## 🚨 Error Quick-Fixes

**PR not approved:**
```bash
gh pr review 123 --approve
# oder: REQUIRE_APPROVAL=false override
```

**PR is DRAFT:**
```bash
gh pr ready 123
# oder: FAIL_ON_DRAFT=false override
```

**Working tree dirty:**
```bash
git stash push -u -m "temp"
# run script
git stash pop
```

---

**Version:** 1.0.0 | **Maintainer:** Peak_Trade Ops Team
