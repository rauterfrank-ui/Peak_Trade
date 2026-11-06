# M01 Mission Kickoff — [DRILL_NAME]

**Date:** YYYY-MM-DD  
**Operator:** [operator_id]  
**Session ID:** [optional: unique session identifier]  
**Scope:** docs-only (unless specified otherwise below)

---

## Purpose

Evidence-based drill selection (meta-drill). Select the next most valuable drill based on:
- Past drill runs (patterns, pain points)
- Recent PRs (failures, friction)
- CI signals (flaky checks, timeouts)
- Operator pain points (recurring issues)

**Output:** Selected drill + charter (scope, criteria, artifacts, CI plan)

---

## Roles

- **ORCHESTRATOR:** [name/agent] — Coordinates decision, final call (with SoD)
- **FACTS_COLLECTOR:** [name/agent] — Gathers evidence (runs, PRs, CI logs)
- **SCOPE_KEEPER:** [name/agent] — Enforces guardrails, blocks scope creep
- **CI_GUARDIAN:** [name/agent] — Defines CI verification plan
- **RISK_OFFICER:** [name/agent] — Assesses risk, approves/blocks drill
- **EVIDENCE_SCRIBE:** [name/agent] — Writes charter + artifacts

**Note:** Roles can be same person/agent, but must switch hats explicitly.

---

## Discovery Checklist

Gather evidence from the following sources:

### 1. Past Drill Runs

**Location:** `docs/ops/drills/runs/`

| Run | Date | Drill ID | Outcome | Pain Points |
|-----|------|----------|---------|-------------|
| [DRILL_RUN_20260109_D03A_CI_POLLING.md](../runs/DRILL_RUN_20260109_D03A_CI_POLLING.md) | 2026-01-09 | D03A | PASS | [note any friction] |
| ... | ... | ... | ... | ... |

**Key Findings:**
- [Finding 1 with evidence pointer: file:line]
- [Finding 2 with evidence pointer: file:line]
- [Finding 3 with evidence pointer: file:line]

---

### 2. Recent PRs (AI Autonomy / Ops Context)

**Query:** `gh pr list --state merged --limit 10 --json number,title,mergedAt,labels`

| PR # | Title | Merged | Friction / Learnings |
|------|-------|--------|----------------------|
| #633 | D03A drill | 2026-01-09 | [e.g., docs-reference-targets-gate failure] |
| #632 | D02 meta-drill | 2026-01-09 | [e.g., forward references needed ignores] |
| ... | ... | ... | ... |

**Key Findings:**
- [Finding 1 with PR link]
- [Finding 2 with PR link]
- [Finding 3 with PR link]

---

### 3. CI Signals (Failures / Flaky Checks)

**Query:** `gh run list --limit 20 --json conclusion,workflowName,createdAt`

| Run ID | Workflow | Conclusion | Notes |
|--------|----------|------------|-------|
| 20864979695 | CI Health Gate | SUCCESS | [any observations] |
| ... | ... | ... | ... |

**Flaky/Failing Checks:**
- [Check name] — Failure rate: X% (evidence: run IDs)
- [Check name] — Timeout rate: Y% (evidence: run IDs)

**Key Findings:**
- [Finding 1 with run link]
- [Finding 2 with run link]

---

### 4. Operator Pain Points (Last 7–14 Days)

**Source:** Runbooks, session notes, chat logs

| Pain Point | Frequency | Impact | Evidence |
|------------|-----------|--------|----------|
| [e.g., "watch timeouts"] | High (5+ times) | 10-15 min/session lost | [link to runbook section] |
| [e.g., "link debt"] | Medium (3 times) | CI failures | [link to past run] |
| ... | ... | ... | ... |

**Key Findings:**
- [Finding 1 with evidence]
- [Finding 2 with evidence]

---

### 5. Open TODOs (from Runbooks / Closeouts)

**Source:** `grep -r "TODO\|FIXME\|FOLLOW-UP" docs/ops/`

| TODO | Source | Priority | Effort |
|------|--------|----------|--------|
| [TODO text] | [file:line] | [HIGH/MED/LOW] | [hours estimate] |
| ... | ... | ... | ... |

**Key Findings:**
- [Finding 1]
- [Finding 2]

---

## Candidate Backlog (3–7 Options)

For each candidate, provide:
- **Kurzname:** D0X-Kandidat
- **Problem Statement:** What pain point does it address?
- **Operator Value:** Time saved / friction removed
- **Risk / Blast Radius:** LOW / MED / HIGH + rationale
- **Prereqs:** Tools, paths, CI jobs needed
- **Success Criteria:** 3–6 measurable bullets
- **Artifacts:** Expected outputs
- **Time-to-Run:** Estimated duration

### Candidate 1: [DRILL_NAME_1]

**Problem Statement:**
[Describe the pain point this drill addresses]

**Operator Value:**
[Time saved / friction removed / risk reduced]

**Risk / Blast Radius:** [LOW / MED / HIGH]
[Rationale: why this risk level?]

