# Release Note — 2026-01-13 — Runbooks Frontdoor Reintegration

## Scope
Docs-only post-merge hygiene for runbooks & incident handling navigation and evidence linkage.

## What shipped (already live on main)
- Runbooks & incident handling is reachable from three frontdoors:
  - docs/README.md
  - docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md
  - WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md
- Evidence entry recorded:
  - EV-20260113-RUNBOOKS-FRONTDOOR (docs/ops/EVIDENCE_INDEX.md)

## PR chain (reference)
- PR #706 — Navigation integration (commit 2243cfac)
- PR #707 — Evidence index entry (commit 54174fb1)

## Verification
- Token Policy Gate: PASS
- Reference Targets Gate: PASS
- Diff Guard Policy Gate: PASS
- CI: 28/28 successful (at time of merge)

## Follow-ups in this PR
- Add stable crosslink from PR_706_MERGE_LOG → EV entry anchor
- Generate docs graph snapshot + orphan check artifacts (Phase 8 tooling)

## Risk
LOW (docs-only). No runtime code paths affected.

## Rollback
Revert this PR (docs-only); no data migrations required.
