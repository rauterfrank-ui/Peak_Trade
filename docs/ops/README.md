# Test README
<!-- MERGE_LOG_EXAMPLES:START -->
- PR #281 — Test PR 281: docs/ops/PR_281_MERGE_LOG.md
<!-- MERGE_LOG_EXAMPLES:END -->

## PR Ops v1

Standardized PR watch, closeout, and required-checks snapshot helpers. See [PR Ops v1 Runbook](pr/pr_ops_v1_runbook.md).

### PR Ops v1 (canonical)
- Entry-point: `scripts&#47;ops&#47;pr_ops_v1.sh <PR_NUM>`
- Runbook: `docs&#47;ops&#47;pr&#47;pr_ops_v1_runbook.md`

## PR Inventory
- See: scripts/ops/pr_inventory_full.sh
- Keyword: pr_inventory. Use **label** (e.g. ops/inventory) for filtering.

## Docs Diff Guard (auto beim Merge)

Beim `--merge` läuft standardmäßig automatisch ein **Docs Diff Guard**, der große versehentliche Löschungen in `docs&#47;*` erkennt und **den Merge blockiert**.

### Override-Optionen
```bash
# Custom Threshold (z.B. bei beabsichtigter Restrukturierung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-threshold 500

# Warn-only (kein Fail, nur Warnung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-warn-only

# Guard komplett überspringen (NOT RECOMMENDED)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --skip-docs-guard
```

**Siehe auch:**
- Vollständige Dokumentation: `docs/ops/README.md` (Abschnitt "Docs Diff Guard")
- PR Management Toolkit: `docs/ops/PR_MANAGEMENT_TOOLKIT.md`
- Standalone Script: `scripts/ops/docs_diff_guard.sh`
- Merge-Log: `docs/ops/PR_311_MERGE_LOG.md`
