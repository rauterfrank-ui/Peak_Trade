# PR_706_MERGE_LOG — docs(ops): reintegrate runbooks & incident handling into navigation

## Summary
Reintroduces central navigation link(s) to Runbooks & Incident Handling doc.

## Why
Ensure discoverability from frontdoor/ops indices.

## Changes
- Navigation indices updated to include `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`:
  - `docs/README.md` (+1 line): Ops/Live Trading section
  - `docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md` (+1 line): Central runbook table
  - `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` (+21 lines): Detailed section with kern-runbooks, status, related docs
- Gate-safe link hygiene (no illustrative link targets)
- Total: 3 files, +23 lines

## Verification
- docs-reference-targets-gate: PASS
- docs-token-policy-gate: PASS
- docs-diff-guard-policy-gate: PASS
- Link targets validated: 7/7 exist
- Pre-commit hooks: ALL PASS
- Repo status clean

## Risk
Low (docs-only). Runbook file itself unchanged.

## Operator How-To
Navigate via:
- `docs/README.md` → Ops / Live Trading → Runbooks & Incident Handling
- `docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md` → Central table → Runbooks & Incident Handling
- `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` → Detailed section with cross-links

## References
- PR #706: https://github.com/rauterfrank-ui/Peak_Trade/pull/706
- Branch: docs&#47;runbooks-frontdoor-reintegration
- Runbook: `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md` (Phase 25/56, unchanged)
- Previous attempt: PR #705 (closed, reverted)
- Evidence Index: [EV-20260113-RUNBOOKS-FRONTDOOR](docs/ops/EVIDENCE_INDEX.md#ev-20260113-runbooks-frontdoor)
