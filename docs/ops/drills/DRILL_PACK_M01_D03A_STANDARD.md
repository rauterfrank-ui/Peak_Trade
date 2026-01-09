# Drill Pack: M01 → D03A Standard

**Version:** 1.0  
**Last Updated:** 2026-01-09  
**Target Audience:** Operators executing Cursor Multi-Agent drills  
**Scope:** docs-only (unless explicitly stated in specific drill)

---

## Purpose

This drill pack provides **standardized templates** for the complete drill lifecycle:

1. **M01 Mission Kickoff** — Evidence-based drill selection (meta-drill)
2. **D01 Evidence Pack** — Pre-flight + evidence collection
3. **D02 CI Triage** — Deterministic CI monitoring + failure drill-down
4. **D03A Closeout** — Post-drill documentation + risk sign-off

**Not a Replacement:**
- Does NOT replace `OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md` (D01-D08 drills)
- Does NOT replace session templates (those remain for freeform notes)

**Complements:**
- Provides structured templates for **each phase** of drill execution
- Ensures evidence-first, SoD-compliant, audit-ready outputs

---

## Guardrails (Non-Negotiable)

### 1. Docs-Only (Default)
- No changes under `src/`, `config/`, `tests/` unless drill explicitly requires it
- Any code changes must be approved by RISK_OFFICER + CI_GUARDIAN

### 2. Evidence-First
- Every claim must be backed by: file path, line number, terminal output, CI check, or GitHub link
- No "magic" assertions: "it works" → "PASS at line 72 of output.txt"

### 3. Separation of Duties (SoD)
Roles must remain distinct:
- **ORCHESTRATOR:** Coordinates, makes final decisions (with SoD input)
- **FACTS_COLLECTOR:** Gathers evidence (files, logs, CI checks)
- **SCOPE_KEEPER:** Enforces guardrails, prevents scope creep
- **CI_GUARDIAN:** Defines CI verification, interprets check results
- **RISK_OFFICER:** Assesses risk, approves/blocks decisions
- **EVIDENCE_SCRIBE:** Writes artifacts (run logs, reports)

**Anti-Pattern:** One role doing everything → violates SoD

### 4. No Assumptions
- If unclear: mark as `[ASSUMPTION: ...]` and document
- Prefer explicit over implicit
- Prefer deterministic over "should work"

### 5. Terminal Pre-Flight (Always)
Every terminal block starts with:
```bash
# Pre-Flight: Ctrl-C to stop any running process
cd /path/to/repo || cd "$(git rev-parse --show-toplevel)"
pwd
git status -sb
```

---

## Drill Lifecycle (Standard Flow)

```
┌──────────────────────────────────────────────────────────────┐
│ M01 — MISSION KICKOFF (Meta-Drill)                          │
│ - Evidence-based drill selection                            │
│ - Scoring matrix (Operator Value, Risk, Frequency, etc.)    │
│ - Output: Selected drill + charter                          │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ D01 — EVIDENCE PACK (Pre-Flight)                            │
│ - Git status, working tree, CI baseline                     │
│ - Tool versions, environment                                │
│ - Output: Evidence pack (snapshot of repo state)            │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ DRILL EXECUTION (from selected drill)                        │
│ - Follow drill-specific procedure                           │
│ - Log steps, observations, evidence in real-time            │
│ - Output: Execution log + artifacts                         │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ D02 — CI TRIAGE (Validation)                                │
│ - Deterministic CI polling (no --watch)                     │
│ - Failure drill-down (if needed)                            │
│ - Output: CI status report + failure logs (if any)          │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ D03A — CLOSEOUT (Documentation)                             │
│ - Scorecard (pass/fail per criterion)                       │
│ - Findings + operator actions                               │
│ - Risk officer sign-off                                     │
│ - Output: Drill run log (audit-ready)                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Templates

| Phase | Template | Purpose |
|-------|----------|---------|
| **M01** | [TEMPLATE_M01_MISSION_KICKOFF.md](templates/TEMPLATE_M01_MISSION_KICKOFF.md) | Evidence-based drill selection |
| **D01** | [TEMPLATE_D01_EVIDENCE_PACK.md](templates/TEMPLATE_D01_EVIDENCE_PACK.md) | Pre-flight evidence snapshot |
| **D02** | [TEMPLATE_D02_CI_TRIAGE.md](templates/TEMPLATE_D02_CI_TRIAGE.md) | CI monitoring + failure triage |
| **D03A** | [TEMPLATE_D03A_CLOSEOUT.md](templates/TEMPLATE_D03A_CLOSEOUT.md) | Post-drill closeout + sign-off |

---

## Usage Workflow

### Step 1: Mission Kickoff (M01)

**When:** At start of drill session or when selecting next drill

```bash
# Copy template
cp docs/ops/drills/templates/TEMPLATE_M01_MISSION_KICKOFF.md \
   docs/ops/drills/M01_MISSION_KICKOFF_$(date +%Y%m%d).md

# Fill in:
# - Discovery checklist (past runs, PRs, pain points)
# - Candidate backlog (3-7 options)
# - Scoring matrix (Operator Value, Risk, Frequency, etc.)
# - Final decision with SoD sign-off
```

**Output:** Selected drill + charter (scope, criteria, artifacts, CI plan)

---

### Step 2: Evidence Pack (D01)

**When:** Before executing selected drill

```bash
# Copy template
cp docs/ops/drills/templates/TEMPLATE_D01_EVIDENCE_PACK.md \
   docs/ops/drills/evidence_pack_$(date +%Y%m%d_%H%M).md

