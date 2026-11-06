# PR #311 — feat(ops): add docs diff guard (mass-deletion protection)

## Summary

PR #311 wurde gemerged am 2025-12-25 03:42:55 UTC.  
Squash-Commit: 0f08d86 — "feat(ops): add docs diff guard (mass-deletion protection) (#311)".  
Branch: feat/ops-docs-diff-guard (auto-gelöscht)

## Why

Verhindert versehentliche Docs-Mass-Deletions (README-Massaker) durch:
- **Standalone Script** `scripts/ops/docs_diff_guard.sh` für manuelle Pre-Merge Checks
- **Automatische Integration** in `scripts/ops/review_and_merge_pr.sh` (läuft vor jedem `--merge`)

Lessons Learned aus PR #310 (-972 Deletions in `docs/ops/README.md`).

## Changes

- `scripts/ops/docs_diff_guard.sh` (neu, executable)  
  → Standalone Guard: prüft große Deletions in `docs/` via `git diff --numstat`
- `scripts/ops/review_and_merge_pr.sh` (+90)  
  → Automatische Integration: läuft vor jedem Merge (default: enabled, Threshold: 200 Deletions/File)  
  → Override-Optionen: `--skip-docs-guard`, `--docs-guard-threshold N`, `--docs-guard-warn-only`
- `docs/ops/README.md` (Dokumentation: Docs Diff Guard Abschnitt)

## Verification

### CI (alle PASS, Auto-Merge)
- ✅ tests (3.11) — 5m41s
- ✅ audit — 2m48s
- ✅ strategy-smoke — 1m12s
- ✅ Lint Gate — 8s
- ✅ Policy Critic Gate — 7s
- ✅ CI Health Gate — 1m7s
- ✅ Guard tracked files — 6s
- ✅ Render Quarto — 28s

### Lokal (Post-Merge)
```bash
# Standalone Script
scripts/ops/docs_diff_guard.sh
# ✅ OK: no large doc deletions detected.

# Review & Merge Integration
scripts/ops/review_and_merge_pr.sh --pr 999 --merge --dry-run
# → DRY-RUN: would run docs diff guard for PR #999 (threshold=200, warn_only=0)
```

## Risk

Low (Ops Scripts + Docs).

## Operator How-To

### Standalone (manuelle Pre-Merge Check)
```bash
# Standard: fail bei Violations
scripts/ops/docs_diff_guard.sh

# Custom Threshold (z.B. 500)
scripts/ops/docs_diff_guard.sh --threshold 500

# Warn-only (kein Fail)
scripts/ops/docs_diff_guard.sh --warn-only
```

### Automatisch (in review_and_merge_pr.sh integriert)
```bash
# Default: Guard läuft automatisch vor --merge
scripts/ops/review_and_merge_pr.sh --pr 123 --merge

# Override: Guard überspringen (NOT RECOMMENDED)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --skip-docs-guard

# Override: Custom Threshold
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-threshold 500

# Override: Warn-only (kein Fail, nur Warnung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-warn-only
```

## References

- PR #311: https://github.com/rauterfrank-ui/Peak_Trade/pull/311
- Commit: 0f08d86
- Lessons Learned: PR #310 (README-Massaker: -972 Deletions)
