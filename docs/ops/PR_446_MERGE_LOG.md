# PR #446 – Fix Moved Script Path References (Phase 1)

**Title:** docs(ci): fix moved script path references (phase1)  
**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/446  
**Merged:** 2025-12-30 (included in stacked PR #447)  
**Merge Commit:** via PR #447 (3be604b)  
**Branch:** `docs&#47;fix-moved-script-paths-phase1` → deleted  
**Change Type:** Docs-only (mechanical path updates)

## Summary

Mechanical documentation update to fix references to scripts that were moved to subdirectories (`scripts&#47;ci&#47;`, `scripts&#47;workflows&#47;`, `scripts&#47;utils&#47;`, `scripts&#47;automation&#47;`). Part of a three-phase docs cleanup effort to eliminate false positives in the docs-reference-targets-gate.

## Motivation

The docs-reference-targets-gate was reporting 30+ missing targets, primarily due to:
1. Scripts moved to subdirectories but doc references not updated
2. Stale references to `src&#47;data&#47;safety` without trailing slashes
3. Changed workflow file names (`.github&#47;workflows&#47;test.yml` → `ci.yml`)

These broken references created noise in CI and made it difficult to identify genuine documentation issues.

## Changes

### Script Path Updates (50+ occurrences in 18 files)

**CI Scripts:**
- `scripts&#47;validate_git_state.sh` → `scripts/ci/validate_git_state.sh`

**Workflow Scripts:**
- `scripts&#47;post_merge_workflow_pr203.sh` → `scripts/workflows/post_merge_workflow_pr203.sh`
- `scripts&#47;quick_pr_merge.sh` → `scripts/workflows/quick_pr_merge.sh`
- `scripts&#47;post_merge_workflow.sh` → `scripts/workflows/post_merge_workflow.sh`
- `scripts&#47;finalize_workflow_docs_pr.sh` → `scripts/workflows/finalize_workflow_docs_pr.sh`

**Utility Scripts:**
- `scripts&#47;render_last_report.sh` → `scripts/utils/render_last_report.sh`

**Automation Scripts:**
- `scripts&#47;update_pr_final_report_post_merge.sh` → `scripts/automation/update_pr_final_report_post_merge.sh`

**Workflow Files:**
- `.github&#47;workflows&#47;test.yml` → `.github/workflows/ci.yml`

**Package References:**
- `src&#47;data&#47;safety` → `src/data/safety/` (directory references with trailing slash)

## Files Changed

```
docs/adr/ADR_0001_Peak_Tool_Stack.md
docs/ops/GIT_STATE_VALIDATION.md
docs/ops/PR_110_MERGE_LOG.md
docs/ops/PR_112_MERGE_LOG.md
docs/ops/PR_121_MERGE_LOG.md
docs/ops/PR_136_MERGE_LOG.md
docs/ops/PR_204_MERGE_LOG.md
docs/ops/PR_208_MERGE_LOG.md
docs/ops/PR_61_FINAL_REPORT.md
docs/ops/PR_62_FINAL_REPORT.md
docs/ops/PR_63_FINAL_REPORT.md
docs/ops/PR_66_FINAL_REPORT.md
docs/ops/PR_90_MERGE_LOG.md
docs/ops/WORKFLOW_SCRIPTS.md
docs/reporting/EVIDENCE_CHAIN_INTEGRATION.md
docs/reporting/REPORTING_QUICKSTART.md
docs/runbooks/PRODUCTION_DEPLOYMENT_STABILITY_STACK.md
docs/ops/NEXT_STEPS_WORKFLOW_DOCS.md
```

**Total:** 18 files changed, 70 insertions(+), 70 deletions(-)

## Verification

### Before (missing targets):
```bash
$ rg "scripts&#47;validate_git_state\.sh" docs
# 11 occurrences with old path

$ rg "scripts&#47;post_merge_workflow_pr203\.sh" docs  
# 8 occurrences with old path
```

### After (all updated):
```bash
$ rg "scripts&#47;validate_git_state\.sh" docs
# 0 occurrences ✅

$ rg "scripts&#47;ci&#47;validate_git_state\.sh" docs
# 19 occurrences with correct path ✅

$ rg "scripts&#47;workflows&#47;post_merge_workflow_pr203\.sh" docs
# 13 occurrences with correct path ✅
```

### CI Checks
- ✅ All pre-commit hooks passed
- ✅ Lint Gate: SUCCESS
- ✅ Audit: SUCCESS  
- ✅ Docs Diff Guard: SUCCESS
- ⚠️  Docs Reference Targets Gate: Still failing (12 remaining false positives addressed in Phase 3)

## Risk Assessment

**🟢 MINIMAL RISK**

**Rationale:**
- Docs-only changes, no code modifications
- Mechanical path substitutions (no logic changes)
- All targets verified to exist in repository
- Comprehensive pre-commit validation passed

## Context

### Three-Phase Cleanup Strategy

This PR is **Phase 1** of a coordinated docs cleanup effort:

1. **Phase 1 (this PR):** Fix moved script path references
2. **Phase 2 (PR #447):** Add deprecated notices for removed scripts
3. **Phase 3 (PR #448):** De-pathify remaining false positives (branch names, example references)

**Stack Design:** PRs were stacked for clean review, with Phase 2 building on Phase 1, and Phase 3 on Phase 2.

### Integration

All three phases were merged together via stacked PR #447 (which included #446 changes) into main on 2025-12-30 at 23:07:36 UTC.

**Final Result:** Docs Reference Targets Gate: 30+ missing targets → 0 ✅

## Related Documentation

- PR #447: Phase 2 (deprecated notices)
- PR #448: Phase 3 (false positives)
- `docs/ops/GIT_STATE_VALIDATION.md` — Git state validation guide

---

**Status:** ✅ Merged (via stacked PR #447)  
**Docs-Reference-Targets-Gate Impact:** Reduced missing targets from 30 → 17  
**Follow-up:** Phase 2 and Phase 3 completed the cleanup to 0 missing targets