# Fill in:
# - Git status (SHA, branch, working tree)
# - CI baseline (last successful run)
# - Tool versions (gh, uv, ruff, etc.)
# - Environment (OS, shell, Python version)
```

**Output:** Evidence pack (baseline for drill execution)

---

### Step 3: Drill Execution

**When:** After evidence pack complete

**Follow drill-specific procedure from:**
- `OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md` (D01-D08)
- OR drill charter from M01 (for new/custom drills)

**Log in real-time:**
- Commands executed
- Observations (what happened)
- Evidence pointers (file:line, CI check, terminal output)
- Deviations from procedure

**Output:** Execution log (use session template or drill-specific format)

---

### Step 4: CI Triage (D02)

**When:** After drill execution, before closeout

```bash
# Copy template
cp docs/ops/drills/templates/TEMPLATE_D02_CI_TRIAGE.md \
   docs/ops/drills/ci_triage_$(date +%Y%m%d_%H%M).md

# Fill in:
# - PR number (if applicable)
# - CI status (using deterministic polling)
# - Failing checks (if any) with drill-down
# - Fix applied (if needed)
```

**Output:** CI status report + failure logs (if any)

---

### Step 5: Closeout (D03A)

**When:** After drill complete + CI verified

```bash
# Copy template
cp docs/ops/drills/templates/TEMPLATE_D03A_CLOSEOUT.md \
   docs/ops/drills/runs/DRILL_RUN_$(date +%Y%m%d_%H%M)_<operator>_<drill_id>.md

# Fill in:
# - Scorecard (pass/fail per criterion with evidence)
# - Findings (what we learned)
# - Operator actions (follow-ups, if any)
# - Risk officer sign-off
```

**Output:** Drill run log (audit-ready, repo-ready)

---

## Quality Standards

A "good" drill execution using this pack exhibits:

### Evidence-First ✅
- Every claim has a pointer: `file:line`, `CI check name`, `terminal output line X`
- No "probably", "should be", "looks like"

### Reproducible ✅
- Same inputs + same environment → same result
- Commands are exact (not paraphrased)
- Git SHA documented at start

### SoD-Compliant ✅
- Roles clearly assigned (no "I did everything")
- Decisions have multi-role sign-off (ORCHESTRATOR + RISK_OFFICER + CI_GUARDIAN minimum)

### Deterministic ✅
- Pass/fail criteria are objective (not subjective)
- CI checks are concrete (not "looks good")

### Audit-Ready ✅
- Outsider can understand what was done and why
- Evidence is verifiable (links work, files exist)
- Risk assessment is explicit

---

## Anti-Patterns (Avoid)

### ❌ "Trust Me"
**Bad:** "It works, trust me"  
**Good:** "PASS at docs/ops/drills/runs/DRILL_RUN_20260109_D03A_CI_POLLING.md:123"

### ❌ Vague References
**Bad:** "See logs"  
**Good:** "See terminal output block at line 45 (SHA: bd192c9e)"

### ❌ Role Confusion
**Bad:** ORCHESTRATOR does everything (evidence collection, risk assessment, writing)  
**Good:** ORCHESTRATOR coordinates; FACTS_COLLECTOR gathers evidence; RISK_OFFICER assesses

### ❌ Scope Creep
**Bad:** "I also fixed this bug in src/" (in a docs-only drill)  
**Good:** "Bug noted in findings; separate PR required (outside drill scope)"

### ❌ Magic Assumptions
**Bad:** "Assuming CI will pass"  
**Good:** "CI verified: 16/16 checks PASS (gh pr checks 633 output: line 12)"

---

## Risk Assessment

### Risk Level: LOW (for docs-only drills)

**Rationale:**
- No production code changes
- No live trading actions
- No credentials/secrets involved
- All changes are documentation

**Failure Modes:**

| Failure | Impact | Mitigation |
|---------|--------|------------|
| **Template drift** | Operators use outdated patterns | Version templates, link from central pack |
| **SoD violation** | Single role makes all decisions | Enforce role sign-off in closeout |
| **Evidence gaps** | Claims not verifiable | Mandate evidence pointers in templates |
| **Scope creep** | Code changes in docs-only drill | SCOPE_KEEPER blocks; RISK_OFFICER reviews |

---

## Validation (Local)

Before committing drill pack artifacts:

```bash
# Pre-Flight
cd /Users/frnkhrz/Peak_Trade || cd "$(git rev-parse --show-toplevel)"
pwd
git status -sb

# Verify docs-reference-targets
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main

# Verify lint (if markdown files changed)
uv run ruff check docs/

# Check for broken links (if new files added)
# (Manual: click links in templates, verify they resolve)

# Git check
git diff --name-only | grep -E '^(src/|config/|tests/)' && echo "ERROR: Non-docs changes detected" || echo "OK: docs-only"
```

---

## References

**Drill Packs:**
- [OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md) — D01-D08 drills + M01 meta-drill

**Session Template:**
- [SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md](SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md) — Freeform session notes

**Runbooks:**
- [RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](../runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md) — Multi-agent workflow
- [RUNBOOK_CI_STATUS_POLLING_HOWTO.md](../runbooks/RUNBOOK_CI_STATUS_POLLING_HOWTO.md) — D03A method (CI polling)

**Evidence:**
- [DRILL_RUN_20260109_D03A_CI_POLLING.md](runs/DRILL_RUN_20260109_D03A_CI_POLLING.md) — Example of complete drill execution

---

## Change Log

- **2026-01-09 (v1.0):** Initial release (M01, D01, D02, D03A templates)
