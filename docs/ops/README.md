# Peak_Trade — Ops documentation index
<!-- MERGE_LOG_EXAMPLES:START -->
- PR #999 — docs(grafana): fix DS_LOCAL uid templating in execution watch dashboard: docs/ops/PR_999_MERGE_LOG.md
<!-- MERGE_LOG_EXAMPLES:END -->








**[Docs Truth Map](registry/DOCS_TRUTH_MAP.md)** — canonical ops documentation registry and change log (truth-first).

<!-- ops readme status navigation note -->
- Projektstatus / Navigation: `docs&#47;INDEX.md` ist der zentrale Einstieg für Docs-Navigation.
- Für kompakten Status-/Lookup-Einstieg nutze `docs&#47;ops&#47;STATUS_MATRIX.md`; für datierten narrativen Kontext nutze `docs&#47;ops&#47;STATUS_OVERVIEW_2026-02-19.md`.

## Canonical Vocabulary / Authority / Provenance v0

- Canonical Spec (verbindlich): [docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- Normative Kurzregel: `Governance > Safety&#47;Kill-Switch > Risk&#47;Exposure Caps`; `Switch-Gate` und `AI Orchestrator` sind Control-Orchestration/advisory, aber keine finale Execution Authority.
- Claim-Disziplin: Claims nur in den Klassen `repo-evidenced`, `documented`, `unverified`, `not-claimed` formulieren (Abschnitt 6); `unverified` und `not-claimed` nicht als verifizierte Fakten ausgeben; `operator-stated` explizit markieren; keine impliziten E2E-/Runtime-Behauptungen.

- LevelUp **v0** (additive Manifest-/IO-/CLI-Grundlage, keine neue Autorität): [`docs/ops/specs/LEVELUP_V0_CANONICAL_SURFACE.md`](specs/LEVELUP_V0_CANONICAL_SURFACE.md)

## HTTP path index — Operator WebUI & live.web (local defaults)

Ports **8000** (Operator WebUI, `src.webui.app`) and **8010** (live.web, `src.live.web.app` via `scripts/ops/run_live_webui.sh`) are **local defaults** on `127.0.0.1`. Processes are **separate**; there is **no shared control plane**. Paths below are for **orientation / navigation** (read-only UI posture; no change to execution or approval semantics).

**Operator WebUI** (default `http://127.0.0.1:8000`):

- `/` — main dashboard
- `/ops` — Ops Cockpit (read-only, local artifacts)
- `/ops/stage1` — Stage1 ops dashboard
- `/ops/workflows` — Ops workflow hub
- `/ops/ci-health` — CI & governance health panel
- `/session/{session_id}` — session detail HTML (read-only)

**Additional Operator WebUI nav** (read-only; labels as in the header: `templates/peak_trade_dashboard/base.html`):

- `/execution_watch` — Execution Watch
- `/live/alerts` — Alerts
- `/r_and_d` — R&D Experiments
- `/r_and_d/experiment/{run_id}` — R&D experiment detail HTML (read-only)
- `/r_and_d/comparison` — R&D multi-run comparison HTML (read-only)
- `/live/telemetry` — Telemetry

**live.web** (default `http://127.0.0.1:8010`):

- `/` and `/dashboard` — live runs dashboard HTML
- `/watch` — watch overview HTML
- `/watch/runs/{run_id}` — run detail (watch)
- `/sessions/{run_id}` — alias to the same run detail

live.web also exposes **read-only** JSON under the **`/api/v0`** prefix (watch/status API); details and examples: [`LIVE_OPERATIONAL_RUNBOOKS.md`](../LIVE_OPERATIONAL_RUNBOOKS.md) (section 10d.4), implementation: [`src/live/web/api_v0.py`](../../src/live/web/api_v0.py).

The live.web companion strips (main dashboard and watch/session HTML) are **read-only navigation** to **`http://127.0.0.1:8000/`**, **`http://127.0.0.1:8000/ops`**, **`http://127.0.0.1:8000/ops/ci-health`**, and the Run UI default **`http://127.0.0.1:8010/`** — local defaults per README, **separate processes**, **no shared control plane** (see `src/live/web/app.py`).

For scripts and port notes, see the root [`README.md`](../../README.md) section **Web UI**.

**Cursor Auto-PR (`feat&#47;**` → `main`):** On pushes to `feat&#47;**`, [`.github/workflows/cursor_auto_pr.yml`](../../.github/workflows/cursor_auto_pr.yml) runs. Each workflow run performs **one** `workflow_dispatch` pass for required checks (the "Dispatch required checks" step); when an open PR already exists, the first step only logs and does **not** dispatch again, so there is no duplicate dispatch sequence in the same run (post–PR #2475).

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
- `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md` — **Bindende kanonische Steuerdatei** für den aktuellen Master-V2-First-Live-Enablement-Clarification-Workstream (Readiness Contract/Ladder)
- `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md` — Kanonisches read-only Interpretations-/Statusmodell v1 für Master-V2-Readiness-Reviews (nicht autorisierend, keine Gate-Closure)
- `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md` — Kanonische docs-only Report-Surface v1 für standardisierte Gate-Status-Tabellen und Per-Gate-Detailformate (read-only, non-authorizing)

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

## Operator Critical Runbooks
- Incident stop / freeze / rollback: [runbooks/incident_stop_freeze_rollback.md](runbooks/incident_stop_freeze_rollback.md)
- Risk limit breach: [runbooks/risk_limit_breach.md](runbooks/risk_limit_breach.md)
- Rollback procedure: [../runbooks/ROLLBACK_PROCEDURE.md](../runbooks/ROLLBACK_PROCEDURE.md)
- Kill switch runbook: [KILL_SWITCH_RUNBOOK.md](KILL_SWITCH_RUNBOOK.md)
- Kill switch troubleshooting: [KILL_SWITCH_TROUBLESHOOTING.md](KILL_SWITCH_TROUBLESHOOTING.md)
- Live mode transition: [../runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md](../runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md)
- Execution telemetry incident: [EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md](EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md)
- Live pilot session wrapper: [runbooks/live_pilot_session_wrapper.md](runbooks/live_pilot_session_wrapper.md)
- Kill switch drill procedure: [../runbooks/KILL_SWITCH_DRILL_PROCEDURE.md](../runbooks/KILL_SWITCH_DRILL_PROCEDURE.md)

