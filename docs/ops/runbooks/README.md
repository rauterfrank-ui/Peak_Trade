# Peak_Trade Operator Runbooks

**Owner:** ops  
**Purpose:** Indexed collection of operational runbooks for Peak_Trade platform

---

- [RUNBOOK_TECH_DEBT_TOP3_ROI_FINISH.md](./RUNBOOK_TECH_DEBT_TOP3_ROI_FINISH.md): Tech-Debt Top-3 ROI bis Finish (Cursor Multi-Agent)


## Research & New Listings (CEX+DEX Crawler, AI Layers)

- [RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES_OPEN_POINTS_2026-02-10.md](RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES_OPEN_POINTS_2026-02-10.md) — Cursor Multi-Agent Runbook für offene Peak_Trade Features (Einstieg→Endpunkt, Blöcke A–J).
- [New Listings Crawler Runbook](./new_listings_crawler_runbook.md)

## Runbook Categories

### Docs Gates & Policies

Runbooks for operating and troubleshooting documentation quality gates:

- [Gates Overview](../GATES_OVERVIEW.md) – Complete gates map (where/what/why/how), change impact matrix, and operator snapshot block
- [RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md](RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md) — Local docs gates snapshot (changed scope), operator evidence block (Cursor Multi-Agent)
- [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md) — Operating the Docs Reference Targets Gate
- [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md) — Handling false positives
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md) — Operating the Docs Token Policy Gate
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) — Docs Token Policy Gate reference
- [RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md) — Operating the Docs Diff Guard Policy Gate
- [RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md](RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md) — Quick start for all docs gates
- [RUNBOOK_DOCS_GRAPH_TRIAGE_AND_REMEDIATION.md](RUNBOOK_DOCS_GRAPH_TRIAGE_AND_REMEDIATION.md) — Docs graph triage and remediation
- [RUNBOOK_DOCS_GATES_FIX_FORWARD_CI_TRIAGE_CURSOR_MULTI_AGENT.md](RUNBOOK_DOCS_GATES_FIX_FORWARD_CI_TRIAGE_CURSOR_MULTI_AGENT.md) — Fix-forward CI triage for Token Policy and Reference Targets gate failures

### AI Autonomy & Control Center

Runbooks for AI autonomy workflows and control center operations:

- [RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md) — Phase 4B M2 Cursor Multi-Agent
- [RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md](RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md) — Control Center operations
- [RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md](RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md) — Control Center dashboard
- [RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_INCIDENT_TRIAGE.md](RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_INCIDENT_TRIAGE.md) — Incident triage
- [RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATOR_CHEATSHEET.md](RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATOR_CHEATSHEET.md) — Operator cheatsheet
- [RUNBOOK_AI_AUTONOMY_4B_M3_CURSOR_CONTROL_CENTER.md](RUNBOOK_AI_AUTONOMY_4B_M3_CURSOR_CONTROL_CENTER.md) — Cursor Control Center
- [CURSOR_MULTI_AGENT_INTEGRATION_RUNBOOK_V1.md](CURSOR_MULTI_AGENT_INTEGRATION_RUNBOOK_V1.md) — Cursor Multi-Agent integration
- [Wave3_Control_Center_Cheatsheet_v2.md](Wave3_Control_Center_Cheatsheet_v2.md) — Wave 3 Control Center cheatsheet

### Phase-Specific Workflows

Runbooks for specific phase implementations and workflows:

