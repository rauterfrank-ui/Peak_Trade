## Summary
Extends the Cursor Multi-Agent Runbook with structured phase runner prompt packs and operator guidance.

## Why
- Standardize operator execution of repeatable phases (0–3) with copy/paste-safe packs.
- Reduce drift across agent runs by pinning protocol + verification commands.

## What changed
- Added/expanded appendix with Phase Runner Prompt Packs (Phase 0–3).
- Clarified entry points, protocol invariants, and verification commands for docs-only runs.
- Improved maintainability section to guide future updates.

## Verification
**Foundation**
- Docs build/render sanity: open file locally; ensure headings/anchors are consistent.
- `bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main` (if docs links/targets touched)

**Governance**
- Policy Critic gates expected green (docs-only; no policy-triggering enable patterns).
- Ensure any live-adjacent guidance remains "manual-only / bounded / shadow".

**Shadow**
- N/A (docs-only). Confirm guidance does not imply autonomous live execution.

## Risk
Low.
- Documentation only.
- Operational benefit: reduces execution ambiguity.

## Operator notes
- Prefer the appendix packs as the single source of truth for phase execution.
- Keep "Pre-Flight" invariant blocks consistent across phases.

## Rollback
Revert PR commit(s) if the runbook structure causes confusion or breaks doc gates.
