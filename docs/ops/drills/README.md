# Drills — AI Autonomy & Operator Competency Validation

**Purpose:** Central index for operator drill packs, templates, and run logs  
**Audience:** Operators executing Cursor Multi-Agent drills  
**Last Updated:** 2026-01-09

---

## Overview

This directory contains:
1. **Drill Packs** — Collections of drills for systematic competency validation
2. **Templates** — Standardized templates for drill lifecycle phases
3. **Run Logs** — Evidence-based drill execution documentation
4. **Backlog** — Candidate drills for future execution

---

## Drill Packs

### Primary Pack: AI Autonomy 4B Milestone 2

**File:** [OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md)

**Contains:**
- **D01–D08:** Operational drills (pre-flight, scope lock, evidence pack, CI triage, etc.)
- **M01:** Meta-drill for evidence-based drill selection

**Usage:** Select a drill from this pack and follow the procedure step-by-step.

---

### Standard Drill Pack: M01 → D03A Lifecycle

**File:** [DRILL_PACK_M01_D03A_STANDARD.md](DRILL_PACK_M01_D03A_STANDARD.md)

**Contains:**
- Standardized templates for complete drill lifecycle
- M01 → D01 → Drill Execution → D02 → D03A flow
- Guardrails: docs-only, evidence-first, SoD enforcement

**Usage:** Use this pack for structured drill execution with audit-ready outputs.

---

## Templates

All templates are located in [templates/](templates/).

| Phase | Template | Purpose |
|-------|----------|---------|
| **M01** | [TEMPLATE_M01_MISSION_KICKOFF.md](templates/TEMPLATE_M01_MISSION_KICKOFF.md) | Evidence-based drill selection (meta-drill) |
| **D01** | [TEMPLATE_D01_EVIDENCE_PACK.md](templates/TEMPLATE_D01_EVIDENCE_PACK.md) | Pre-flight evidence snapshot |
| **D02** | [TEMPLATE_D02_CI_TRIAGE.md](templates/TEMPLATE_D02_CI_TRIAGE.md) | CI monitoring + failure triage (D03A method) |
| **D03A** | [TEMPLATE_D03A_CLOSEOUT.md](templates/TEMPLATE_D03A_CLOSEOUT.md) | Post-drill closeout + risk sign-off |

**Usage:**
1. Copy template to appropriate location
2. Rename following naming convention (see [runs/README.md](runs/README.md))
3. Fill in during drill execution
4. Save as drill run log after completion

---

## Run Logs

**Location:** [runs/](runs/)

**Purpose:** Evidence-based documentation of drill executions

**Naming Convention:** `DRILL_RUN_YYYYMMDD_HHMM_<operator>_<drill_id>.md`

**Examples:**
- [DRILL_RUN_20260109_1930_ai_autonomy_D01.md](runs/DRILL_RUN_20260109_1930_ai_autonomy_D01.md) — Pre-Flight Discipline (D01)
- [DRILL_RUN_20260109_D03A_CI_POLLING.md](runs/DRILL_RUN_20260109_D03A_CI_POLLING.md) — CI Polling without Watch Timeouts (D03A)

**Guidelines:** See [runs/README.md](runs/README.md) for quality standards and lifecycle.

---

## Backlog

**Location:** [backlog/](backlog/)

**Purpose:** Candidate drills for future execution

**File:** [backlog/DRILL_BACKLOG.md](backlog/DRILL_BACKLOG.md)

**Contains:**
- D03A–D03D candidates (from D02 meta-drill selection)
- Prioritized by scoring matrix (Operator Value, Risk Reduction, Frequency, etc.)
- Each candidate includes: problem statement, success criteria, artifacts, time-to-run

**Usage:** Refer to this backlog when selecting next drill (M01 process).

---

## Session Templates

**File:** [SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md](SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md)

**Purpose:** Freeform session notes template

**Usage:**
- For ad-hoc sessions (not following drill pack)
- For quick notes during drill execution
- For exploratory work (spikes, investigations)

**Note:** Structured drills should use lifecycle templates (M01/D01/D02/D03A) instead.

---

