# PR #446 — Script path reference remediation (Phase 1)

## Summary
Docs-only remediation of stale script path references after repository script relocations, plus normalization of directory references used in documentation.

## Why
The docs-reference-targets gate requires documentation references to point to real, repo-existing targets. A set of legacy script paths and directory references had drifted due to prior refactors/moves.

## Changes
- Updated documentation references for moved scripts (examples):
  - `scripts/validate_git_state.sh` → `scripts/ci/validate_git_state.sh`
  - `scripts/post_merge_workflow_pr203.sh` → `scripts/workflows/post_merge_workflow_pr203.sh`
  - Additional workflow/util/automation scripts updated to their current locations (mechanical path replacements).
- Normalized directory references where documentation intent is "package/directory":
  - Added trailing slash for directory references (e.g., `src/data/safety/` and related `src/data/*` directories where applicable).

## Verification
- On main:
  - `rg -n "scripts/validate_git_state\.sh" -S docs` returned 0 matches.
  - `rg -n "scripts/post_merge_workflow_pr203\.sh" -S docs` returned 0 matches.
- CI gates: docs-reference-targets gate succeeded; docs-only diff.

## Risk
Minimal. Documentation-only, mechanical replacements, no code-path impact.

## Operator How-To
- When referencing scripts in docs/runbooks, always use the current repo location under:
  - `scripts/ci/`, `scripts/workflows/`, `scripts/utils/`, `scripts/automation/` (as applicable)
- Prefer directory references with trailing slash when the intent is "the package/folder", and use specific file paths only when semantically required.

## References
- PR #446
- Follow-ups: PR #447 (deprecated notices), PR #448 (gate false-positive hardening)
