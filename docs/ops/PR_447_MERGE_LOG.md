# PR #447 — Deprecate historical `inspect_offline_feed` references (Phase 2)

## Summary
Docs-only hardening for historical references to `scripts/inspect_offline_feed.py` by adding explicit DEPRECATED notices while preserving historical context.

## Why
The referenced script was removed from the repository. Historical "FINAL_REPORT" documents still referenced it, which could mislead operators and also interact poorly with strict docs target validation.

## Changes
- Added consistent DEPRECATED callouts near historical mentions of the removed script:
  - Blockquote notice near the first mention in each document.
  - Inline DEPRECATED markers for command and file-list references.
- Preserved historical references (no deletion), with explicit "do not use for current workflows" guidance.

## Verification
- `rg -n "scripts/inspect_offline_feed\.py" -S docs` used to identify occurrences and confirm coverage.
- Docs-only change set; CI gates green in stack order.

## Risk
Minimal. Documentation-only; no operational behavior changes.

## Operator How-To
- Treat `inspect_offline_feed` references as historical context only.
- Use current runbooks and workflows for offline feed inspection; do not rely on removed legacy scripts.

## References
- PR #447
- Base: PR #446
- Follow-up: PR #448 (de-pathification/false-positive hardening)
