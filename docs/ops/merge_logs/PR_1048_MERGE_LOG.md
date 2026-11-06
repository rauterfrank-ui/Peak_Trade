# PR 1048 — MERGE LOG

## Summary
PR #1048 wurde als squash gemerged; Branch gelöscht; guarded merge via `--match-head-commit` eingehalten.

## Why
Test-Suite soll die dokumentierte `prepare_once()` Semantik hart absichern: Cache-Key ist `id(data)` (Objektidentität).

## Changes
- tests&#47;strategies&#47;test_prepare_once.py
  - Ergänzt/gehärtet: `df.copy(deep=True)` (neues Objekt) triggert erneut `prepare()` (id(data)-Semantik)

## Verification
- PR Checks: alle relevanten Checks PASS (inkl. Tests-Matrix)

## Merge Evidence
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1048
- state: MERGED
- mergedAt: 2026-01-28T10:09:46Z
- mergeCommit: ed206d1a7377d796759e5fc9ed6de8e5a4df7d21
- approval_exact_comment_id: 3810292265

## Risk
Low (Test-only).

## Operator How-To
- Keine Operator-Aktion notwendig.

## References
- PR #1048
