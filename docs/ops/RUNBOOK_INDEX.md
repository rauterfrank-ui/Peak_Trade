# Ops Runbook Index

> **Zweck:** Zentraler Verweis auf alle Runbooks und Ops-Dokumentation  
> **Stand:** 2026-03-10  
> **Status:** canonical

---

## Canonical Vocabulary / Authority / Provenance v0

- Canonical Spec (verbindlich): [docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- Normative Kurzregel: `Governance`, `Safety`, `Kill-Switch` und `Risk&#47;Exposure Caps` sind bindend; `Switch-Gate` und `AI Orchestrator` sind advisory, sofern nicht separat und ausdrücklich anderweitig durch canonical authority definiert.
- Claim-Disziplin: Ist-/Runtime-/E2E-Behauptungen nur mit verifizierbarer Repo-Evidenz; sonst klar als `Soll` / `intended` / `documented` / `unclear` trennen (Klassen und Definitionen: Spec, Abschnitt 6).

- LevelUp **v0** — kanonische Ops-/Spec-Oberfläche (Manifest-/IO-/CLI, ohne neue Autorität): [`LEVELUP_V0_CANONICAL_SURFACE.md`](specs/LEVELUP_V0_CANONICAL_SURFACE.md)

---

## Master Execution Runbook (Program-Wide, non-authorizing)

| Artefakt | Pfad | Rolle |
|----------|------|-------|
| **Aktiver kanonischer Repo-Runbook-Owner** | [master_execution/PEAK_TRADE_MASTER_EXECUTION_RUNBOOK_V1.md](master_execution/PEAK_TRADE_MASTER_EXECUTION_RUNBOOK_V1.md) | Current-State-, Resume- und Programm-Steuerungs-Owner; **keine** Trading-/Runtime-Authority |
| **Maschinen-Checkpoint** | [master_execution/CURRENT_CHECKPOINT.env](master_execution/CURRENT_CHECKPOINT.env) | Parsebarer Programm-Status |
| **Changelog (append-only)** | [master_execution/RUNBOOK_CHANGELOG.csv](master_execution/RUNBOOK_CHANGELOG.csv) | Statusänderungen und Migrationen |
| **Durable Ursprungssnapshot** | `…&#47;planning&#47;peak_trade_master_execution_runbook_v1_20260626T233500Z` (Archive) | Unveränderlicher verified Origin (`MANIFEST_VERIFY_RC=0`) |
| **Desktop-Lesekopie** | `/Users/frnkhrz/Desktop/Peak_Trade_Master_Execution_Runbook_V1.md` | **Nicht kanonisch** — Convenience only |

---

## Runbooks

| Kategorie | Pfad | Hinweis |
|-----------|------|---------|
| **Futures (readiness, non-authority)** | [runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md](runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md) | Krypto-Perp/CME-Readiness-Stufen; **kein** Live-/Execution-Enable |
| **Ops Runbooks** | [runbooks/](runbooks/) | Standard- und Incident-Runbooks |
| **Pre-Flight** | [../../PRE_FLIGHT_CHECKLIST_RUNBOOK_OPS.md](../../PRE_FLIGHT_CHECKLIST_RUNBOOK_OPS.md) | Pre-Flight-Checkliste (Repo-Root) |
| **Audit** | [../audit/AUDIT_RUNBOOK_COMPLETE.md](../audit/AUDIT_RUNBOOK_COMPLETE.md) | Audit-Runbook |

---

## Ops-Docs

| Bereich | Pfad |
|---------|------|
| **Ops allgemein** | [docs/ops/](.) |
| **Workflows** | [workflows/](workflows/) |
| **Registry** | [registry/](registry/) |
| **Archiv** | [_archive/](_archive/) |

### Workflow Policy Docs

Policy-Dokumente für illustrative Pfade und Workflow-Konventionen (relevant für Docs-Gates):

- [WORKFLOW_NOTES_FRONTDOOR.md](workflows/WORKFLOW_NOTES_FRONTDOOR.md) — Policy für `&#47;`-Encoding in Markdown
- [PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md](workflows/PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md) — Historische Workflow-Notizen

---

## Script Orientation (Key Ops Scripts → Runbook)

| Script | Primärer Einstieg |
|--------|-------------------|
| `scripts&#47;ops&#47;check_merge_log_hygiene.py` | [RUNBOOK_MERGE_LOG_PR_MERGE_AND_OPTIONAL_META_MERGE_LOG_CHAIN](runbooks/RUNBOOK_MERGE_LOG_PR_MERGE_AND_OPTIONAL_META_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md), [RUNBOOK_DOCS_ONLY_PR_MERGE_AUTOMERGE](runbooks/RUNBOOK_DOCS_ONLY_PR_MERGE_AUTOMERGE_AND_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md) |
| `scripts&#47;ci&#47;validate_required_checks_hygiene.py` | [RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE](runbooks/RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE_OPERATIONS.md) |
| `scripts&#47;ops&#47;validate_docs_token_policy.py` | [RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR](runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md), [GATES_OVERVIEW](GATES_OVERVIEW.md) |
| `scripts&#47;ops&#47;verify_docs_reference_targets.sh` | [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR](runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md), [GATES_OVERVIEW](GATES_OVERVIEW.md) |
| `scripts&#47;ops&#47;reconcile_required_checks_branch_protection.py --check` | [RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE](runbooks/RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE_OPERATIONS.md) |
| `scripts&#47;ops&#47;check_docs_drift_guard.py` | [RUNBOOK_CURSOR_MULTI_AGENT_TRUTH_GOVERNANCE](runbooks/RUNBOOK_CURSOR_MULTI_AGENT_TRUTH_GOVERNANCE.md) |
| `scripts&#47;ops&#47;pt_docs_gates_snapshot.sh` | [RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT](runbooks/RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md), [RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART](runbooks/RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md) |

**Weitere Scripts:** [WORKFLOW_SCRIPTS.md](WORKFLOW_SCRIPTS.md), [OPS_SCRIPT_TEMPLATE_GUIDE.md](OPS_SCRIPT_TEMPLATE_GUIDE.md)

---

## Workflow-Übersicht

Für eine zentrale Workflow- und Runbook-Übersicht siehe:

- [WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md](../../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md) (Repo-Root)

## Critical Operator Runbooks
- [incident_stop_freeze_rollback.md](runbooks/incident_stop_freeze_rollback.md)
- [risk_limit_breach.md](runbooks/risk_limit_breach.md)
- [ROLLBACK_PROCEDURE.md](../runbooks/ROLLBACK_PROCEDURE.md)
- [KILL_SWITCH_RUNBOOK.md](KILL_SWITCH_RUNBOOK.md)
- [KILL_SWITCH_TROUBLESHOOTING.md](KILL_SWITCH_TROUBLESHOOTING.md)
- [LIVE_MODE_TRANSITION_RUNBOOK.md](../runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md)
- [EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md](EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md)
- [live_pilot_session_wrapper.md](runbooks/live_pilot_session_wrapper.md)
- [KILL_SWITCH_DRILL_PROCEDURE.md](../runbooks/KILL_SWITCH_DRILL_PROCEDURE.md)

## Incident-stop / HOLD classification discoverability

- Canonical incident-stop runbook: `docs/ops/runbooks/incident_stop_freeze_rollback.md`
- Scheduler/preflight HOLD boundary: `docs/SCHEDULER_DAEMON.md`
- Paper/Shadow-247 preflight contract: `docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md`
- Shadow-247 governance charter (activation ladder, non-authorizing): `docs/ops/runbooks/SHADOW_247_GOVERNANCE_CHARTER_V0.md`

Use these as index pointers only. Under `HOLD_NO_PAPER_RUN`, `active` and `unknown`
classifications keep runtime and go-live progression blocked. `stale_closed` requires
the documented follow-up procedure before read-only snapshot/preflight checks are rerun.
This index is non-authorizing and must not become a duplicate readiness or evidence
surface.
