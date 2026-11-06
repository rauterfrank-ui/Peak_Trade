# Drill Session Template — AI Autonomy 4B Milestone 2

**Template Version:** 1.0  
**Purpose:** Standardized format for drill session documentation  
**Target Audience:** Operators executing drills from OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md  
**Last Updated:** 2026-01-09

---

## Session Metadata

**Session Information:**
- **Date/Time:** YYYY-MM-DDTHH:MM:SSZ
- **Drill ID:** D__ (e.g., D01, D02, ...)
- **Drill Name:** [Full drill name from pack]
- **Operator:** [Name or identifier]
- **Session Duration:** [Actual time taken] / [Timebox limit]
- **Git Ref (start):** [SHA at session start]
- **Branch (start):** [Branch name at session start]

**Roles (SoD):**
- ORCHESTRATOR: [Who coordinated the drill]
- FACTS_COLLECTOR: [Who gathered evidence]
- SCOPE_KEEPER: [Who enforced scope]
- CI_GUARDIAN: [Who validated gates]
- EVIDENCE_SCRIBE: [Who documented]
- RISK_OFFICER: [Who assessed risks]

**Scope & Constraints:**
- Docs-only: YES/NO
- Read-only operations: YES/NO
- Code changes: YES/NO (should be NO for drill sessions)
- Config changes: YES/NO (should be NO for drill sessions)

---

## Run Manifest

**Drill Objective:**
[One sentence: what this drill validates/trains]

**Preconditions:**
- [List all preconditions from drill pack]
- [E.g., Repository: /Users/frnkhrz/Peak_Trade]
- [E.g., Branch: main or feature branch]

**Expected Inputs:**
- [List specific inputs required]
- [E.g., PR number, file paths, config values]

**Expected Outputs:**
- [List artifacts that will be produced]
- [E.g., Operator Notes, Validator Reports, Evidence Pack]

**Pass/Fail Criteria (from Drill Pack):**
- [Criterion 1]: [Expected state]
- [Criterion 2]: [Expected state]
- [...]

**Timebox:** [Minutes allocated]

---

## Execution Log

Format: `[Timestamp] Step N: [Action] → [Observation] → [Evidence Pointer]`

### Step 1: [Step Name]
**Action:** [What was executed]  
**Command (if applicable):**
```bash
# Command here
```
**Observation:** [What happened]  
**Evidence Pointer:** [File path + line/section OR "see terminal output below"]  
**Status:** PASS / FAIL / PARTIAL

### Step 2: [Step Name]
**Action:** [What was executed]  
**Command (if applicable):**
```bash
# Command here
```
**Observation:** [What happened]  
**Evidence Pointer:** [File path + line/section OR "see terminal output below"]  
**Status:** PASS / FAIL / PARTIAL

### Step N: [Step Name]
**Action:** [What was executed]  
**Observation:** [What happened]  
**Evidence Pointer:** [File path + line/section OR "not verified"]  
**Status:** PASS / FAIL / PARTIAL

---

## Evidence Pointers

**Format:** `[Evidence ID] | [Type] | [Location] | [Note]`

| ID | Type | Location | Note |
|----|------|----------|------|
| E01 | Terminal Output | Step 1 command output | Repository root verification |
| E02 | Git Status | Step 2 command output | Branch tracking status |
| E03 | File Content | path/to/target_file.md:123-145 | Specific section reference |
| E04 | CI Check | GitHub Actions run #12345 | Lint gate result |
| ... | ... | ... | ... |

**Evidence Storage:**
- Terminal outputs: [Captured in this document OR external log file]
- Screenshots: [Path to screenshot files if applicable]
- Artifacts: [Path to generated artifacts]

---

## Scorecard

**Overall Result:** PASS / FAIL / PARTIAL

| Criterion | Expected | Actual | Pass/Fail | Evidence | Notes |
|-----------|----------|--------|-----------|----------|-------|
| [Criterion 1 from drill] | [Expected state] | [Observed state] | PASS/FAIL | E01, E02 | [Any clarifications] |
| [Criterion 2 from drill] | [Expected state] | [Observed state] | PASS/FAIL | E03 | [Any clarifications] |
| [Criterion N] | [Expected state] | [Observed state] | PASS/FAIL | E04, E05 | [Any clarifications] |