- [RUNBOOK_TO_FINISH_MASTER.md](RUNBOOK_TO_FINISH_MASTER.md) — Master: docs-only Branch → PR → D2/D3/D4 DoD → SSoT „Finish“-Definition (NO‑LIVE)
- [RUNBOOK_FINISH_A_MVP.md](RUNBOOK_FINISH_A_MVP.md) — Finish Level A (MVP): Backtest → Artifacts → Report → Watch‑Only Dashboard (Cursor Multi‑Agent, NO‑LIVE)
- [RUNBOOK_FINISH_B_BETA_EXECUTIONPIPELINE.md](RUNBOOK_FINISH_B_BETA_EXECUTIONPIPELINE.md) — Finish Level B (Beta): ExecutionPipeline + Ledger + Paper‑Trading (Cursor Multi‑Agent, NO‑LIVE)
- [RUNBOOK_EXECUTION_SLICE2_LEDGER_PNL.md](RUNBOOK_EXECUTION_SLICE2_LEDGER_PNL.md) — ExecutionPipeline Slice 2: Ledger/Accounting + deterministic PnL (NO‑LIVE, snapshot-only)
- [RUNBOOK_FINISH_C_V1_LIVE_BROKER_OPS.md](RUNBOOK_FINISH_C_V1_LIVE_BROKER_OPS.md) — Finish Level C (v1.0) overview/pointer: Broker Adapter + Live‑Ops (governance‑first, NO‑LIVE default)
- [finish_c/RUNBOOK_FINISH_C_MASTER.md](finish_c/RUNBOOK_FINISH_C_MASTER.md) — Finish Level C (Live‑Broker‑Ops Track): governance‑safe, NO‑LIVE default, C0–C5 + D1 artifacts repro
- [RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md](RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md) — Workstream D4: Ops/Governance polish (docs gates, evidence, merge logs, release checklist)
- [RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md](RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md) — Phase 5A normalized report consumer
- [RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED_CURSOR_MULTI_AGENT.md](RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED_CURSOR_MULTI_AGENT.md) — Phase 5B trend ledger from seed (multi-agent)
- [RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md](RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md) — Phase 5B trend ledger from seed
- [RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE_OPERATIONS.md](RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE_OPERATIONS.md) — Phase 5E required checks hygiene gate
- [RUNBOOK_PHASE6_STRATEGY_SWITCH_SANITY_CHECK_CURSOR_MULTI_AGENT.md](RUNBOOK_PHASE6_STRATEGY_SWITCH_SANITY_CHECK_CURSOR_MULTI_AGENT.md) — Phase 6 strategy switch sanity check
- [RUNBOOK_PHASE7_WORKFLOW_DOCS_FINISH_CLOSEOUT_2026-01-12_CURSOR_MULTI_AGENT.md](RUNBOOK_PHASE7_WORKFLOW_DOCS_FINISH_CLOSEOUT_2026-01-12_CURSOR_MULTI_AGENT.md) — Phase 7 workflow docs finish closeout
- [RUNBOOK_PHASE8_DOCS_INTEGRITY_HARDENING_CURSOR_MULTI_AGENT.md](RUNBOOK_PHASE8_DOCS_INTEGRITY_HARDENING_CURSOR_MULTI_AGENT.md) — Phase 8 docs integrity hardening
- [RUNBOOK_WORKFLOW_DOCS_INTEGRATION_2026-01-12_CURSOR_MULTI_AGENT.md](RUNBOOK_WORKFLOW_DOCS_INTEGRATION_2026-01-12_CURSOR_MULTI_AGENT.md) — Workflow docs integration
- [Phase T — Data Node + Immutable Export Channel + GitHub Consumer](PHASE_T_DATA_NODE_EXPORT_CHANNEL.md) — Data Node, export packs, GitHub consumer (audit-safe)

### Runbook B — Execution Gates (B5/B3/B2)

Safety controls for Shadow → Mini-Live (ArmedGate, RiskGate, Reconciliation). **All OFF by default.**

- [runbook_b_execution_gates_quickstart.md](runbook_b_execution_gates_quickstart.md) — Quickstart: env toggles, safe usage, config examples
- [runbook_b_env_example.txt](runbook_b_env_example.txt) — Minimal env example (all disabled)

### CI & Operations

Runbooks for CI operations and general operational procedures:

