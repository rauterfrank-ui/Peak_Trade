# PR #240 — Merge Log

**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/240  
**Title:** test(ops): add run_helpers adoption guard  
**Author:** @rauterfrank-ui  
**Merged:** 2025-12-21T21:20:31Z  
**Merge Commit:** be6ac71f8d5ce491592ef4789d73b0d7d7773c17

---

## Summary
- Added an adoption guard to prevent drift: key ops scripts must reference `run_helpers.sh`.
- Delivered both a runnable guard script and a fast pytest regression check.

## Why
- Ensures strict/robust ops standards stay consistent over time.
- Catches accidental removals of `run_helpers.sh` integration early in CI.

## Changes
- **Added**
  - `scripts/ops/check_run_helpers_adoption.sh` — strict/warn/all-ops modes
  - `tests/ops/test_ops_run_helpers_adoption_guard.py` — tiny, deterministic regression test

## Verification
- **CI:** all checks green (health gate, audit, lint, tests, strategy-smoke).
- **Post-merge sanity:**
  - `scripts/ops/check_run_helpers_adoption.sh`
  - `python3 -m pytest -q tests&#47;ops&#47;test_ops_run_helpers_adoption_guard.py`

## Risk
- 🟢 **Low** — adds guardrails only; no trading/core runtime changes.

## Operator How-To
- Run strict check: `scripts/ops/check_run_helpers_adoption.sh`
- Warn only: `scripts&#47;ops&#47;check_run_helpers_adoption.sh --warn-only`
- Scan all ops scripts: `scripts&#47;ops&#47;check_run_helpers_adoption.sh --all-ops`

## References
- PR #240: https://github.com/rauterfrank-ui/Peak_Trade/pull/240
