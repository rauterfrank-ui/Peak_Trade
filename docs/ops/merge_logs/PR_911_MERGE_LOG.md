# PR #911 — MERGE LOG (docs-only)

## Summary
Merged PR #911 (squash) introducing repo-wide label governance docs: decision list, audit report framing, hard-refs separation, taxonomy notes, and an updated governance runbook that splits refs scanning into **broad vs operational** and documents that **Issues are disabled**.

## Why
- Make label governance deterministic and auditable (snapshot artifacts + decision rules).
- Prevent accidental label renames/deletes when operational hard-refs exist.
- Clarify repo reality: relabeling applies to PRs only; Issues are disabled.

## Changes
- Added/updated label governance docs:
  - `docs/ops/labels/LABEL_DECISION.md`
  - `docs/ops/labels/LABEL_AUDIT_REPORT.md`
  - `docs/ops/labels/LABEL_HARD_REFS.md`
  - `docs/ops/labels/LABEL_TAXONOMY.md`
- Updated runbook:
  - `docs/ops/runbooks/RUNBOOK_LABEL_GOVERNANCE.md` (refs scan split: `labels_refs_broad.txt` vs `labels_refs_operational.txt`; Issues disabled note; PR-only relabel example as Operator-only)

## Verification
- GitHub merge gate satisfied via exact approval comment:
  - `approval_exact_comment_id: 3778418992`
- Merge state at time of merge: `mergeStateStatus=CLEAN`, `mergeable=MERGEABLE` (operator snapshot).
- Merge evidence:
  - PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/911
  - mergedAt: `2026-01-21T14:28:49Z`
  - mergeCommit: `e1c4441f2f452250399129a6802bbe63b68f7653`

## Risk
LOW — documentation only; no GitHub label edits/renames/deletes performed.

## Operator How-To
- Audit artifacts (local, deterministic):
  - `tmp/labels.json`
  - `tmp/labels_audit.tsv`
  - `tmp/labels_candidates_used0.txt`
  - `tmp/labels_refs_broad.txt` (includes docs; intentionally noisy)
  - `tmp/labels_refs_operational.txt` (only `.github/` + `scripts`; label-carrying patterns)
- Decision rules and current decisions: see `docs/ops/labels/LABEL_DECISION.md`.
- Any migration/relabel/rename/delete remains **Operator-only** per runbook.

## References
- PR #911: https://github.com/rauterfrank-ui/Peak_Trade/pull/911
- Merge commit: `e1c4441f2f452250399129a6802bbe63b68f7653`
- Approval comment id: `3778418992`
