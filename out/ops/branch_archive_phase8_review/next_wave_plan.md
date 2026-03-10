# Next Wave Plan — Phase 8 Review

**Stand:** 2026-03-10

## Wave 9: Safest Archive/Disposal Proof Wave

### Goal
Establish proof of duplication or supersession for branches before any archive/disposal. No deletions; evidence collection only.

### Target Branches/Groups
1. **execution-networked p122–p132** (8 branches) — cycle closed; diff vs main to confirm duplication
2. **backup/\*** (9 branches) — snapshot branches; diff vs main to confirm no unique content
3. **tmp/stack-test** — scratch; quick diff proof
4. **wip/local-*** (2) — local snapshots; diff proof

### Safety Gates
- No branch deletions
- No remote mutation
- Diff output only; no code changes
- Go/no-go: if any branch shows unique high-value content, escalate to MANUAL_DEEP_REVIEW

### Required Evidence
- `git diff main..<branch> --stat` for each target
- `git log main..<branch> --oneline` (last 5) for each
- Summary: unique files, unique commits, overlap %

### Go/No-Go Criteria
- **Go:** All target branches show >95% overlap with main or clearly superseded
- **No-Go:** Any branch shows unique logic in src/, tests/, or critical config

---

## Wave 10: Highest-Value Remaining Implementation/Salvage Wave

### Goal
Prioritize salvage or implementation of top-value branches: p101, p22, p80, p99-launchd-hard, p28, p29, wip/salvage-* (rescue remotes).

### Target Branches/Groups
1. **KEEP_FOR_FUTURE_IMPL** (4): p101, p22, p80, p99-launchd-hard
2. **High-value ARCHIVE_REVIEW** (2): p28, p29
3. **MANUAL_DEEP_REVIEW with rescue remotes** (2): wip/salvage-code-tests-untracked, wip/untracked-salvage

### Safety Gates
- No live execution changes
- No autonomous merges
- Each salvage requires: diff review, test run, operator approval
- docs/GOVERNANCE_DATAFLOW_REPORT.md and docs/REPO_AUDIT_REPORT.md remain untouched <!-- pt:ref-target-ignore -->

### Required Evidence
- Diff vs main for each
- Test status (if applicable)
- Conflict assessment
- Salvage checklist per branch

### Go/No-Go Criteria
- **Go:** Operator approves salvage plan; no conflicts with governance locks
- **No-Go:** Conflicts with main, test failures, or governance risk

---

## Ordering

1. **Wave 9 first** — establishes proof baseline; no execution risk
2. **Wave 10 second** — uses Wave 9 evidence; focuses on high-value salvage

## No Execution Yet

This plan is review-only. No branches deleted, merged, or rebased in this wave.