**Prereqs:**
- [Tool or condition 1]
- [Tool or condition 2]
- ...

**Success Criteria:**
1. [Criterion 1 — measurable]
2. [Criterion 2 — measurable]
3. [Criterion 3 — measurable]
4. ...

**Artifacts:**
- [Expected output 1: file or report]
- [Expected output 2: file or report]
- ...

**Time-to-Run:** [X minutes / hours]

---

### Candidate 2: [DRILL_NAME_2]

[Repeat structure from Candidate 1]

---

### Candidate 3: [DRILL_NAME_3]

[Repeat structure from Candidate 1]

---

[Add more candidates as needed, up to 7 maximum]

---

## Scoring Matrix

Score each candidate 1–5 (5 = best). Weighted scoring:

| Criterion | Weight | Leitfrage |
|-----------|-------:|-----------|
| **Operator Value** | 3 | Saves time/nerves in next 2 weeks? |
| **Risk Reduction** | 3 | Lowers governance/CI risk measurably? |
| **Frequency** | 2 | How often does problem occur? |
| **Time-to-Run** | 2 | Can complete in <90 min? |
| **Determinism** | 2 | Output stable/reproducible? |
| **Dependency Load** | 1 | New tools/refactors needed? (lower = better) |

**Scoring:**

| Candidate | Op Value (×3) | Risk Red (×3) | Freq (×2) | Time (×2) | Determ (×2) | Dep (×1) | **Total** |
|-----------|---------------|---------------|-----------|-----------|-------------|----------|-----------|
| [Name 1]  | [score] ×3 = X | [score] ×3 = X | [score] ×2 = X | [score] ×2 = X | [score] ×2 = X | [score] ×1 = X | **[SUM]** |
| [Name 2]  | ... | ... | ... | ... | ... | ... | **[SUM]** |
| [Name 3]  | ... | ... | ... | ... | ... | ... | **[SUM]** |

**Note:** Highest score does NOT auto-win if Risk/Blast Radius is unacceptable.

---

## Final Decision (with SoD Sign-Off)

**Selected Drill:** [DRILL_ID] — [DRILL_NAME]

**Rationale (Evidence-Based):**
1. [Reason 1 with evidence pointer]
2. [Reason 2 with evidence pointer]
3. [Reason 3 with evidence pointer]

**Risk Posture:** [LOW / MED / HIGH]
[Justification: why acceptable?]

**SoD Sign-Off:**
- **ORCHESTRATOR:** [signature/timestamp] — Final decision
- **RISK_OFFICER:** [signature/timestamp] — Risk acceptable
- **CI_GUARDIAN:** [signature/timestamp] — CI plan sound
- **SCOPE_KEEPER:** [signature/timestamp] — Scope within guardrails

---

## Drill Charter (for Selected Drill)

### Drill ID & Title
**ID:** [e.g., D03B]  
**Title:** [e.g., "Docs Reference Targets Fast-Path Triage"]

### Scope
- **Type:** [docs-only / code-safe / mixed]
- **Files:** [paths or patterns, e.g., docs/ops/]
- **Out-of-Scope:** [explicitly excluded paths or actions]

### Success Criteria (3–6 Measurable Bullets)
1. [Criterion 1]
2. [Criterion 2]
3. [Criterion 3]
4. [Criterion 4]
5. [Criterion 5]
6. [Criterion 6]

### Primary Artifacts (Minimum 2)
1. [Artifact 1 with expected path]
2. [Artifact 2 with expected path]
3. [Optional: Artifact 3]

### CI Verification Plan
- **Expected Checks:** [list check names that must pass]
- **Expected Skipped:** [list checks expected to skip]
- **Failure Tolerance:** [any known flaky checks?]

### Operator Playbook (Max 12 Lines)
```bash
# Step 1: [description]
[command 1]

# Step 2: [description]
[command 2]

# Step 3: [description]
[command 3]

# ... (up to 12 lines total)
```

### Start Conditions
- [Condition 1: e.g., "On main branch, clean working tree"]
- [Condition 2: e.g., "CI baseline: last run SUCCESS"]
- [Condition 3: e.g., "Tool X version Y installed"]

### Stop Conditions
- [Condition 1: e.g., "Timebox exceeded (>90 min)"]
- [Condition 2: e.g., "Scope creep detected (non-docs changes)"]
- [Condition 3: e.g., "Risk escalation (unacceptable failure mode)"]

---

## References

**Drill Pack:**
- [OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](../OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md)

**Past Runs:**
- [DRILL_RUN_20260109_D03A_CI_POLLING.md](../runs/DRILL_RUN_20260109_D03A_CI_POLLING.md)
- [Add other relevant runs]

**Runbooks:**
- [RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](../../runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md)
- [RUNBOOK_CI_STATUS_POLLING_HOWTO.md](../../runbooks/RUNBOOK_CI_STATUS_POLLING_HOWTO.md)

---

## Change Log

- **[Date]:** Initial kickoff (operator: [name])
