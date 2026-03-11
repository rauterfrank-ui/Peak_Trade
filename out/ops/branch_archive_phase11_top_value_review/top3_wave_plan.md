# Top 3 Implementation Wave Plan — Phase 11

**Stand:** 2026-03-10  
**Mode:** Implementation prep only; no execution

---

## Wave 21: High-Value Salvage (SALVAGE_NOW)

### Goal
Salvage the 6 branches classified SALVAGE_NOW with highest confidence and lowest conflict risk.

### Target Branches
1. recover/p22-roadmap-runbook-merge (governance)
2. recover/p99-launchd-hard-guardrails-v1 (launchd)
3. recover/p28-backtest-loop-positions-cash-v1 (backtest)
4. recover/p29-accounting-v2-avgcost-realizedpnl (accounting)
5. recover/p111-execution-adapter-selector-v1 (execution)
6. recover/ops-launchd-supervisor-subcommands-v1 (supervisor)

### Likely Touched Areas
- docs/roadmap/, docs/analysis/p99/
- src/backtest/p28/, src/backtest/p29/
- src/execution/adapters/
- scripts/ops/ (supervisor, launchd)
- tests/p28/, tests/p29/, tests/p88/, tests/p111/

### Safety Gates
- No live execution changes
- Run tests before/after each salvage
- Conflict assessment per branch
- docs&#47;GOVERNANCE_DATAFLOW_REPORT.md, docs&#47;REPO_AUDIT_REPORT.md untouched

### Expected Validations
- `pytest tests&#47;p28 tests&#47;p29 tests&#47;p88 tests&#47;p111 -q`
- No new lint/type errors
- Merge conflict resolution documented

### Go/No-Go
- **Go:** Operator approves; no governance locks
- **No-Go:** Conflicts, test failures, or governance risk

---

## Wave 22: Workbook + Verify (SALVAGE_LATER)

### Goal
Resolve p101 intent (deletions) and salvage if appropriate.

### Target Branches
1. recover/p101-workbook-checklists-stop-playbook-v1

### Likely Touched Areas
- scripts/ops/p101_stop_playbook_v1.sh

### Safety Gates
- Verify whether deletions are intentional or stale
- Compare with main's current p101 script
- No speculative changes

### Expected Validations
- Diff review
- Operator sign-off on intent

### Go/No-Go
- **Go:** Intent clear; salvage adds value
- **No-Go:** Unclear; defer to manual review

---

## Wave 23: Manual Deep Review (MANUAL_DEEP_REVIEW)

### Goal
Manual diff review of salvage-wip branches; selective salvage or archive.

### Target Branches
1. wip/salvage-code-tests-untracked-20251224_082521
2. wip/untracked-salvage-20251224_081737

### Likely Touched Areas
- src/strategies/, tests/ (first)
- docs/, scripts/, src/, tests/ (second — broad)

### Safety Gates
- Full diff vs main before any action
- Overlap analysis with existing main content
- Rescue remote verification

### Expected Validations
- Overlap % with main
- Unique content inventory
- Test coverage delta

### Go/No-Go
- **Go:** Operator approves selective salvage
- **No-Go:** High overlap; archive after evidence