## Workflow Diagram (Drill Lifecycle)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. SELECT DRILL                                              │
│    - From OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md           │
│    - OR from M01 meta-drill (evidence-based selection)       │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. PRE-FLIGHT (D01)                                          │
│    - Copy TEMPLATE_D01_EVIDENCE_PACK.md                      │
│    - Capture baseline: Git, CI, tools, environment          │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. DRILL EXECUTION                                           │
│    - Follow drill-specific procedure                         │
│    - Log steps, observations, evidence in real-time          │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. CI TRIAGE (D02)                                           │
│    - Copy TEMPLATE_D02_CI_TRIAGE.md                          │
│    - Use D03A method (deterministic polling, no --watch)     │
│    - Fix failures (if any) + verify                          │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. CLOSEOUT (D03A)                                           │
│    - Copy TEMPLATE_D03A_CLOSEOUT.md                          │
│    - Scorecard (pass/fail per criterion)                     │
│    - Findings + operator actions                             │
│    - Risk officer sign-off                                   │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. SAVE RUN LOG                                              │
│    - Save to runs/ (following naming convention)             │
│    - Optional: Commit via docs-only PR                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Guardrails (Non-Negotiable)

### 1. Docs-Only (Default)
- No changes under `src/`, `config/`, `tests/` unless drill explicitly requires
- Any code changes must be approved by RISK_OFFICER + CI_GUARDIAN

### 2. Evidence-First
- Every claim backed by: file path, line number, terminal output, CI check, or GitHub link
- No "magic" assertions

### 3. Separation of Duties (SoD)
- Roles must remain distinct: ORCHESTRATOR, FACTS_COLLECTOR, SCOPE_KEEPER, CI_GUARDIAN, RISK_OFFICER, EVIDENCE_SCRIBE
- Decisions require multi-role sign-off

### 4. No Assumptions
- If unclear: mark as `[ASSUMPTION: ...]` and document
- Prefer explicit over implicit

### 5. Terminal Pre-Flight (Always)
```bash
# Pre-Flight: Ctrl-C to stop any running process
cd /path/to/repo || cd "$(git rev-parse --show-toplevel)"
pwd
git status -sb
```

---

## Quality Standards

A "good" drill execution exhibits:

### Evidence-First ✅
- Every claim has pointer: `file:line`, `CI check name`, `terminal output line X`
- No "probably", "should be", "looks like"

### Reproducible ✅
- Same inputs + same environment → same result
- Commands are exact (not paraphrased)
- Git SHA documented at start

### SoD-Compliant ✅
- Roles clearly assigned (no "I did everything")
- Decisions have multi-role sign-off

### Deterministic ✅
- Pass/fail criteria are objective (not subjective)
- CI checks are concrete

### Audit-Ready ✅
- Outsider can understand what was done and why
- Evidence is verifiable (links work, files exist)
- Risk assessment is explicit

---

## Related Documentation

**Runbooks:**
- [RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](../runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md) — Multi-agent workflow
- [RUNBOOK_CI_STATUS_POLLING_HOWTO.md](../runbooks/RUNBOOK_CI_STATUS_POLLING_HOWTO.md) — D03A method (CI polling)

**Ops Index:**
- [docs/ops/README.md](../README.md) — Central ops documentation hub

**Evidence Index:**
- [docs/ops/EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) — Consolidated evidence pointers

---

## Quick Start

### For New Operators

1. **Read this README** — Understand structure and guardrails
2. **Review a past run** — See example: [DRILL_RUN_20260109_D03A_CI_POLLING.md](runs/DRILL_RUN_20260109_D03A_CI_POLLING.md)
3. **Select a drill** — From [OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md)
4. **Use templates** — Follow M01 → D01 → Execution → D02 → D03A flow
5. **Save run log** — Document in [runs/](runs/) directory

### For Experienced Operators

1. **M01 Meta-Drill** — Select next drill via [TEMPLATE_M01_MISSION_KICKOFF.md](templates/TEMPLATE_M01_MISSION_KICKOFF.md)
2. **Execute Drill** — Follow selected drill procedure
3. **Use Lifecycle Templates** — D01 (evidence), D02 (CI), D03A (closeout)
4. **Commit Run Log** — If significant findings, commit via docs-only PR

---

## Change Log

- **2026-01-09 (v1.0):** Initial README creation (drill packs, templates, workflow)
