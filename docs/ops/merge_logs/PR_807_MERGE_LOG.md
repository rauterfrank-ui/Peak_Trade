# PR 807 — Merge Log

## Summary

docs(ops): add repo-root legacy docs archive (additive)

## Why

Preserve legacy repo-root documents as a linkable, governance-safe archive under docs/ops/archives/repo_root_docs/ (docs-only, additive, NO-LIVE).

## Changes

- Add: docs/ops/archives/repo_root_docs/** (+ `README.md` index)
- Update (docs-only): ops documentation navigation/templates/index entries to reflect the archive integration
- Add: evidence entry `docs/ops/evidence/EV_ARCHIVE_IMPORT_20260118T204239Z.md`

## Verification

- Local snapshot: `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` → PASS
- CI: required contexts PASS (snapshot); mergeStateStatus=CLEAN at merge time

## Risk

LOW (docs-only, additive, NO-LIVE)

## Merge Data

- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/807
- mergedAt: 2026-01-18T20:58:40Z
- mergeCommit: bf024942b142e1fb9bcfd0d05a504d5159c36da3
- headRefName: docs/a0-archive-salvage-20260118
- headRefOid: 517f33a3384a7913a09f03e65e3fced7d6eb66b2
