# PR_726_MERGE_LOG — docs(ops): add PR template for workflow changes

## Summary

PR #726 merged via squash merge into main. Adds PR template system for high-risk workflow/CI configuration changes.

**Squash Commit:** `3a5f3c1d`  
**Merged:** 2026-01-14  
**Branch:** feature/pr-template-workflow-changes → main

## Why

Establish governance scaffolding for workflow-related PRs to enforce:
- Explicit risk assessment (required checks impact, path filters, job name changes)
- Gate safety verification
- Mandatory rollback planning
- Scope discipline

Workflow changes are high-risk (can break CI, block merges, bypass gates). This template ensures operators follow structured review process.

## Changes

**Files Added:** 2 (+409 lines, 0 deletions)

1. .github/PULL_REQUEST_TEMPLATE/workflow_changes.md (201 lines)
   - 8 sections: Workflow Changes Summary, Risk Assessment, Gate Safety Verification, Testing Performed, Rollback Plan, Documentation Updates, Reviewer Checklist, Additional Context
   - 47 checklist items
   - Required checks impact analysis
   - Path filter change tracking
   - Job name drift detection
   - Mandatory rollback plan

2. .github/PULL_REQUEST_TEMPLATE/README.md (208 lines)
   - Operator guide for template selection
   - 3 selection methods: GitHub UI, URL query param, gh CLI
   - Decision tree (workflow changes → workflow_changes.md)
   - Troubleshooting guide
   - Quick reference table

**Scope:** Docs-only, additive, no workflow logic modified.

## Verification

**Required Checks (10/10): ALL PASS**
- Docs Token Policy Gate: PASS (7s)
- Docs Reference Targets Gate: PASS (9s)
- Docs Diff Guard Policy Gate: PASS (7s)
- Policy Critic Gate: PASS (5s)
- Required Checks Hygiene Gate: PASS (8s)
- Lint Gate: PASS (6s)
- Workflow Dispatch Guard: PASS (8s)
- Policy Guard - No Tracked Reports: PASS (7s)
- Audit: PASS (1m25s)
- Test Health Automation/CI Health Gate: PASS (1m27s)

**Gate Compliance:**
- Token Policy: 0 violations (no inline backticks with unescaped slashes)
- Reference Targets: 0 broken links (no markdown links in templates)
- Diff Guard: Additive only (+409, -0)

**Local Verification Commands:**

```bash
# Verify files exist
ls -la .github/PULL_REQUEST_TEMPLATE/

# Expected output:
# README.md (208 lines, ~5KB)
# workflow_changes.md (201 lines, ~4KB)

# Check line counts
wc -l .github/PULL_REQUEST_TEMPLATE/*.md

# Verify no token policy violations
grep -n '`[^`]*\/[^`]*`' .github/PULL_REQUEST_TEMPLATE/*.md | grep -v '```'
# Expected: Empty (all slashes in fenced code blocks)

# Verify no markdown links (to avoid reference targets issues)
grep -n '\[.*\](.*\.md)' .github/PULL_REQUEST_TEMPLATE/*.md
# Expected: Empty (no relative markdown links)
```

## Risk

**Overall:** LOW

**Rationale:**
- Docs-only changes (no code, no workflows modified)
- Additive only (no deletions)
- Templates are opt-in (not auto-applied)
- No impact on existing PRs
- All required checks passed

**Potential Issues:**
- Template not showing in GitHub UI → Use URL query param
- Fields not applicable → Mark as N/A
- Confusion about usage → README provides decision tree

**Rollback:**
- Time: ~5 minutes
- Method: Revert squash commit or delete template directory
- Impact: None (templates not yet in use)

## Operator How-To

### Using the Template

**Method 1: GitHub UI (Automatic)**
- Create PR that changes files in .github/workflows/
- GitHub may auto-suggest workflow_changes.md template
- Select template from dropdown if multiple templates exist

**Method 2: URL Query Parameter**

```
https://github.com/rauterfrank-ui/Peak_Trade/compare/main...BRANCH?template=workflow_changes.md
```

Replace BRANCH with your feature branch name.

**Method 3: gh CLI**

```bash
# Interactive (opens browser with template selection)
gh pr create --web

# Or: Paste template content manually
gh pr create --body "$(cat .github/PULL_REQUEST_TEMPLATE/workflow_changes.md)"
```

### When to Use

Use workflow_changes.md template when PR includes:
- Changes to .github/workflows/ files
- Modifications to GitHub Actions workflows
- Updates to required status checks
- Path filter changes
- Job or check name changes

### Template Sections

**Must Complete:**
1. Workflow Changes Summary (list all modified workflows)
2. Risk Assessment (required checks impact, path filters, job names)
3. Gate Safety Verification (which gates affected)
4. Testing Performed (local validation)
5. Rollback Plan (how to revert if issues)

**Optional:**
6. Documentation Updates (if runbooks affected)
7. Additional Context (related PRs, issues, design docs)

### Reviewer Checklist

Ops reviewers should verify:
- Workflow syntax is valid
- No hardcoded secrets
- Path filters tested
- Job names match required checks config
- Rollback plan is clear
- Gates not bypassed

## References

- **PR #726:** https://github.com/rauterfrank-ui/Peak_Trade/pull/726
- **Branch:** feature/pr-template-workflow-changes
- **Runbook:** [RUNBOOK_PR726_MERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md](runbooks/RUNBOOK_PR726_MERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md)
- **Evidence Index:** [EV-20260114-PR726-WORKFLOW-PR-TEMPLATE](EVIDENCE_INDEX.md#ev-20260114-pr726-workflow-pr-template)
- **Template Files:**
  - .github/PULL_REQUEST_TEMPLATE/README.md (operator guide)
  - .github/PULL_REQUEST_TEMPLATE/workflow_changes.md (template)

---

**Post-Merge Actions:**
1. Fill in squash commit SHA above
2. Update evidence index with commit SHA
3. Verify templates appear in GitHub UI
4. Test template selection via URL query param
5. Communicate template availability to team
