# D03A Closeout — [DRILL_NAME]

**Date:** YYYY-MM-DD HH:MM  
**Operator:** [operator_id]  
**Drill ID:** [e.g., D03B, D04, etc.]  
**PR Number:** [e.g., #633] (if applicable)  
**Session ID:** [optional: unique session identifier]

---

## Purpose

Post-drill documentation + risk sign-off. Provides:
- Scorecard (pass/fail per criterion with evidence)
- Findings (what we learned)
- Operator actions (follow-ups, if any)
- Risk officer sign-off

**Output:** Audit-ready drill run log

**Not for:**
- Pre-drill evidence (use TEMPLATE_D01_EVIDENCE_PACK.md)
- CI triage (use TEMPLATE_D02_CI_TRIAGE.md)

---

## Session Metadata

| Field | Value |
|-------|-------|
| **Drill Name** | [full drill name] |
| **Drill ID** | [e.g., D03B] |
| **Operator** | [operator ID] |
| **Date / Time** | [YYYY-MM-DD HH:MM] |
| **Duration** | [X minutes / hours] |
| **Timebox** | [Y minutes / hours] |
| **Timebox Exceeded?** | [Y/N] — [reason if yes] |
| **Git SHA (Start)** | [commit hash at start] |
| **Git SHA (End)** | [commit hash at end] |
| **Branch** | [branch name] |
| **PR Created** | [Y/N] — [PR # if yes] |
| **PR Merged** | [Y/N] — [merge SHA if yes] |

---

## Run Manifest

### Objective

[State the drill objective in 1-2 sentences]

**Example:**
```
Validate deterministic CI polling method (D03A) to eliminate
watch-timeout friction. Save 10-15 min/session for operators.
```

---

### Preconditions

**Pre-Drill State:**
- **Git Branch:** [branch name]
- **Git SHA:** [commit hash]
- **Working Tree:** [CLEAN / MODIFIED]
- **CI Baseline:** [last successful run ID]
- **Tool Versions:** [list key tools + versions]

**Evidence:** [link to evidence pack, e.g., `evidence_pack_20260109_2130.md`]

---

### Success Criteria (from Drill Charter)

List the original success criteria from M01 charter or drill pack:

1. [Criterion 1]
2. [Criterion 2]
3. [Criterion 3]
4. [Criterion 4]
5. [Criterion 5]
6. [Criterion 6]

---

## Execution Log (Summary)

**Note:** Full execution details should be in session notes or drill-specific log.
This is a high-level summary for closeout.

### Key Steps

| Step | Description | Outcome | Evidence |
|------|-------------|---------|----------|
| 1 | [Step 1 description] | [PASS / FAIL / SKIP] | [pointer to evidence] |
| 2 | [Step 2 description] | [PASS / FAIL / SKIP] | [pointer to evidence] |
| 3 | [Step 3 description] | [PASS / FAIL / SKIP] | [pointer to evidence] |
| ... | ... | ... | ... |

---

### Deviations from Procedure

[Document any deviations from the drill procedure]

**Example:**
```
- Deviated at Step 5: Used alternative command due to environment issue
- Reason: [explain why]
- Impact: [explain impact on results]
- Risk: [LOW / MED / HIGH] — [rationale]
```

**If no deviations:** [State "No deviations from drill procedure"]

---

## Scorecard (Pass/Fail per Criterion)

For each success criterion, provide:
- **Status:** PASS / FAIL / PARTIAL
- **Evidence:** Pointer to file, line, output, or CI check
- **Notes:** Brief explanation (if needed)

### Criterion 1: [Criterion text]

**Status:** [PASS / FAIL / PARTIAL]

**Evidence:**
- [Pointer 1: e.g., "File: docs/ops/drills/runs/DRILL_RUN_20260109_D03A_CI_POLLING.md:123"]
- [Pointer 2: e.g., "Terminal output: Step 2, line 45"]
- [Pointer 3: e.g., "CI check: docs-reference-targets-gate PASS"]

**Notes:** [Optional: explain if FAIL or PARTIAL]

---

### Criterion 2: [Criterion text]

**Status:** [PASS / FAIL / PARTIAL]

**Evidence:**
- [Pointer 1]
- [Pointer 2]

**Notes:** [Optional]

---

### Criterion 3: [Criterion text]

**Status:** [PASS / FAIL / PARTIAL]

**Evidence:**
- [Pointer 1]
- [Pointer 2]

**Notes:** [Optional]

---

[Repeat for all criteria]

---

### Scorecard Summary

| Criterion | Status | Evidence Count |
|-----------|--------|----------------|
| 1. [Short name] | [PASS/FAIL/PARTIAL] | [count] |
| 2. [Short name] | [PASS/FAIL/PARTIAL] | [count] |
| 3. [Short name] | [PASS/FAIL/PARTIAL] | [count] |
| ... | ... | ... |

**Overall:** [ALL PASS / PARTIAL PASS / FAIL]

**Pass Rate:** [X/Y criteria passed] ([Z%])

---

## Findings

### What We Learned

[Document key learnings from drill execution]

**Example:**
```
1. D03A method (deterministic polling) eliminates watch-timeout risk
   - Evidence: 3 polling runs, all <10s, no timeouts
   - Impact: 50-67% time savings vs. watch method

2. Branch names with "docs/" prefix trigger false positives
   - Evidence: docs-reference-targets-gate failure at PR #633
   - Mitigation: Use `<!-- pt:ref-target-ignore -->` tag

3. [Finding 3]
```

---

### Reproducibility

**Can another operator reproduce this drill?**

[Y / N / PARTIAL]

**Rationale:**
- [Factor 1: e.g., "Commands are exact and deterministic"]
- [Factor 2: e.g., "Evidence pointers are precise"]
- [Factor 3: e.g., "Environment documented"]

**Gaps (if any):**
- [Gap 1: e.g., "Missing tool version for X"]
- [Gap 2: e.g., "Vague reference at step Y"]

---

### Failure Modes (Encountered or Potential)

| Failure Mode | Likelihood | Impact | Mitigation |
|--------------|------------|--------|------------|
| [e.g., "Watch timeout"] | [HIGH/MED/LOW] | [time lost] | [use D03A method] |
| [e.g., "False positive link check"] | [MED] | [CI failure] | [use ignore tag] |
| ... | ... | ... | ... |

---

## Operator Actions (Follow-Ups)

### Required Actions

[List any required follow-up actions]

**Example:**
```
1. Update DOCS_REFERENCE_TARGETS_DEBT_GUIDE.md with "pseudo-path hazard" pattern
   - Owner: [name]
   - Deadline: [date]
   - Priority: [HIGH/MED/LOW]

2. Cross-link D03A how-to from Control Center runbooks
   - Owner: [name]
   - Deadline: [date]
   - Priority: [MED]
```

**If no required actions:** [State "No required follow-ups"]

---

### Optional Actions (Nice-to-Have)

[List any optional follow-up actions]

**Example:**
```
1. Consider adding CI polling to pre-commit hook (future enhancement)
2. Explore GitHub Actions status badge for drill runs
```

**If no optional actions:** [State "No optional follow-ups"]

---

## Risk Officer Review

**Role:** RISK_OFFICER  
**Reviewer:** [name/agent]  
**Review Date:** [YYYY-MM-DD HH:MM]

### Risk Assessment (Post-Drill)

**Risk Level:** [LOW / MED / HIGH]

**Rationale:**
- [Factor 1: e.g., "Docs-only scope maintained"]
- [Factor 2: e.g., "No live actions executed"]
- [Factor 3: e.g., "CI verified (all checks PASS)"]

**Risk Changes (vs. Pre-Drill):**
- [Change 1: e.g., "Risk level same (LOW → LOW)"]
- [Change 2: e.g., "No new risks introduced"]

---

### Governance Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **Docs-Only Scope** | [PASS/FAIL] | [git diff shows no src/ changes] |
| **No-Live Enforcement** | [PASS/FAIL] | [no trading actions in logs] |
| **Evidence-First** | [PASS/FAIL] | [all claims have pointers] |
| **SoD Maintained** | [PASS/FAIL] | [roles distinct, sign-offs present] |
| **CI Verification** | [PASS/FAIL] | [all required checks PASS] |

**Overall Compliance:** [COMPLIANT / NON-COMPLIANT]

**Issues (if any):**
- [Issue 1: e.g., "Minor scope creep at step X (resolved)"]
- [Issue 2: e.g., "SoD violation (same role for ORCHESTRATOR + RISK_OFFICER)"]

---

### Sign-Off

**Approved:** [Y / N / CONDITIONAL]

**Conditions (if conditional):**
- [Condition 1: e.g., "Fix issue X before committing"]
- [Condition 2: e.g., "Get second review from Y"]

**Signature:** [name/agent + timestamp]

---

## Final Validation Checklist

**Before Sign-Off (ORCHESTRATOR + RISK_OFFICER):**

- [ ] All success criteria met or deviations documented
- [ ] Evidence Pack complete (all claims have evidence)
- [ ] If M01 was bypassed: one-line bypass rationale + scope limitation recorded in run artifact and referenced in this Evidence Pack.
- [ ] CI verification complete (required checks PASS)
- [ ] Risk assessment signed off by RISK_OFFICER
- [ ] All SoD roles approved
- [ ] Closeout artifact is PR-ready (Summary/Why/Changes/Verification/Risk/How-To/References)

---

## SoD Sign-Off (All Roles)

| Role | Name/Agent | Timestamp | Status |
|------|------------|-----------|--------|
| **ORCHESTRATOR** | [name] | [timestamp] | [APPROVED/BLOCKED] |
| **FACTS_COLLECTOR** | [name] | [timestamp] | [APPROVED/BLOCKED] |
| **SCOPE_KEEPER** | [name] | [timestamp] | [APPROVED/BLOCKED] |
| **CI_GUARDIAN** | [name] | [timestamp] | [APPROVED/BLOCKED] |
| **RISK_OFFICER** | [name] | [timestamp] | [APPROVED/BLOCKED] |
| **EVIDENCE_SCRIBE** | [name] | [timestamp] | [APPROVED/BLOCKED] |

**Note:** Roles can be same person/agent, but sign-off must be explicit per role.

---

## Artifacts

### Primary Artifacts (Created During Drill)

| Artifact | Location | Status |
|----------|----------|--------|
| [Artifact 1] | [path] | [COMMITTED / PENDING / DRAFT] |
| [Artifact 2] | [path] | [COMMITTED / PENDING / DRAFT] |
| [Artifact 3] | [path] | [COMMITTED / PENDING / DRAFT] |

**Example:**
```
| Run Log | docs/ops/drills/runs/DRILL_RUN_20260109_D03A_CI_POLLING.md | COMMITTED |
| How-To | docs/ops/runbooks/RUNBOOK_CI_STATUS_POLLING_HOWTO.md | COMMITTED |
| Evidence Pack | docs/ops/drills/evidence_pack_20260109.md | DRAFT |
```

---

### Secondary Artifacts (Optional)

[List any secondary artifacts: screenshots, logs, CI reports, etc.]

**Example:**
```
- Terminal output: saved to session notes
- CI logs: GitHub Actions run #20864979695
- Screenshot: (if applicable)
```

---

## CI Verification

**PR Number:** [e.g., #633]  
**PR Status:** [MERGED / OPEN / CLOSED]

### Final CI Status

| Check Name | Status | Notes |
|------------|--------|-------|
| [Check 1] | [PASS/FAIL/SKIP] | [notes if needed] |
| [Check 2] | [PASS/FAIL/SKIP] | [notes if needed] |
| ... | ... | ... |

**Overall:** [ALL PASS / FAILURES / PENDING]

**Evidence:** [link to gh pr checks output or CI run URL]

---

## References

**Drill Pack:**
- [DRILL_PACK_M01_D03A_STANDARD.md](../DRILL_PACK_M01_D03A_STANDARD.md)

**Operator Drill Pack:**
- [OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](../OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md)

**Templates:**
- [TEMPLATE_M01_MISSION_KICKOFF.md](../templates/TEMPLATE_M01_MISSION_KICKOFF.md)
- [TEMPLATE_D01_EVIDENCE_PACK.md](../templates/TEMPLATE_D01_EVIDENCE_PACK.md)
- [TEMPLATE_D02_CI_TRIAGE.md](../templates/TEMPLATE_D02_CI_TRIAGE.md)

**Runbooks:**
- [RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](../../runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md)
- [RUNBOOK_CI_STATUS_POLLING_HOWTO.md](../../runbooks/RUNBOOK_CI_STATUS_POLLING_HOWTO.md)

**Past Runs:**
- [DRILL_RUN_20260109_D03A_CI_POLLING.md](../runs/DRILL_RUN_20260109_D03A_CI_POLLING.md)

---

## Change Log

- **[Date]:** Closeout completed (operator: [name])
