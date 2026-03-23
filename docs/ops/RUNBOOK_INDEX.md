# Ops Runbook Index

> **Zweck:** Zentraler Verweis auf alle Runbooks und Ops-Dokumentation  
> **Stand:** 2026-03-10  
> **Status:** canonical

---

## Runbooks

| Kategorie | Pfad | Hinweis |
|-----------|------|---------|
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
| `scripts&#47;ops&#47;create_required_checks_drift_guard_pr.sh` | [RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE](runbooks/RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE_OPERATIONS.md) |

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

