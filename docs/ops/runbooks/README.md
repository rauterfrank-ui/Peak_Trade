# Peak_Trade Operator Runbooks

**Owner:** ops  
**Purpose:** Indexed collection of operational runbooks for Peak_Trade platform

---

## Canonical Vocabulary / Authority / Provenance v0

- Binding spec: [docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](../specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- **Primary norm** for term discipline, authority/veto precedence, and claim/provenance discipline (details in the spec).
- Claim classes: `repo-evidenced`, `documented`, `operator-stated`, `unverified`, `not-claimed` (definitions: spec section 6).

---

## Workflow / policy references

Markdown workflow-policy notes live under `docs&#47;ops&#47;workflows&#47;`:

- [WORKFLOW_NOTES_FRONTDOOR.md](../workflows/WORKFLOW_NOTES_FRONTDOOR.md)
- [PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md](../workflows/PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md)

Broader Ops runbook/script orientation stays in [`RUNBOOK_INDEX.md`](../RUNBOOK_INDEX.md).

---

- [RUNBOOK_TECH_DEBT_TOP3_ROI_FINISH.md](./RUNBOOK_TECH_DEBT_TOP3_ROI_FINISH.md): Tech-Debt Top-3 ROI bis Finish (Cursor Multi-Agent)


## Research & New Listings (CEX+DEX Crawler, AI Layers)

- [RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES_OPEN_POINTS_2026-02-10.md](./RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES_OPEN_POINTS_2026-02-10.md) — Cursor Multi-Agent Runbook für offene Peak_Trade Features (Einstieg→Endpunkt, Blöcke A–J).
- [New Listings Crawler Runbook](./new_listings_crawler_runbook.md)

## Runbook Categories

### Docs Gates & Policies

Runbooks for operating and troubleshooting documentation quality gates:

- [Gates Overview](../GATES_OVERVIEW.md) – Complete gates map (where/what/why/how), change impact matrix, and operator snapshot block
- [RUNBOOK_CURSOR_MULTI_AGENT_TRUTH_GOVERNANCE.md](RUNBOOK_CURSOR_MULTI_AGENT_TRUTH_GOVERNANCE.md) — Cursor Multi-Agent: Truth / Docs / Drift Governance (Truth Map, Claims, Drift Guard, Officers)
- [RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md](RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md) — Local docs gates snapshot (changed scope), operator evidence block (Cursor Multi-Agent)
- [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md) — Operating the Docs Reference Targets Gate
- [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md) — Handling false positives
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md) — Operating the Docs Token Policy Gate
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) — Docs Token Policy Gate reference
- [RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md) — Operating the Docs Diff Guard Policy Gate
- [RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md](RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md) — Quick start for all docs gates
- [RUNBOOK_DOCS_GRAPH_TRIAGE_AND_REMEDIATION.md](RUNBOOK_DOCS_GRAPH_TRIAGE_AND_REMEDIATION.md) — Docs graph triage and remediation
- [RUNBOOK_DOCS_GATES_FIX_FORWARD_CI_TRIAGE_CURSOR_MULTI_AGENT.md](RUNBOOK_DOCS_GATES_FIX_FORWARD_CI_TRIAGE_CURSOR_MULTI_AGENT.md) — Fix-forward CI triage for Token Policy and Reference Targets gate failures
- [RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md](RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md) — Secret Handling (credential boundaries): planning-first, Cursor vs human-only, placeholders only (non-authorizing)

### Non-execution readiness & observation gates (planning only)

- [TESTNET_CHECKER_PREREQUISITES_V0.md](TESTNET_CHECKER_PREREQUISITES_V0.md) — Read-only Testnet prerequisite keys (non-authorizing)
- [ORPHAN_SCHEDULER_AFTER_RUN_WITH_TIMEOUT_V0.md](ORPHAN_SCHEDULER_AFTER_RUN_WITH_TIMEOUT_V0.md) — Orphan scheduler classification after bounded timeout (no auto-kill in doc)
- [BOUNDED_SCHEDULER_SINGLE_TICK_OPS_RUNBOOK_V0.md](BOUNDED_SCHEDULER_SINGLE_TICK_OPS_RUNBOOK_V0.md) — Bounded real-config scheduler: one dry-run tick on a `/tmp` copy (`run_scheduler_tick_once`; NO-LIVE)
- [DAEMON_PAPER_24H_PLUS_OBSERVATION_GATE_BEFORE_TESTNET_V0.md](DAEMON_PAPER_24H_PLUS_OBSERVATION_GATE_BEFORE_TESTNET_V0.md) — Gate runbook for planning a future 24h+ Daemon Paper-Observation before Testnet review (no start commands; prose only; not “demo”)
- [DAEMON_PAPER_24H_PLUS_OPERATOR_SCOPE_PREFLIGHT_V0.md](DAEMON_PAPER_24H_PLUS_OPERATOR_SCOPE_PREFLIGHT_V0.md) — Operator scope / preflight worksheet for a future Daemon 24h+ Paper-Test (decisions and checklist only; no commands)

