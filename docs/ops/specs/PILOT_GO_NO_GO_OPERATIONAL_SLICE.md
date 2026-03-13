# Pilot Go/No-Go Operational Slice

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Operator-facing mapping from PILOT_GO_NO_GO_CHECKLIST to evidence sources (Ops Cockpit, Runbooks, Config)
docs_token: DOCS_TOKEN_PILOT_GO_NO_GO_OPERATIONAL_SLICE

## Intent
This document maps each checklist item in `PILOT_GO_NO_GO_CHECKLIST` to the concrete evidence sources an operator can use to answer the question. It makes the go/no-go material operator-usable without adding execution authority.

## Relationship
- Companion to `docs/ops/specs/PILOT_GO_NO_GO_CHECKLIST.md`
- References Ops Cockpit payload structure from `src/webui/ops_cockpit.py`
- No direct activation authority; read-only operator guidance

## Checklist → Evidence Mapping

| # | Area | Question | Evidence Source | Where to Look |
|---|------|----------|-----------------|---------------|
| 1 | Safety Gates | enabled/armed/confirm-token/dry-run explicit? | Ops Cockpit | `policy_state`, `operator_state`, `guard_state` (enabled, armed, dry_run, confirm_token_required) |
| 2 | Kill Switch | posture visible and clear? | Ops Cockpit | `policy_state.kill_switch_active`, `incident_state.kill_switch_active`; `data/kill_switch/state.json` |
| 3 | Policy Posture | current policy action visible? | Ops Cockpit | `policy_state.action` (NO_TRADE / TRADE_READY), `policy_state.summary` |
| 4 | Operator Visibility | blocked vs allowed quickly identifiable? | Ops Cockpit | `policy_state.blocked`, `incident_state.requires_operator_attention`, Executive Summary |
| 5 | Pilot Caps | bounded caps defined and documented? | Ops Cockpit + Config | `exposure_state.caps_configured` (from `live_risk` in config.toml) |
| 6 | Treasury Separation | trading vs treasury explicit? | Ops Cockpit | `guard_state.treasury_separation` = enforced; `src/ops/treasury_separation_gate.py` |
| 7 | Fee/Slippage Realism | conservative assumptions documented? | Edge Case Matrix | `PILOT_EXECUTION_EDGE_CASE_MATRIX` Fee/slippage row; no dedicated assumptions doc yet |
| 8 | Partial Fill Handling | bounded and understood? | Specs + Engine | `PILOT_EXECUTION_EDGE_CASE_MATRIX`, `ReconciliationEngine` (position/cash recon) |
| 9 | Stale State Handling | stale balance/order/position handled safely? | Ops Cockpit | `stale_state` (balance, position, order, exposure); `exposure_state.stale` |
| 10 | Restart / Replay | restart and replay semantics safe? | Edge Case Matrix | `PILOT_EXECUTION_EDGE_CASE_MATRIX` Restart mid-session, Replay ambiguity; no dedicated runbook yet |
| 11 | Incident Runbooks | critical incident paths exist? | Runbooks | `RUNBOOK_PILOT_INCIDENT_*` (Exchange Degraded, Telemetry Degraded, Reconciliation Mismatch, Transfer Ambiguity, Session End Mismatch, Unexpected Exposure) |
| 12 | Evidence Continuity | evidence/audit trail sufficient? | Ops Cockpit | `evidence_state` (summary, audit_trail, telemetry_evidence) |
| 13 | Dependency Degradation | degraded exchange/telemetry explicit? | Ops Cockpit | `dependencies_state` (exchange, telemetry, market_data_cache, degraded) |
| 14 | Human Supervision | pilot explicitly operator-supervised? | Specs | `PILOT_GO_NO_GO_CHECKLIST`, `PILOT_READY_EXECUTION_REVIEW_SPEC`; no cockpit surface |
| 15 | Ambiguity Rule | ambiguity → NO_TRADE / safe stop? | Ops Cockpit + Specs | `policy_state`, `incident_state`; `RECONCILIATION_FLOW_SPEC` |

## Ops Cockpit Entry Point
- Payload: `build_ops_cockpit_payload()` in `src/webui/ops_cockpit.py`
- HTML: `render_ops_cockpit_html()` for operator dashboard view

## Known Gaps (Follow-up)
- Fee/slippage: dedicated conservative-assumptions document
- Restart mid-session: dedicated runbook
- Human supervision: explicit cockpit surface (optional)
- Go/No-Go script: automated checklist evaluation against cockpit/config (future)

## Explicit Non-Goals
- no direct activation authority
- no replacement for operator judgment
- no claim of pilot readiness
