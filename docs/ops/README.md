# Test README
<!-- MERGE_LOG_EXAMPLES:START -->
- PR #281 — Test PR 281: docs/ops/PR_281_MERGE_LOG.md
<!-- MERGE_LOG_EXAMPLES:END -->

- `docs/ops/specs/OPS_SUITE_DASHBOARD_VNEXT_SPEC.md` — OPS Suite / Dashboard vNext Spezifikation
- `docs/ops/runbooks/RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md` — Phasenplan für spätere Umsetzung
- `docs/ops/specs/PILOT_READY_EXECUTION_REVIEW_SPEC.md` — Pilot-Ready Execution Review Spezifikation
- `docs/ops/runbooks/RUNBOOK_PILOT_READY_EXECUTION_REVIEW_PLAN.md` — Phasenplan für Pilot-Ready Review/Härtung
- `docs/ops/specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md` — Kanonische Edge-Case-Matrix für Pilot-Execution-Härtung
- `docs/ops/specs/PILOT_GO_NO_GO_CHECKLIST.md` — Kanonische Go/No-Go-Checkliste für begrenzte Pilot-Freigabe
- `docs/ops/specs/RECONCILIATION_FLOW_SPEC.md` — Kanonische Reconciliation-Flow-Spezifikation für bounded pilot / execution safety
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md` — Incident-Runbook für degraded exchange/broker Verhalten
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md` — Incident-Runbook für degradierte Telemetrie / Evidenz
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md` — Incident-Runbook für Reconciliation-Mismatch
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md` — Incident-Runbook für unexpected exposure

- `docs/ops/specs/OPS_SUITE_EXPOSURE_READ_MODEL_CONTRACT.md` — Kanonischer Read-Model-Contract für Exposure State im Ops Cockpit
- `docs/ops/specs/OPS_SUITE_EXPOSURE_DATA_SOURCE_DECISION.md` — Kanonische Entscheidung: live_runs als primäre Exposure-Datenquelle

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
