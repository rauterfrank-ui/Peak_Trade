# PR #738 — Merge Log

## Summary
- Added watch-only “Start→Finish” operator runbook for Dashboard observation (read-only).
- Added local docs gates snapshot (changed-scope) cursor multi-agent runbook.
- Added pointer runbook for stale-branch hygiene “local gone”.
- Linked runbooks in runbook index and workflow frontdoor / dashboard overview.
- Remediated docs-token-policy illustrative path tokens (encode `/` as `&#47;`) to keep gates green.

## Why
- Provide a deterministic, operator-grade dashboard observation workflow aligned with existing runbook patterns.
- Ensure docs-only changes remain gate-compliant (token policy + reference targets + diff-guard).

## Changes
- Updated: `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md`
- Updated: `docs/ops/runbooks/README.md`
- New: `docs/ops/runbooks/RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md`
- New: `docs/ops/runbooks/RUNBOOK_OPERATOR_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md`
- New: `docs/ops/runbooks/RUNBOOK_STALE_BRANCH_HYGIENE_LOCAL_GONE_CURSOR_MULTI_AGENT.md`
- New/Updated: `docs/webui/DASHBOARD_OVERVIEW.md`

## Verification
CI (PR #738):
- Docs Token Policy Gate: PASS
- Docs Reference Targets Gate: PASS
- Docs Diff Guard Policy Gate: PASS
- Audit + core CI suites: PASS (docs-only scope; health checks skipped where path-filtered)
Local:
- `scripts/ops/pt_docs_gates_snapshot.sh --changed` → PASS

## Risk
LOW
- Documentation-only; dashboard is explicitly watch-only/read-only; no execution/governance codepaths changed.

## Operator How-To
- Entry: `docs/webui/DASHBOARD_OVERVIEW.md` → follow watch-only runbook for start commands + verification URLs.
- For deterministic evidence: use the runbook’s snapshot export commands.
- If token policy trips on illustrative paths: encode `/` inside inline-code as `&#47;`.

## References
- PR #738 (dashboard watch-only operator runbook)
- Runbooks index: `docs/ops/runbooks/README.md`
- Dashboard overview: `docs/webui/DASHBOARD_OVERVIEW.md`
- Workflow frontdoor: `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md`
