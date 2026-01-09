# APPENDIX B — TASKBOARD TEMPLATE

## Usage
Kopiere dieses Template für neue Milestones/Sessions und passe es an.

---

# [MILESTONE_NAME] — TASKBOARD

**Session:** [SESSION_ID]  
**Date:** [YYYY-MM-DD]  
**Branch:** [branch-name]  
**Worktree:** [path]

## P0 (Must — Blocking)
- [ ] Task 1: Description
  - Owner: [Agent A/B/C/D]
  - Status: [TODO/IN_PROGRESS/BLOCKED/DONE]
  - Evidence: [file/command/log]
- [ ] Task 2: Description
  - Owner: [Agent A/B/C/D]
  - Status: [TODO/IN_PROGRESS/BLOCKED/DONE]
  - Evidence: [file/command/log]

## P1 (Should — Important)
- [ ] Task 3: Description
  - Owner: [Agent A/B/C/D]
  - Status: [TODO/IN_PROGRESS/BLOCKED/DONE]
  - Evidence: [file/command/log]

## P2 (Nice — Optional)
- [ ] Task 4: Description
  - Owner: [Agent A/B/C/D]
  - Status: [TODO/IN_PROGRESS/BLOCKED/DONE]
  - Evidence: [file/command/log]

## Blocked / Needs Operator
- [ ] Task X: Description
  - Blocker: [reason]
  - Action: [what operator needs to do]

## Done (Completed)
- [x] Task Y: Description
  - Owner: [Agent A/B/C/D]
  - Completed: [YYYY-MM-DD HH:MM]
  - Evidence: [file/command/log]

---

## Review Cadence
- After each P0 task: Run minimal gates (ruff + pytest subset)
- After all P0 tasks: Run full gates + document status

## Definition of Done
- [ ] All P0 tasks completed
- [ ] Lint gate: `ruff format --check` + `ruff check` → PASS
- [ ] Test gate: `pytest -q` (targeted) → PASS
- [ ] Audit gate: Status documented (PASS or remediation plan)
- [ ] Docs gate: No broken links, no accidental path-like strings
- [ ] PR skeleton prepared (or PR created)
- [ ] Session log updated
- [ ] Decisions logged (if any)

---

## Notes
- Use this template for each new milestone/session
- Keep task descriptions short & actionable
- Update status in real-time during session
- Document evidence (file paths, commands, log snippets)