### Preflight / Primary Evidence (blocked, read-only)

- [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](./PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) — **Canonical** Paper/Shadow 24/7 preflight contract (§2a / §2a.1 primary-evidence hard gate; **BLOCKED**; evidence ≠ approval; `PREFLIGHT_REMAINS_BLOCKED=true`)

### Preflight Taxonomy / Runtime Lanes (blocked, read-only)

- [RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md](../specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) — **Canonical** Runtime Lane Taxonomy + Authority Levels contract (§2 taxonomy index; **BLOCKED** lanes; evidence ≠ approval; `PREFLIGHT_REMAINS_BLOCKED=true`; `RUNTIME_LANE_TAXONOMY_FAIL_CLOSED=true`)

### Shadow-247 Governance / Activation Ladder (blocked, read-only)

- [SHADOW_247_GOVERNANCE_CHARTER_V0.md](./SHADOW_247_GOVERNANCE_CHARTER_V0.md) — **Canonical** Shadow-247 governance charter (activation ladder, operator/stop/evidence planning; **non-authorizing**; `PREFLIGHT_REMAINS_BLOCKED=true`; `STOP_IDLE_PRESERVED=true`; `SHADOW_247_GOVERNANCE_FAIL_CLOSED=true`)

### Evidence Durable Enforcement Readiness / GAP2A1 Planning (blocked, read-only)

- [CI_AUDIT — Evidence Durable Enforcement Readiness Review RC v0 — index v0](../CI_AUDIT_KNOWN_ISSUES.md) — **Canonical** EER1 enforcement-readiness review meta-index (consolidates Preflight §2b.2, SECTION5 §2a.1, and completed prerequisite RC arcs; **non-authorizing**; `GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false`; `ENFORCEMENT_ACTIVATED=false`; `PREFLIGHT_REMAINS_BLOCKED=true`; `EER1_ENFORCEMENT_READINESS_FAIL_CLOSED=true`)
- Preflight §2b.2 EER1 crosslink + §2a.1 primary-evidence hard gate (reuse — see **Preflight / Primary Evidence** above)
- [SECTION5 Preflight Gap Owner Map](../planning/SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md) — SECTION5 §2a.1 Gap-2a.1 + EER1 readiness review guard (reference only)

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

### Ops Cockpit (WebUI, read-only)

- [webui_ops_cockpit_v2_5_truth_first.md](./webui_ops_cockpit_v2_5_truth_first.md) — **Canonical** Ops Cockpit v2.5 truth-first operator runbook (`/ops`, `/api/ops-cockpit`; read-only; operator summary: [OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md](../specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md))

### Phase-Specific Workflows

Runbooks for specific phase implementations and workflows:

- [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) — **Bindende kanonische Steuerdatei** fuer den aktuellen Master-V2-First-Live-Enablement-Clarification-Workstream (Specs-Surface, kein Ausfuehrungs-Runbook)
- [RUNBOOK_TO_FINISH_MASTER.md](RUNBOOK_TO_FINISH_MASTER.md) — Master: docs-only Branch → PR → D2/D3/D4 DoD → SSoT „Finish“-Definition (NO‑LIVE)
- [RUNBOOK_CURSOR_MA_P4C_P6_P7CORE_P5B_2026-02-19.md](RUNBOOK_CURSOR_MA_P4C_P6_P7CORE_P5B_2026-02-19.md) — Cursor Multi-Agent: P4C (L2 Market Outlook) → P6 (Shadow) → P7 Core (Paper) → P5B (Evidence CI)
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
- [Phase U — Data Node Bootstrap (Ubuntu) + Hardening](PHASE_U_DATA_NODE_BOOTSTRAP.md) — Server bootstrap checklist, exporter skeleton, object storage template
- [Phase W — GitHub Consumer: Download + Verify Export Packs](PHASE_W_EXPORT_PACK_GH_CONSUMER.md) — rclone S3-compatible, read-only secrets

### Bounded Pilot & Live Pilot (governance-first)

- [RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) — **Bounded Pilot Live Entry** (Ist-Zustand Repo): Dry-Validation → Go/No-Go → `run_bounded_pilot_session` / `run_execution_session --mode bounded_pilot`
- [RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md](RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md) — Trockenvalidierung vor Real-Money-Pilot
- [live_pilot_execution_plan.md](live_pilot_execution_plan.md) — Gesamtplan inkl. Gates und Caps
- [live_pilot_kickoff.md](live_pilot_kickoff.md) — Kickoff (Pointer)

