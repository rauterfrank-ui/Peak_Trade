# PR #488 — docs(ops): standardize bg_job execution pattern in cursor phases runbook

## Summary
Standardizes the bg_job runner as operator tooling in the Cursor Multi-Agent workflow by adding dedicated sections to the Frontdoor, Phases V2, and Live Execution Roadmap runbooks. Provides discovery-first guidance, operator notation standards, and troubleshooting patterns.

## Why
The bg_job runner (PR #486) addresses timeout-prone long-running tasks in multi-agent workflows (backtests, VaR suites, sweeps). Anchoring it in the standard runbooks ensures operators and agents use it consistently, with clear documentation patterns and gate-safe reference formats.

## Changes
- `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md`: Added Appendix B.3 with bg_job discovery command and gate-safety hint; added operator tooling reference in Section 9.
- `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md`: Added Section 7 "bg_job Execution Pattern (Standard)" with when-to-use criteria, discovery-first commands, operator-notizen template, troubleshooting minimum, and gate-safety reminder.
- `docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md`: Added Section 6 "Toolbox: bg_job Runner" with multi-agent context and discovery command.

## Verification
Commands (local):
```bash
# Verify no raw script tokens (hard constraint)
rg -n "scripts/ops/bg_job\.sh" docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md
# Expected: Exit 1 (no matches) or only masked references

# Verify docs reference targets gate
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
# Expected: Exit 0 (PASS) or not applicable
```

CI checks:
- All pre-commit hooks passed
- No linter errors
- Docs reference targets gate: not applicable (no repo targets added)

## Risk
**None.** Docs-only change. No code, config, or execution logic modified.

## Operator How-To

### Quick access to bg_job pattern
See the standardized pattern in:
- `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md`, Section 7 (primary reference)
- `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md`, Appendix B.3 and Section 9
- `docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md`, Section 6

### Discovery-first command
Always start with:
```bash
bash 'scripts'/'ops'/'bg_job.sh' --help || bash 'scripts'/'ops'/'bg_job.sh' help
```

### When to use bg_job
Use for Multi-Agent workflow steps with:
- Long runtime (> 5 minutes)
- Timeout risk in Cursor/shell sessions
- Need for exit-code capture and log tracking

### Operator notation standard (Session Runlog)
Document each bg_job run with:
- **Zweck / Step-ID**: e.g., "WP0B Risk Suite"
- **Startzeit**: ISO format timestamp
- **Status/Logs Location**: Reference help + PR_486_MERGE_LOG.md
- **Exit-Code erwartung**: Typically 0 for success

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/488
- Parent PRs: #486 (bg_job runner implementation), #487 (initial runbook integration)
- Branch: docs/bg-job-execution-pattern
- Merged at: 2026-01-01
- Commit: 427de20, 8312cb9