- [PR Ops v1 Runbook](../pr/pr_ops_v1_runbook.md) — PR watch, closeout, required-checks snapshot (generated via `p41 --with-pr-ops`)
- [RUNBOOK_MCP_TOOLING.md](RUNBOOK_MCP_TOOLING.md) — MCP Tooling (Cursor): Playwright + Grafana (read-only), Secret-Handling, Smoke/Preflight
- [RUNBOOK_AI_LIVE_OPS_LOCAL.md](RUNBOOK_AI_LIVE_OPS_LOCAL.md) — AI Live Ops Pack (local start/verify/troubleshoot; snapshot-only)
- [RUNBOOK_EXECUTION_WATCH_DEMO_STACK.md](RUNBOOK_EXECUTION_WATCH_DEMO_STACK.md) — Execution Watch Demo-Stack (shadow_mvs + ai_live, STRICT NO-LIVE)
- [RUNBOOK_SLICE_3_6_REPLAY_REGRESSION_PACK_OPERATOR_SHORTCUT.md](RUNBOOK_SLICE_3_6_REPLAY_REGRESSION_PACK_OPERATOR_SHORTCUT.md) — Slice 3.6: Offline deterministic replay regression pack shortcut (bundle → compare → consume)
- [RUNBOOK_PR736_CI_SNAPSHOT_AUTOMERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md](RUNBOOK_PR736_CI_SNAPSHOT_AUTOMERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md) — PR #736: CI snapshot → enable auto-merge → post-merge verify on main (snapshot-only)
- [RUNBOOK_OPERATOR_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md](RUNBOOK_OPERATOR_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md) — Operator Dashboard (Watch-Only) start→finish (local, read-only monitoring + deterministic snapshot export)
- [RUNBOOK_DASHBOARD_WATCH_ONLY_V01B.md](RUNBOOK_DASHBOARD_WATCH_ONLY_V01B.md) — Dashboard Watch-Only UI v0.1B (observability) for src/live/web/app.py (read-only)
- [RUNBOOK_EXECUTION_WATCH_DASHBOARD.md](RUNBOOK_EXECUTION_WATCH_DASHBOARD.md) — Execution Watch Dashboard v0.2 (read-only execution runs/events + session registry)
- [RUNBOOK_CI_STATUS_POLLING_HOWTO.md](RUNBOOK_CI_STATUS_POLLING_HOWTO.md) — CI status polling how-to
- [PHASE4E_STABILITY_MONITORING_CHECKLIST.md](PHASE4E_STABILITY_MONITORING_CHECKLIST.md) — Phase 4E stability monitoring checklist
- [rebase_cleanup_workflow.md](rebase_cleanup_workflow.md) — Rebase cleanup workflow
- [Stale Branch Hygiene (Local "gone")](RUNBOOK_STALE_BRANCH_HYGIENE_LOCAL_GONE_CURSOR_MULTI_AGENT.md) — Safe cleanup of local branches with deleted upstream refs (DRY-RUN, recovery via reflog, protected branches)
- [RUNBOOK_BRANCH_CLEANUP_RECOVERY.md](RUNBOOK_BRANCH_CLEANUP_RECOVERY.md) — Branch cleanup recovery (tags + bundles)
- [Commit Salvage Workflow](RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md) ⭐ — Salvaging commits from wrong branch (feature branch → PR → merge workflow)
- [Pointer Pattern Operations](RUNBOOK_POINTER_PATTERN_OPERATIONS.md) — Operator runbook for root canonical runbooks integration (pointer pattern maintenance, gates compliance)
- [Pointer Pattern Quarterly Review](RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md) — Quarterly drift control and orphan prevention for pointer pattern architecture
- [github_rulesets_pr_reviews_policy.md](github_rulesets_pr_reviews_policy.md) — GitHub rulesets PR reviews policy
- [policy_critic_execution_override.md](policy_critic_execution_override.md) — Policy critic execution override
- [RUNBOOK_CURSOR_MULTI_AGENT_ORCHESTRATOR_NEXT_TASKS_2026-01-18.md](RUNBOOK_CURSOR_MULTI_AGENT_ORCHESTRATOR_NEXT_TASKS_2026-01-18.md) — Cursor Multi-Agent Orchestrator next tasks operating system (v2026-01-18) (snapshot-only, NO-LIVE)
- [RUNBOOK_POST_MERGE_VERIFY_MAIN_AND_DOCS_GATES_SNAPSHOT_CURSOR_MULTI_AGENT.md](RUNBOOK_POST_MERGE_VERIFY_MAIN_AND_DOCS_GATES_SNAPSHOT_CURSOR_MULTI_AGENT.md) — Post-merge verify (main) + local docs gates snapshot (no-watch)
- [RUNBOOK_DOCS_ONLY_PR_MERGE_AUTOMERGE_AND_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md](RUNBOOK_DOCS_ONLY_PR_MERGE_AUTOMERGE_AND_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md) — Docs-only PR merge (auto-merge/squash) + CI snapshot + merge-log chain (Cursor Multi-Agent)
- [RUNBOOK_MERGE_LOG_PR_MERGE_AND_OPTIONAL_META_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md](RUNBOOK_MERGE_LOG_PR_MERGE_AND_OPTIONAL_META_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md) — Merge-log PR merge (squash) + CI snapshot + optional meta merge-log chain (Cursor Multi-Agent)

### Incident Response & Troubleshooting

Runbooks for responding to incidents and troubleshooting:

- [general.md](general.md) — General incident response procedures
- [data_feed_down.md](data_feed_down.md) — Data feed down incident response
- [drift_critical.md](drift_critical.md) — Critical drift incident response
- [drift_high.md](drift_high.md) — High drift incident response
- [execution_error.md](execution_error.md) — Execution error incident response
- [risk_limit_breach.md](risk_limit_breach.md) — Risk limit breach incident response
- [var_report_compare.md](var_report_compare.md) — VaR report comparison and analysis

---

## Runbook Conventions

### File Naming
- **Phase-specific:** `RUNBOOK_PHASE<N>_<DESCRIPTION>.md`
- **General operator:** `RUNBOOK_<TOPIC>_OPERATOR.md`
- **Incident response:** `<incident_type>.md` (lowercase, underscore-separated)
- **Cursor Multi-Agent:** `*_CURSOR_MULTI_AGENT.md` suffix

### Structure
All runbooks should follow this structure:
1. **Purpose:** What this runbook covers
2. **Scope:** When to use this runbook
3. **Pre-flight Checklist:** Required state before starting
4. **Steps:** Numbered, actionable steps
5. **Verification:** How to verify success
6. **Troubleshooting:** Common issues and solutions
7. **References:** Related docs, PRs, commits

---

## Related Documentation

- [../README.md](../README.md) — Docs Ops overview
- [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) — Evidence index
- [../control_center/CONTROL_CENTER_NAV.md](../control_center/CONTROL_CENTER_NAV.md) — Control Center navigation

---

## Notes

### Runbook Locations

Most operational runbooks are located in docs/ops/runbooks/. Some runbooks remain in the repo root for provenance or to minimize risk of breaking references:

- **Root-level runbooks** (marked with ⭐): Canonical artifact in repo root, pointer in this index
- **Standard runbooks**: Directly located in docs/ops/runbooks/

This hybrid approach balances discoverability (all findable from this index) with stability (no forced migrations of established references).

---

**Last Updated:** 2026-01-18  
**Maintainer:** ops
