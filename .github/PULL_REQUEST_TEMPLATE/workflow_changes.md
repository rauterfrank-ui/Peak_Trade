# PR: Workflow Changes

**PR Type:** Workflow / CI Configuration Change  
**Risk Level:** HIGH (Governance Surface)  
**Required Review:** Ops + Gate Guardian

---

## 1. WORKFLOW CHANGES SUMMARY

### Workflows Modified

List all workflow files changed in this PR:

- [ ] workflow file 1
- [ ] workflow file 2

### Change Type

- [ ] New workflow added
- [ ] Existing workflow modified
- [ ] Workflow deleted or disabled
- [ ] Job added or removed
- [ ] Step logic changed
- [ ] Conditional logic changed
- [ ] Path filters changed
- [ ] Schedule or trigger changed

---

## 2. RISK ASSESSMENT

### Required Checks Impact

**Does this PR modify any workflow that is configured as a required status check?**

- [ ] YES — High Risk: Changes affect merge-blocking checks
- [ ] NO — Standard Risk

**If YES, list affected required checks:**

1. Check name
2. Check name

### Path Filter Changes

**Does this PR modify path filters or trigger conditions?**

- [ ] YES — Document old vs new filters below
- [ ] NO

**If YES, provide before/after comparison:**

```yaml
# BEFORE
paths:
  - old/path/**

# AFTER
paths:
  - new/path/**
```

### Job Name or Check Name Changes

**Does this PR rename any jobs or change check names reported to GitHub?**

- [ ] YES — CRITICAL: This will break required checks configuration
- [ ] NO

**If YES, document the migration plan:**

---

## 3. GATE SAFETY VERIFICATION

### CI Gates Affected

Check all gates that may be impacted:

- [ ] docs-token-policy-gate
- [ ] docs-reference-targets-gate
- [ ] docs-diff-guard-policy-gate
- [ ] required-checks-hygiene-gate
- [ ] policy-critic-gate
- [ ] lint-gate
- [ ] var-report-regression-gate
- [ ] Other (specify)

### Pre-Merge Gate Run

**Have you run the affected gates locally or in a test branch?**

- [ ] YES — Gates passed
- [ ] YES — Gates failed, see mitigation below
- [ ] NO — Justification

**Gate Results:**

Paste relevant output or link to CI run.

---

## 4. TESTING PERFORMED

### Local Testing

```bash
# Example: Run workflow locally or validate syntax
act -l
yamllint .github/workflows/my-workflow.yml
```

**Results:** (Describe what you tested)

### Branch Protection Simulation

**Have you verified that this change does not break branch protection rules?**

- [ ] YES
- [ ] NO
- [ ] N/A

**Method:**

Describe how you tested merge-blocking behavior.

---

## 5. ROLLBACK PLAN

**If this PR causes CI failures or blocks merges, what is the rollback strategy?**

1. Revert commit hash
2. Hotfix alternative
3. Fast-forward fix

**Estimated Rollback Time:** (e.g., 5 minutes, 1 hour)

---

## 6. DOCUMENTATION UPDATES

**Have you updated relevant docs?**

- [ ] Runbook updated (if workflow is documented)
- [ ] README or ops docs updated
- [ ] No docs changes needed

**Links:**

List any doc files updated in this PR.

---

## 7. REVIEWER CHECKLIST (For Ops Team)

- [ ] Workflow syntax is valid
- [ ] No hardcoded secrets or tokens
- [ ] Path filters are correct and tested
- [ ] Job names match required checks config
- [ ] Triggers are appropriate for the workflow purpose
- [ ] No infinite loops or unbound retries
- [ ] Resource limits are set (timeout-minutes, etc)
- [ ] Gates are not bypassed unintentionally
- [ ] PR does not introduce Scope Creep
- [ ] Rollback plan is clear and actionable

---

## 8. ADDITIONAL CONTEXT

Provide any additional context, screenshots, or references:

- Related PRs
- GitHub Issues
- Design docs
- Incident postmortems

---

## MERGE CRITERIA

**This PR should NOT be merged until:**

- [ ] All required gates pass
- [ ] At least one Ops reviewer approves
- [ ] Rollback plan is documented
- [ ] No breaking changes to required checks (or migration plan is in place)

---

**Final Sign-Off:**

By merging this PR, I confirm that:
- I have verified the workflow changes locally or in a test environment
- I understand the risk to the governance surface
- I have a rollback plan if something goes wrong

**Operator:** @mention  
**Date:** YYYY-MM-DD
