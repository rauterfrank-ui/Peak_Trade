# Top Value Candidates — Phase 8 Review

**Stand:** 2026-03-10

## Top 10 by Likely Value (Conservative)

| Rank | Branch | Theme | Rationale |
|------|--------|-------|------------|
| 1 | recover/p101-workbook-checklists-stop-playbook-v1 | workbook | Explicit KEEP; workbook checklists, stop playbook — high ops value |
| 2 | recover/p22-roadmap-runbook-merge | governance | Explicit KEEP; roadmap runbook merge — governance alignment |
| 3 | recover/p80-supervisor-stop-idempotent-v1 | supervisor | Explicit KEEP; 2 ahead; supervisor stop idempotent — safety |
| 4 | recover/p99-launchd-hard-guardrails-v1 | launchd | Explicit KEEP; launchd guardrails — safety |
| 5 | recover/p28-backtest-loop-positions-cash-v1 | backtest | High value; backtest loop positions/cash — accounting core |
| 6 | recover/p29-accounting-v2-avgcost-realizedpnl | accounting | High value; avg cost, realized PnL — reporting core |
| 7 | wip/salvage-code-tests-untracked-20251224_082521 | salvage | Rescue remote exists; code tests — possible test coverage |
| 8 | wip/untracked-salvage-20251224_081737 | salvage | Rescue remote exists; untracked salvage — possible unique content |
| 9 | recover/p111-execution-adapter-selector-v1 | execution | Adapter selector — execution routing |
| 10 | recover/ops-launchd-supervisor-subcommands-v1 | supervisor | Supervisor subcommands — ops tooling |

## Groups by Action Bucket

### KEEP_FOR_FUTURE_IMPL (4)
- recover/p101-workbook-checklists-stop-playbook-v1
- recover/p22-roadmap-runbook-merge
- recover/p80-supervisor-stop-idempotent-v1
- recover/p99-launchd-hard-guardrails-v1

### MANUAL_DEEP_REVIEW_NEXT (9)
- recover/ops_pr-drill-20260211T070830Z
- recover/p13-kickoff
- recover/stash-2
- recover/stash-3
- wip/pausepoint-branch-cleanup-recovery-20260124T133039Z
- wip/restore-stash-after-pr432
- wip/restore-stash-operator-pack
- wip/salvage-code-tests-untracked-20251224_082521
- wip/untracked-salvage-20251224_081737

### ARCHIVE_REVIEW_NEXT (32)
- All recover execution-networked p122–p132 (8)
- All recover supervisor/launchd except p80, p99-launchd-hard (6)
- recover p27, p28, p29, p33, p51, p54, p64–p66, p75, p81, p87, p88, p92, p94, p97, p98, p99-guarded-plist
- recover fix-p76, p105-*, p118, pr-ops, pr-trigger
- tmp/docs-runbook-to-finish-clean

### DISPOSAL_CANDIDATE_NEEDS_PROOF (18)
- wip/local-uncommitted-20260128
- wip/local-unrelated-20260127-205436
- wip/salvage-dirty-main-20260118
- backup/* (9)
- tmp/stack-test
