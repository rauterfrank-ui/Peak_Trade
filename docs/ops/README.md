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
- `docs/ops/specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md` — Operator-Mapping: Checkliste → Ops Cockpit / Runbooks / Config
- `docs/ops/specs/TREASURY_BALANCE_SEPARATION_SPEC.md` — Trading vs Treasury Balance: Execution muss Trading-Balance nutzen
- `docs/ops/specs/RECONCILIATION_FLOW_SPEC.md` — Kanonische Reconciliation-Flow-Spezifikation für bounded pilot / execution safety
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md` — Incident-Runbook für degraded exchange/broker Verhalten
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md` — Incident-Runbook für degradierte Telemetrie / Evidenz
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md` — Incident-Runbook für Reconciliation-Mismatch
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md` — Incident-Runbook für Transfer-Ambiguity (Asset-Transfer-Status unklar)
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md` — Incident-Runbook für Session-End-Mismatch (lokaler Closeout vs Broker)
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md` — Incident-Runbook für unexpected exposure

- `docs/ops/specs/OPS_SUITE_EXPOSURE_READ_MODEL_CONTRACT.md` — Kanonischer Read-Model-Contract für Exposure State im Ops Cockpit
- `docs/ops/specs/OPS_SUITE_EXPOSURE_DATA_SOURCE_DECISION.md` — Kanonische Entscheidung: live_runs als primäre Exposure-Datenquelle

- `docs/ops/specs/FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS.md` — Kanonische konservative Fee-/Slippage-Annahmen für bounded Echtgeldpilot / Go-No-Go Row 7

- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md` — Incident-Runbook für Prozess-Neustart während aktiver Orders/Positions

- `docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md` — Kanonischer operatorischer Eintrittsvertrag für den ersten strikt begrenzten Echtgeldpilot
- `docs/ops/runbooks/RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md` — Kanonische First-Session-Sequenz für den ersten strikt begrenzten Echtgeldpilot-Kandidatenfluss

- `docs/ops/specs/BOUNDED_PILOT_CAPS_ENFORCEMENT_POINT.md` — Kanonische Einordnung des aktuellen Caps-Enforcement-Punkts im bounded-pilot-Pfad

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

## Bounded Acceptance Documentation Chain
- start here: `docs&#47;ops&#47;reviews&#47;bounded_acceptance_start_here_page&#47;START_HERE.md`
- index, runbook, cheat sheet, go/no-go snapshot, readiness matrix, and governance framing are linked from there

## Cursor Multi-Agent
- Frontdoor: [CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md](CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md)
- Founder/Operator-Regel: `.cursor/rules/peak_trade_founder_operator_paper_stability_guard.mdc` (`paper_stability_guard`, one-topic-one-PR, read-only-inventory-first)