**Summary:**
- **Passed Criteria:** [Count]
- **Failed Criteria:** [Count]
- **Partial Criteria:** [Count]
- **Execution Time:** [Actual minutes] / [Timebox minutes]
- **Timebox Status:** WITHIN / EXCEEDED

---

## Findings & Operator Actions

### Top Findings (Max 5, Reproducible)

**Finding 1: [Title] (RISK LEVEL: LOW/MEDIUM/HIGH)**
- **Observation:** [What was observed]
- **Evidence:** [Pointer to evidence IDs]
- **Risk:** [Impact if not addressed]
- **Reproducibility:** [Steps to reproduce]

**Finding 2: [Title] (RISK LEVEL: LOW/MEDIUM/HIGH)**
- **Observation:** [What was observed]
- **Evidence:** [Pointer to evidence IDs]
- **Risk:** [Impact if not addressed]
- **Reproducibility:** [Steps to reproduce]

**Finding N: [Title] (RISK LEVEL: LOW/MEDIUM/HIGH)**
- **Observation:** [What was observed]
- **Evidence:** [Pointer to evidence IDs]
- **Risk:** [Impact if not addressed]
- **Reproducibility:** [Steps to reproduce]

### Operator Actions (Immediate)

**Action 1: [Title]**
- **Command/Steps:** [Exact commands or procedure]
- **Why:** [Justification]
- **Risk:** [Risk level if action is taken]
- **Status:** PENDING / COMPLETED / DEFERRED

**Action 2: [Title]**
- **Command/Steps:** [Exact commands or procedure]
- **Why:** [Justification]
- **Risk:** [Risk level if action is taken]
- **Status:** PENDING / COMPLETED / DEFERRED

### Common Failure Modes Encountered

| Failure Mode | Description | How Fixed | Prevention |
|--------------|-------------|-----------|------------|
| [Mode 1] | [What happened] | [How resolved] | [How to avoid next time] |
| [Mode 2] | [What happened] | [How resolved] | [How to avoid next time] |

---

## Follow-Ups (Docs-Only PR Suggestions)

**Follow-Up 1: [Title]**
- **Type:** Documentation update / New doc / Link fix / Clarification
- **Scope:** Docs-only (no code changes)
- **Files Affected:** [List files]
- **Justification:** [Why needed based on drill findings]
- **Priority:** LOW / MEDIUM / HIGH
- **Status:** PROPOSED / IN PROGRESS / COMPLETED

**Follow-Up 2: [Title]**
- **Type:** Documentation update / New doc / Link fix / Clarification
- **Scope:** Docs-only (no code changes)
- **Files Affected:** [List files]
- **Justification:** [Why needed based on drill findings]
- **Priority:** LOW / MEDIUM / HIGH
- **Status:** PROPOSED / IN PROGRESS / COMPLETED

---

## Session Closeout

**Operator Sign-Off:**
- **Operator:** [Name]
- **Date:** [ISO8601 timestamp]
- **Overall Assessment:** [Brief summary]
- **Drill Completion:** COMPLETE / INCOMPLETE / ABORTED
- **Next Drill Recommendation:** [D__ or "None"]

**Risk Officer Review:**
- **Reviewer:** [Name or role]
- **Risk Assessment:** [Summary of governance/safety risks]
- **Recommendation:** GO / NO-GO / GO-WITH-CONDITIONS
- **Conditions (if any):** [List any conditions]

**Artifact Preservation:**
- This session log: [File path where this document is saved]
- Supporting artifacts: [List paths to any additional files]
- CI artifacts: [Links to CI runs if applicable]

---

## References

**Drill Source:**
- Drill Pack: docs/ops/drills/OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md
- Drill Section: [Lines X-Y or specific section heading]

**Related Documentation:**
- Runbook: docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md
- Ops Index: docs/ops/README.md
- Template: docs/ops/drills/SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md (this document)

**Session Artifacts Index:**
- Evidence Packs: [Link to evidence pack index if applicable]
- Prior Session Logs: [Link to previous drill runs if applicable]

---

## Change Log

- **2026-01-09 (v1.0):** Initial template creation (standardized format for M2 drill sessions)