#### Bounded Pilot Incident / Triage (blocked, read-only)

- [RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md) — **Canonical** bounded-pilot incident / §5 abort triage compass (symptom routing → incident runbook, L5 evidence discipline; **non-authorizing**; `BOUNDED_PILOT_INCIDENT_NAVIGATION_FAIL_CLOSED=true`; `PILOT_GO_AUTHORIZED=false`; `PREFLIGHT_REMAINS_BLOCKED=true`)
- [RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md) — Exchange/broker API degraded (Row 11 doc-based evidence owner)
- [RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md) — Unexpected exposure / envelope doubt
- [RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md) — Reconciliation / ledger disagreement
- [RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md) — Session-end / closeout mismatch
- [RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md) — Transfer / funding ambiguity
- [RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md) — Telemetry / observability degraded
- [RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md) — Mid-session restart / continuity break (Row 10 doc-based evidence owner)

### Runbook B — Execution Gates (B5/B3/B2)

Safety controls for Shadow → Mini-Live (ArmedGate, RiskGate, Reconciliation). **All OFF by default.**

- [runbook_b_execution_gates_quickstart.md](runbook_b_execution_gates_quickstart.md) — Quickstart: env toggles, safe usage, config examples
- [runbook_b_env_example.txt](runbook_b_env_example.txt) — Minimal env example (all disabled)

### CI & Operations

Runbooks for CI operations and general operational procedures:

- [PR Ops v1 Runbook](../pr/pr_ops_v1_runbook.md) — PR watch, closeout, required-checks snapshot (generated via `p41 --with-pr-ops`)
- [RUNBOOK_MCP_TOOLING.md](RUNBOOK_MCP_TOOLING.md) — MCP Tooling (Cursor): Playwright + Grafana (read-only), Secret-Handling, Smoke/Preflight
- [RUNBOOK_AI_LIVE_OPS_LOCAL.md](RUNBOOK_AI_LIVE_OPS_LOCAL.md) — AI Live Ops Pack (local start/verify/troubleshoot; snapshot-only)
- [RUNBOOK_EXECUTION_WATCH_DEMO_STACK.md](RUNBOOK_EXECUTION_WATCH_DEMO_STACK.md) — Execution Watch Demo-Stack (shadow_mvs + ai_live; ersetzt entfernte Watch-Only-Dashboard-Operator-Runbooks; STRICT NO-LIVE)
- [RUNBOOK_SLICE_3_6_REPLAY_REGRESSION_PACK_OPERATOR_SHORTCUT.md](RUNBOOK_SLICE_3_6_REPLAY_REGRESSION_PACK_OPERATOR_SHORTCUT.md) — Slice 3.6: Offline deterministic replay regression pack shortcut (bundle → compare → consume)
- [RUNBOOK_PR736_CI_SNAPSHOT_AUTOMERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md](RUNBOOK_PR736_CI_SNAPSHOT_AUTOMERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md) — PR #736: CI snapshot → enable auto-merge → post-merge verify on main (snapshot-only)
- [LIVE_STATUS_PANELS.md](../../webui/LIVE_STATUS_PANELS.md) — Live-Status-Panels / read-only Web-Dashboard-UI (ersetzt das entfernte Watch-Only-Dashboard-Runbook v0.1B)
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
- [incident_stop_freeze_rollback.md](incident_stop_freeze_rollback.md) — operator flow for STOP / FREEZE / ROLLBACK incident handling
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

## Workflow Policy Docs

Policy-Dokumente für illustrative Pfade und Workflow-Konventionen (relevant für Docs-Gates):

- [WORKFLOW_NOTES_FRONTDOOR.md](../workflows/WORKFLOW_NOTES_FRONTDOOR.md) — Policy für `&#47;`-Encoding in Markdown
- [PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md](../workflows/PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md) — Historische Workflow-Notizen

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

**Last Updated:** 2026-05-11
**Maintainer:** ops

## Incident-stop / HOLD classification discoverability

For operator classification of incident-stop artifacts under `HOLD_NO_PAPER_RUN`, use
`docs/ops/runbooks/incident_stop_freeze_rollback.md` as the canonical runbook. It
clarifies the conservative classification vocabulary:

- `active`: keep `HOLD_NO_PAPER_RUN` active.
- `unknown`: keep `HOLD_NO_PAPER_RUN` active; this is not a clearance state.
- `stale_closed`: only after a human operator records this decision may the documented
  follow-up procedure be used before rerunning read-only snapshot/preflight checks.

Scheduler/preflight boundaries under HOLD are documented in `docs/SCHEDULER_DAEMON.md`.
These references are discoverability pointers only; they do not create a new readiness,
evidence, or go-live authorization surface.
