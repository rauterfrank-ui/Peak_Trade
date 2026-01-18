# PR #789 — MERGE LOG

## Summary
Indexed the orchestrator “next tasks” runbook in `docs/ops/runbooks/README.md` for discoverability.

## Why
Make the runbook discoverable from the canonical runbooks index (operator frontdoor), without changing runtime behavior.

## Changes
- Added a single index entry in `docs&#47;ops&#47;runbooks&#47;README.md` pointing to:
  - `RUNBOOK_CURSOR_MULTI_AGENT_ORCHESTRATOR_NEXT_TASKS_2026-01-18.md`

## Verification
- CI for PR #789: PASS (Docs gates, lint/tests matrix, audit, health, bugbot; expected skips ok).
- Local hygiene (optional): `python3 scripts&#47;ops&#47;check_merge_log_hygiene.py docs&#47;ops&#47;merge_logs&#47;PR_789_MERGE_LOG.md`

## Risk
LOW (docs-only, additive, NO-LIVE unaffected).

## Operator How-To
- Open runbooks index: `docs&#47;ops&#47;runbooks&#47;README.md`
- Navigate to the new entry and open the runbook.

## References
- PR #789: https://github.com/rauterfrank-ui/Peak_Trade/pull/789
