# APPENDIX C — PR TEMPLATE (Milestone 2)

## Usage
Verwende dieses Template, um eine PR für Milestone 2 zu erstellen.

---

# feat(ai): 4B M2 cursor multi-agent workflow

## Objective
Implement **4B Milestone 2: Cursor Multi-Agent Workflow Integration** for Peak_Trade.

## Scope
- Worktree-based workflow setup (`~/.cursor-worktrees/Peak_Trade/4b-m2`)
- Multi-agent chat session structure (roles, communication protocol)
- Session artifacts (logs, taskboards, decision records)
- Local gates enforcement (ruff, pytest, audit)

## Changed Files
<!-- Auto-generated or manual list -->
- `scripts/ops/setup_worktree_4b_m2.sh`
- `docs/ops/sessions/SESSION_4B_M2_20260109.md`
- `docs/ops/sessions/SESSION_4B_M2_TASKBOARD.md`
- `docs/ops/sessions/SESSION_4B_M2_DECISIONS.md`
- `docs/ops/sessions/APPENDIX_A_SYSTEM_PROMPT.md`
- `docs/ops/sessions/APPENDIX_B_TASKBOARD_TEMPLATE.md`
- `docs/ops/sessions/APPENDIX_C_PR_TEMPLATE.md`
- [weitere Dateien hier]

## Tests Executed
<!-- Document which tests ran and their results -->
```bash
# Lint Gate
ruff format --check
ruff check

# Test Gate (targeted)
pytest -q tests/[specific_module]

# Audit Gate
pip-audit  # or: uv pip-audit
```

**Results:**
- Lint: ✅ PASS / ❌ FAIL (with details)
- Tests: ✅ PASS / ❌ FAIL (with details)
- Audit: ✅ PASS / ⚠️ FINDINGS (with remediation plan)

## Verification Note
<!-- Local verification snippet -->
```bash
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2
git status -sb
ruff format --check
ruff check
pytest -q tests/[module]
```

**Status:**
- Branch: `feat/4b-m2-cursor-multi-agent`
- Base: `origin/main` (commit: 340dd29c)
- Worktree: clean, no uncommitted changes
- Gates: [summary]

## Risk Note
<!-- Document any risks, open questions, follow-ups -->
- **Risk:** [description]
  - **Mitigation:** [action taken or planned]
- **Open Question:** [question]
  - **Owner:** [who will resolve]
- **Follow-up:** [ticket/issue link]

## Definition of Done (Checklist)
- [ ] All P0 tasks from taskboard completed
- [ ] Lint gate: `ruff format --check` + `ruff check` → PASS
- [ ] Test gate: `pytest -q` (targeted) → PASS
- [ ] Audit gate: documented (PASS or remediation plan)
- [ ] Docs gate: no broken links, no accidental path-like strings
- [ ] Session log updated
- [ ] Decisions logged
- [ ] PR description complete (this template)
- [ ] Ready for review

## Merge Criteria
- ✅ CI passes (all required checks green)
- ✅ Code review approved (1+ approver)
- ✅ No unresolved comments
- ✅ Docs updated (if behavior changed)
- ✅ Merge log entry prepared (if required)

## Reviewer Notes
<!-- Guidance for reviewers -->
- Focus: Workflow structure, session artifacts, gate enforcement
- Key files: `setup_worktree_4b_m2.sh`, session docs
- Test coverage: [describe test strategy]
- Governance: No high-risk paths touched (no live trading, no execution changes)

---

**PR Author:** Frank (Operator)  
**Session Date:** 2026-01-09  
**Milestone:** 4B M2
