# Drill Run Logs — AI Autonomy 4B Milestone 2

**Purpose:** Central registry and guidelines for drill session documentation  
**Audience:** Operators executing drills from OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md  
**Last Updated:** 2026-01-09

---

## Purpose of Drill Run Logs

Drill run logs serve multiple purposes:

1. **Evidence Trail:** Provide audit-grade documentation of operator competency validation
2. **Reproducibility:** Enable future operators to understand what was tested and how
3. **Learning:** Capture findings, failure modes, and fixes for knowledge sharing
4. **Governance:** Demonstrate SoD (Separation of Duties) enforcement and no-live compliance
5. **Continuous Improvement:** Identify drill gaps, ambiguities, or areas for refinement

**Not for:**
- Production run logs (see separate production logging)
- General troubleshooting notes (use incident logs)
- Code review documentation (use PR merge logs)

---

## Naming Convention

**Format:** `DRILL_RUN_YYYYMMDD_HHMM_<operator_id>_<drill_id>.md`

**Components:**
- `DRILL_RUN_` — Fixed prefix for easy grep/search
- `YYYYMMDD` — Date in ISO format (e.g., 20260109)
- `HHMM` — Time in 24h format (e.g., 1930 for 7:30 PM)
- `<operator_id>` — Operator identifier (e.g., `ai_autonomy`, `frank`, `ops_team`)
- `<drill_id>` — Drill identifier from pack (e.g., `D01`, `D02`, `D08`)

**Examples:**
- `DRILL_RUN_20260109_1930_ai_autonomy_D01.md` — AI agent ran D01 on Jan 9, 2026 at 19:30
- `DRILL_RUN_20260110_0800_frank_D02.md` — Operator Frank ran D02 on Jan 10, 2026 at 08:00 (file not created)
- `DRILL_RUN_20260115_1500_ops_team_D08.md` — Ops team ran D08 on Jan 15, 2026 at 15:00

**Storage Location:**
- Primary: `docs&#47;ops&#47;drills&#47;runs&#47;` (this directory)
- Optional: Operator-specific subdirectories if volume grows (e.g., `docs&#47;ops&#47;drills&#47;runs&#47;ai_autonomy&#47;`)

---

## What "Good" Looks Like

A high-quality drill run log exhibits these characteristics:

### Evidence-First
- ✅ Every claim backed by a specific file path, line number, terminal output, or CI check result
- ✅ Evidence pointers are precise: `path&#47;to&#47;file.md:123` not "somewhere in the docs"
- ❌ Avoid: "Probably correct", "Should be", "Looks like"

### Reproducible
- ✅ Step-by-step procedure with exact commands
- ✅ Git SHA documented at session start
- ✅ Tool versions documented (if relevant)
- ✅ Environment documented (OS, shell, branch)
- ❌ Avoid: "I ran some commands and it worked"

### Concise but Complete
- ✅ Execution log captures all steps (including failures)
- ✅ Scorecard shows pass/fail for each criterion
- ✅ Findings are actionable (not just observations)
- ❌ Avoid: Multi-page prose with no structure

### SoD Enforced
- ✅ Roles clearly assigned (ORCHESTRATOR, FACTS_COLLECTOR, etc.)
- ✅ No single role making all decisions (separation maintained)
- ❌ Avoid: "I did everything" or no role attribution

### Deterministic
- ✅ Pass/Fail criteria are objective (not subjective)
- ✅ Same inputs + same environment → same result
- ❌ Avoid: "It felt right" or "Looks good to me"

### Timebox Respected
- ✅ Execution time documented vs. timebox
- ✅ If exceeded: reason documented + stop condition noted
- ❌ Avoid: Open-ended drill sessions with no time tracking

### Governance Compliant
- ✅ Docs-only scope maintained (if applicable)
- ✅ No-live enforcement verified
- ✅ Risk officer review included
- ❌ Avoid: Scope creep (code changes in a docs-only drill)

---

## Template Usage

**Recommended Workflow:**

