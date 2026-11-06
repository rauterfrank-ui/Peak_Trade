# PR #235 — MERGE LOG (kompakt)

**PR:** #235 — fix(ops): improve label_merge_log_prs.sh to find open PRs  
**Status:** MERGED (squash)  
**Datum:** 2025-12-21  
**Scope:** Ops / Scripts

## Summary
- `label_merge_log_prs.sh` erweitert, damit offene PRs ebenfalls gefunden werden.

## Why
- Vorher wurden nur closed PRs erfasst → offene Merge-Log PRs sind durchgerutscht.
- Ziel: vollständige Abdeckung in Bulk-Labeling Runs.

## Changes
- PR Query: `--state closed` → `--state all`
- Regex erweitert: `add` → `(?:add|align|update)` (mehr Titel-Varianten)
- Ergebnis: 31 → 35 PRs gefunden (inkl. 3 offene)

## Verification
- CI: audit ✅, lint ✅, tests ✅, strategy-smoke ✅
- Lokal: optional `bash -n scripts/ops/label_merge_log_prs.sh` + kurzer Dry-Run

## Risk
🟢 **Low** — Ops-Skriptverhalten, keine Core-Änderungen.

## Operator How-To
- `bash scripts/ops/label_merge_log_prs.sh`

## References
- PR #235 (GitHub)
- Script: `scripts/ops/label_merge_log_prs.sh`
