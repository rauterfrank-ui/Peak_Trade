# PR 1059 — MERGE LOG

## Summary
Merged PR #1059: Ops merge scripts — robust approval gating (do not rely on `reviewDecision`; use review states + exact `APPROVED` comment fallback).

## Why
Prevent false-negative approvals when `reviewDecision` is empty/unstable; keep CHANGES_REQUESTED fail-fast semantics.

## Changes
- Updates ops merge scripts approval gate:
  - approval_ok if any review state == APPROVED OR exact comment body == "APPROVED"
  - fail-fast if any review state == CHANGES_REQUESTED
- Updates dryrun workflow docs update script as needed.

## Verification
- Syntax: `bash -n` PASS (reported).
- (Optional) operator spot-check: run scripts in snapshot-only mode against a known PR.

## Risk
Low. Ops-only changes; improves merge safety.

## Operator How-To
- Sanity:
  - `bash -n scripts/ops/merge_both_prs.sh`
  - `bash -n scripts/ops/review_and_merge_pr.sh`
  - `bash -n scripts/ops/update_merge_dryrun_workflow_docs.sh`

## References
- PR: #1059
- Merge commit: `28120fca4bb2dfc0ea118e28ce610a34bc75f14d`
- Merged at: `2026-01-28T18:12:58Z`