1. **Before Session:**
   - Copy `SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md` to this directory
   - Rename following naming convention (see above)
   - Fill in Session Metadata section

2. **During Session:**
   - Update Execution Log in real-time (or immediately after each step)
   - Capture terminal outputs, screenshots, CI links as you go
   - Note any deviations from drill procedure

3. **After Session:**
   - Complete Scorecard (pass/fail per criterion)
   - Document Findings & Operator Actions
   - Get Risk Officer sign-off (even if same person, note the role switch)
   - Save file to `docs&#47;ops&#47;drills&#47;runs&#47;`

4. **Optional: Commit to Repo**
   - If drill run is significant or reveals important findings, commit via docs-only PR
   - Link from this README (see "Session Index" below)
   - Label PR: `documentation`, `ops&#47;drill-run`

---

## Session Index (Optional)

If drill runs are committed to the repo, maintain a simple index here:

### 2026-01-09
- [DRILL_RUN_20260109_1930_ai_autonomy_D01.md](DRILL_RUN_20260109_1930_ai_autonomy_D01.md) — Pre-Flight Discipline (PASS)

### 2026-01-10
- `DRILL_RUN_20260110_0800_frank_D02.md` — Scope Lock Verification (PASS) (file not created)

*(Add entries as drill runs are committed)*

---

## Common Patterns & Anti-Patterns

### Pattern: Evidence Pointer Table

Good drill runs use a structured table for evidence:

| ID | Type | Location | Note |
|----|------|----------|------|
| E01 | Terminal Output | Step 1 output | Repository root verified |
| E02 | File Reference | docs/ops/README.md:72 | Link to drill pack |
| E03 | CI Check | GitHub Actions run #12345 | Lint gate passed |

### Anti-Pattern: Vague References

Avoid:
- "See logs" (which logs? where?)
- "As mentioned earlier" (where earlier? line number?)
- "The file" (which file? full path?)

### Pattern: Reproducible Commands

Good drill runs show exact commands with context:

```bash
# Context: on main branch, clean working tree
cd /Users/frnkhrz/Peak_Trade
git status -sb
# Output: ## main...origin/main (clean)
```

### Anti-Pattern: Missing Context

Avoid:
- `git status` (which directory? which branch?)
- `pytest` (which tests? which environment?)

---

## Drill Run Lifecycle

```
┌─────────────────────┐
│ Select Drill from   │
│ OPERATOR_DRILL_PACK │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Copy Template       │
│ Fill Metadata       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Execute Drill Steps │
│ (Log in real-time)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Complete Scorecard  │
│ Document Findings   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Risk Officer Review │
│ Sign-Off            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Save to runs/       │
│ (Optional: Commit)  │
└─────────────────────┘
```

---

## Quality Checklist

Before considering a drill run log "complete", verify:

- [ ] Session Metadata filled (date, drill ID, operator, roles)
- [ ] Run Manifest includes objective, preconditions, pass/fail criteria
- [ ] Execution Log has all steps with commands, observations, evidence pointers
- [ ] Evidence Pointers table populated (or inline references clear)
- [ ] Scorecard shows pass/fail for each criterion with evidence
- [ ] Findings are reproducible (steps to reproduce documented)
- [ ] Operator Actions are concrete (commands or steps provided)
- [ ] Risk Officer Review completed (sign-off or assessment)
- [ ] References section points to drill source, runbook, template
- [ ] File named per convention: `DRILL_RUN_YYYYMMDD_HHMM_<operator>_<drill>.md`

---

## Related Documentation

**Drill Pack:**
- [OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](../OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md) — Source of drills D01-D08

**Template:**
- [SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md](../SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md) — Reusable template for drill sessions

**Runbook:**
- [RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](../../runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md) — Operator workflow for M2

**Ops Index:**
- [docs/ops/README.md](../../README.md) — Central ops documentation hub

---

## Change Log

- **2026-01-09 (v1.0):** Initial README creation (naming convention, quality guidelines, lifecycle)
