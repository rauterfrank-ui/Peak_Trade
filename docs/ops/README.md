# Peak_Trade – Ops Tools

Bash-Skripte und Tools für Repository-Verwaltung, Health-Checks und PR-Analyse im Peak_Trade Repository.

---

## Closeouts & Playbooks

### Wave Restore Tools
- **[RUNBOOK: Wave Restore](RUNBOOK_WAVE_RESTORE.md)** — Standardized runbook for restore waves (naming, gates, workflow, commands)
- **[Tool: wave_restore_status.sh](../../scripts/ops/wave_restore_status.sh)** — Dashboard for wave restore sessions (PR status, branches)
- **[Wave2 Restore Closeout](WAVE2_RESTORE_CLOSEOUT_20260106_214505Z.md)** — Wave2 session outcomes (PRs #579, #580, #571, #581, #582)

### Session Closeouts
- **[Phase 9C Closeout](graphs/PHASE9C_CLOSEOUT_2026-01-14.md)** — Docs Graph Remediation Waves 3–5 (114→39 broken targets, −65.8%, goal achieved)
- **[Session Closeout 2026-01-06](SESSION_CLOSEOUT_20260106_PEAK_TRADE_DOCS_OPS_INTEGRATION.md)** — Gap analysis & security fixes (PR #573, #574, #575, #576)
- **[Tools Peak Trade Gap Analysis](TOOLS_PEAK_TRADE_SCRIPTS_GAP_ANALYSIS.md)** — Comprehensive gap analysis (REJECT recommendation)

### PR Merge Logs & Closeouts

**Recent lifecycle notes (Strategien):**
- `prepare()` = Hook-only (nicht als externer Entry-Point gedacht)
- bevorzugter Entry-Point: `signals = strategy.run(data)`
- `run()` ruft `prepare_once(data)` auf und danach `generate_signals(data)`
- `prepare_once()` ist idempotent pro DataFrame-Objekt (Cache-Key: `id(data)`)
- Konsequenz: `df.copy()`/neues Objekt triggert `prepare()` erneut (gewollt)
- Source of Truth: [docs/STRATEGY_DEV_GUIDE.md](../STRATEGY_DEV_GUIDE.md)

- [merge_logs/PR_1037_MERGE_LOG.md](merge_logs/PR_1037_MERGE_LOG.md) — PR #1037 (docs(ops): finish tech-debt D evidence + backlog status) ([PR #1037](https://github.com/rauterfrank-ui/Peak_Trade/pull/1037), 2026-01-28)
- [merge_logs/PR_1051_MERGE_LOG.md](merge_logs/PR_1051_MERGE_LOG.md) — PR #1051 (docs(strategies): clarify prepare_once id(data) semantics) ([PR #1051](https://github.com/rauterfrank-ui/Peak_Trade/pull/1051), 2026-01-28)
- [merge_logs/PR_1048_MERGE_LOG.md](merge_logs/PR_1048_MERGE_LOG.md) — PR #1048 (test(strategies): assert prepare_once id(data) semantics via df.copy()) ([PR #1048](https://github.com/rauterfrank-ui/Peak_Trade/pull/1048), 2026-01-28)
- [merge_logs/PR_1046_MERGE_LOG.md](merge_logs/PR_1046_MERGE_LOG.md) — PR #1046 (docs(strategies): align guide examples with run() lifecycle) ([PR #1046](https://github.com/rauterfrank-ui/Peak_Trade/pull/1046), 2026-01-28)
- [merge_logs/PR_1044_MERGE_LOG.md](merge_logs/PR_1044_MERGE_LOG.md) — PR #1044 (docs(strategies): document run/prepare_once lifecycle + test idempotency) ([PR #1044](https://github.com/rauterfrank-ui/Peak_Trade/pull/1044), 2026-01-28)
- [merge_logs/PR_1043_MERGE_LOG.md](merge_logs/PR_1043_MERGE_LOG.md) — PR #1043 (docs(ops): add PR #1042 merge log) ([PR #1043](https://github.com/rauterfrank-ui/Peak_Trade/pull/1043), 2026-01-28)
- [merge_logs/PR_1042_MERGE_LOG.md](merge_logs/PR_1042_MERGE_LOG.md) — PR #1042 (docs(ops): add PR #1041 merge log) ([PR #1042](https://github.com/rauterfrank-ui/Peak_Trade/pull/1042), 2026-01-28)
- [merge_logs/PR_1041_MERGE_LOG.md](merge_logs/PR_1041_MERGE_LOG.md) — PR #1041 (docs(ops): add PR #1040 merge log) ([PR #1041](https://github.com/rauterfrank-ui/Peak_Trade/pull/1041), 2026-01-28)
- [merge_logs/PR_1040_MERGE_LOG.md](merge_logs/PR_1040_MERGE_LOG.md) — PR #1040 (docs(ops): add PR #1039 merge log) ([PR #1040](https://github.com/rauterfrank-ui/Peak_Trade/pull/1040), 2026-01-28)
- [merge_logs/PR_1039_MERGE_LOG.md](merge_logs/PR_1039_MERGE_LOG.md) — PR #1039 (docs(ops): add PR #1038 merge log) ([PR #1039](https://github.com/rauterfrank-ui/Peak_Trade/pull/1039), 2026-01-28)
- [merge_logs/PR_1038_MERGE_LOG.md](merge_logs/PR_1038_MERGE_LOG.md) — PR #1038 (docs(ops): Item D evidence pack + backlog status) ([PR #1038](https://github.com/rauterfrank-ui/Peak_Trade/pull/1038), 2026-01-28)
- [merge_logs/PR_1013_MERGE_LOG.md](merge_logs/PR_1013_MERGE_LOG.md) — PR #1013 (docs(ops): add PR #1012 merge log) ([PR #1013](https://github.com/rauterfrank-ui/Peak_Trade/pull/1013), 2026-01-27)
- [merge_logs/PR_1012_MERGE_LOG.md](merge_logs/PR_1012_MERGE_LOG.md) — PR #1012 (docs(ops): add PR 1011 merge log) ([PR #1012](https://github.com/rauterfrank-ui/Peak_Trade/pull/1012), 2026-01-27)
- [merge_logs/PR_1011_MERGE_LOG.md](merge_logs/PR_1011_MERGE_LOG.md) — PR #1011 (feat(learning-promotion): promotion loop v1 (runner + live overrides + docs finalizer)) ([PR #1011](https://github.com/rauterfrank-ui/Peak_Trade/pull/1011), 2026-01-27)
- [merge_logs/PR_994_MERGE_LOG.md](merge_logs/PR_994_MERGE_LOG.md) — PR #994 (ops(mcp): first-class Playwright/Grafana MCP tooling: preflight + runbook + CI signal) ([PR #994](https://github.com/rauterfrank-ui/Peak_Trade/pull/994), 2026-01-27)
- [merge_logs/PR_964_MERGE_LOG.md](merge_logs/PR_964_MERGE_LOG.md) — PR #964 (AI Live Ops Pack v1: alerts + Grafana ops summary + runbook) ([PR #964](https://github.com/rauterfrank-ui/Peak_Trade/pull/964), 2026-01-24)
- [merge_logs/PR_716_MERGE_LOG.md](merge_logs/PR_716_MERGE_LOG.md) — PR #716 (Phase 9C Wave 5: broken targets 58→39, goal achieved, 27 token policy violations fixed) ([PR #716](https://github.com/rauterfrank-ui/Peak_Trade/pull/716), 2026-01-14)
- [merge_logs/PR_714_MERGE_LOG.md](merge_logs/PR_714_MERGE_LOG.md) — PR #714 (Phase 9C Wave 4: broken targets 87→65, CI-Parity Guide) ([PR #714](https://github.com/rauterfrank-ui/Peak_Trade/pull/714), 2026-01-14)
- [merge_logs/PR_712_MERGE_LOG.md](merge_logs/PR_712_MERGE_LOG.md) — PR #712 (Phase 9C Wave 3: broken targets 114→89) ([PR #712](https://github.com/rauterfrank-ui/Peak_Trade/pull/712), 2026-01-14)
- **[Phase 5C Workflow Dispatch Guard Enforcement Closeout](PHASE5C_WORKFLOW_DISPATCH_GUARD_ENFORCEMENT_CLOSEOUT.md)** — Phase 5C closeout: dispatch-guard enforcement activation, 10 required checks, verified (2026-01-12)
- ``docs&#47;ops&#47;PR_693_MERGE_LOG.md`` — PR #693 (Docs Token Policy Gate: CI enforcement + tests + runbook + allowlist) ([PR #693](https://github.com/rauterfrank-ui/Peak_Trade/pull/693), 2026-01-13)
- ``docs&#47;ops&#47;PR_691_MERGE_LOG.md`` — PR #691 (Workflow notes integration + docs-reference-targets-gate policy formalization) ([PR #691](https://github.com/rauterfrank-ui/Peak_Trade/pull/691), 2026-01-13)
- ``docs&#47;ops&#47;PR_690_MERGE_LOG.md`` — PR #690 (Docs frontdoor + crosslink hardening + illustrative paths neutralization) ([PR #690](https://github.com/rauterfrank-ui/Peak_Trade/pull/690), 2026-01-13)
- ``docs&#47;ops&#47;PR_669_MERGE_LOG.md`` — PR #669 (Phase 5D Required Checks Hygiene Gate + dispatch-guard always-run proof) ([PR #669](https://github.com/rauterfrank-ui/Peak_Trade/pull/669), 2026-01-12)
- ``docs&#47;ops&#47;PR_664_MERGE_LOG.md`` — PR #664 (offline_suites workflow_dispatch input context fix) (PR #664, 2026-01-12)
- ``docs&#47;ops&#47;PR_663_MERGE_LOG.md`` — PR #663 (Phase 5B workflow dispatch condition fix) (PR #663, 2026-01-12)
- ``docs&#47;ops&#47;PR_653_MERGE_LOG.md`` — AI Autonomy Phase 4D: L4 Critic Determinism Contract + Validator + CI (PR #653, 2026-01-11)
- ``docs&#47;ops&#47;PR_651_MERGE_LOG.md`` — Merge Log for PR #650 (Merge Log for PR #649) (PR #651, 2026-01-11)
- ``docs&#47;ops&#47;PR_650_MERGE_LOG.md`` — Merge Log for PR #649 (Phase 4D Triage Docs) (PR #650, 2026-01-11)
- ``docs&#47;ops&#47;PR_649_MERGE_LOG.md`` — AI Autonomy Phase 4D: L4 Critic Determinism Triage Documentation (PR #649, 2026-01-11)
- ``docs&#47;ops&#47;PR_645_MERGE_LOG.md`` — AI Autonomy Phase 4C: L4 Critic Replay Determinism Hardening (PR #645, 2026-01-11)
- ``docs&#47;ops&#47;PR_643_MERGE_LOG.md`` — AI Autonomy Phase 4B: L4 Governance Critic Runner (PR #643, 2026-01-11)
- ``docs&#47;ops&#47;PR_640_MERGE_LOG.md`` — (PR #640, 2026-01-11)
- ``docs&#47;ops&#47;PR_642_MERGE_LOG.md`` — AI Autonomy Phase 4A: L1 DeepResearch Runner + Evidence Pack + Record/Replay (PR #642, 2026-01-10)
- ``docs&#47;ops&#47;PR_619_MERGE_LOG.md`` — AI Autonomy Phase 4B M2: Operator Runbook (Evidence-First Loop) (PR #619, 2026-01-09)
- ``docs&#47;ops&#47;PR_614_MERGE_LOG.md`` — AI Autonomy Phase 3B: Evidence Pack Validator (fail-closed, SoD enforced) (PR #614, 2026-01-08)
- ``docs&#47;ops&#47;PR_611_MERGE_LOG.md`` — AI Autonomy Phase 3A: Runtime Orchestrator v0 (fail-closed) (PR #611, 2026-01-08)
- ``docs&#47;ops&#47;PR_610_MERGE_LOG.md`` — AI Autonomy Phase 2: Capability Scopes + Model Registry (PR #610, 2026-01-08)
- ``docs&#47;ops&#47;PR_569_MERGE_LOG.md`` — MLflow CI Failures Fix: Run Lifecycle Hardening for mlflow≥3.0 (PR #569, 2026-01-05)
- ``docs&#47;ops&#47;PR_562_MERGE_LOG.md`` — AI-Ops Toolchain v1.1: Evals Runner + CI + Scoreboard (PR #562, 2026-01-05)
- ``docs&#47;ops&#47;PR_560_MERGE_LOG.md`` — Cursor Multi-Agent Integration V1 (PR #560, 2026-01-05)
- ``docs&#47;ops&#47;merge_logs&#47;20260104_pr-544_var-backtest-suite-phase-8c.md`` — Phase 8C: VaR Backtest Suite Runner & Report Formatter (PR #544, 2026-01-04)
- ``docs&#47;ops&#47;merge_logs&#47;2026-01-04_feat-var-backtest-christoffersen-cc_merge_log.md`` — Christoffersen VaR Backtests (PR #422, 2026-01-04)
- ``docs&#47;ops&#47;merge_logs&#47;2025-12-27_mass_docs_pr_closeout.md`` — Mass PR Wave Closeout (2025-12-27)
- ``docs&#47;ops&#47;CASCADING_MERGES_AND_RERERE_PLAYBOOK.md`` — Cascading merges & git rerere Operator Playbook

## Closeout Automation
- ``scripts&#47;ops&#47;run_closeout_2025_12_27.sh`` — Runner (Safety Gates + Auto-Merge Workflow)
- ``scripts&#47;ops&#47;create_closeout_2025_12_27.sh`` — Generator (Docs + PR scaffold)

## Cursor Multi-Agent Runbooks

**Quick Start:** Beginne mit der **Frontdoor** für Rollen, Task-Packets und Gates. Wähle dann deine **Phase** (0–7: Foundation → Live Operations) im Phasen-Runbook. Jede Session: erstelle ein **Runlog** aus dem Template. Die Frontdoor definiert *wie* wir liefern (Prozess), die Phasen definieren *was* wir liefern (Deliverables pro Phase).

**Navigation:**
- 🚪 **Start hier:** [CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md](CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md) — Rollen (A0–A5), Task-Packet-Format, PR-Contract, Gate-Index, Stop-Regeln
- 📋 **Phasen-Guide:** [CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md](CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md) — Phase 0 (Foundation) → Phase 7 (Continuous Ops); Entry/Exit Criteria, Deliverables, Operator How-To
- 📝 **Session Template:** [CURSOR_MULTI_AGENT_SESSION_RUNLOG_TEMPLATE.md](CURSOR_MULTI_AGENT_SESSION_RUNLOG_TEMPLATE.md) — Strukturiertes Log-Format für jede Multi-Agent Session
- 🔄 **Workflow-Definition:** [CURSOR_MULTI_AGENT_WORKFLOW.md](CURSOR_MULTI_AGENT_WORKFLOW.md) — Canonical Workflow (Roles, Protocol, Recovery)
- 🗺️ **Legacy Roadmap:** [CURSOR_MULTI_AGENT_PHASES_TO_LIVE.md](CURSOR_MULTI_AGENT_PHASES_TO_LIVE.md) — Älterer Phasen-Runbook (P0–P10), siehe Frontdoor + PHASES_V2 für aktuelle Version
- ``docs&#47;ops&#47;LIVE_READINESS_PHASE_TRACKER.md`` — Phase gates tracker (P0-P10: research → shadow → live)

## Workflow Documentation

**Quick Start:** Beginne mit der **[Workflow Frontdoor](../WORKFLOW_FRONTDOOR.md)** für zentrale Navigation zwischen autoritativer Operations-Referenz (2026) und historischem Chat-Workflow-Kontext (Dec 2025).

**Navigation:**
- 🚪 **Start hier:** [WORKFLOW_FRONTDOOR.md](../WORKFLOW_FRONTDOOR.md) — Central navigation hub for workflow and runbook documentation
- 📘 **Authoritative (2026):** [WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md](../../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md) — Comprehensive operational reference: 18+ CLI sections, 12+ runbooks, Wave3 Control Center, AI Autonomy cheatsheet, 5 checklists, status tables
- 📙 **Legacy (Dec 2025):** [WORKFLOW_NOTES.md](../WORKFLOW_NOTES.md) — Historical snapshot: Technical layer status, Frank/ChatGPT/Claude workflow mechanics, prompt style conventions
- 📁 **Workflow Notes Archive:** [workflows/](workflows/) — Consolidated workflow notes with docs-reference-targets-gate compliance
  - [WORKFLOW_NOTES_FRONTDOOR.md](workflows/WORKFLOW_NOTES_FRONTDOOR.md) — Policy guide for illustrative path encoding
  - [PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md](workflows/PEAK_TRADE_WORKFLOW_NOTES_2025-12-03.md) — Historical workflow snapshot

**When to Use:**
- **Daily Operations:** WORKFLOW_RUNBOOK_OVERVIEW (authoritative, current)
- **CLI Command Lookup:** WORKFLOW_RUNBOOK_OVERVIEW Section 9 + [CLI_CHEATSHEET.md](../CLI_CHEATSHEET.md)
- **PR Management (Wave3):** WORKFLOW_RUNBOOK_OVERVIEW Section 2
- **Historical Context:** WORKFLOW_NOTES (legacy, Dec 2025 technical snapshot)
- **Chat-Based Development:** WORKFLOW_NOTES (continuation context for Frank/ChatGPT/Claude sessions)
- **Docs Gate Policy:** workflows/WORKFLOW_NOTES_FRONTDOOR.md (illustrative path encoding guide)

## Installation & Setup

- [Installation Quickstart](../INSTALLATION_QUICKSTART.md)
- [Installation & Roadmap Snapshot (2026-01-12)](../../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md)

### Phase 5 NO-LIVE Drill Pack (Governance-Safe, Manual-Only)

🚨 **NO-LIVE / Drill-Only** — Kein Live Trading, keine realen Funds, keine Exchange Connectivity

**WP5A — Phase 5 NO-LIVE Drill Pack:**
- 📖 **Operator Runbook:** [WP5A_PHASE5_NO_LIVE_DRILL_PACK.md](WP5A_PHASE5_NO_LIVE_DRILL_PACK.md) — End-to-End Workflow für NO-LIVE Operator Drills (5-Step Procedure, Evidence Pack, Hard Prohibitions)

**Templates (Phase 5 NO-LIVE):**
- 📋 Operator Checklist: [templates/phase5_no_live/PHASE5_NO_LIVE_OPERATOR_CHECKLIST.md](templates/phase5_no_live/PHASE5_NO_LIVE_OPERATOR_CHECKLIST.md)
- ✅ Go/No-Go Record: [templates/phase5_no_live/PHASE5_NO_LIVE_GO_NO_GO_RECORD.md](templates/phase5_no_live/PHASE5_NO_LIVE_GO_NO_GO_RECORD.md)
- 📦 Evidence Index: [templates/phase5_no_live/PHASE5_NO_LIVE_EVIDENCE_INDEX.md](templates/phase5_no_live/PHASE5_NO_LIVE_EVIDENCE_INDEX.md)
- 📝 Post-Run Review: [templates/phase5_no_live/PHASE5_NO_LIVE_POST_RUN_REVIEW.md](templates/phase5_no_live/PHASE5_NO_LIVE_POST_RUN_REVIEW.md)

**Key Deliverables:**
- NO-LIVE Enforcement (Shadow/Paper/Drill-Only modes)
- Hard Prohibitions (keys, funding, real orders verboten)
- Operator Competency Validation (drill-safe)
- Governance-Safe Evidence Chain (GO ≠ Live Authorization)

### Phase 5A: Normalized Report Consumer + Trend Seed

🔄 **CI Artifact Consumption → Trend Seed Generation** — Tooling-only, deterministic, schema-versioned

**Phase 5A Runbook:**
- 📖 **Cursor Multi-Agent Runbook:** [RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md](runbooks/RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md) — Standardized workflow for consuming Phase 4E normalized validator reports and generating deterministic Trend Seeds (6-role multi-agent orchestration: ORCHESTRATOR, FACTS_COLLECTOR, SCOPE_KEEPER, CI_GUARDIAN, EVIDENCE_SCRIBE, RISK_OFFICER)

**Key Deliverables:**
- Trend Seed Schema v0.1.0 (minimal, append-only mindset)
- Consumer with fail-closed behavior (schema mismatch → hard fail)
- Deterministic output (stable JSON, sorted keys, no secrets)
- CI integration (artifact download → consumer → upload Trend Seed)
- Operator Notes template for PR/run documentation

**Risk:** LOW (tooling + artifacts only, no trading code, no live execution)

### Phase 5B: Trend Ledger from Seed

📊 **Trend Seed → Canonical Ledger Snapshot** — Deterministic aggregation, artifact persistence

**Phase 5B Runbooks:**
- 📖 **Cursor Multi-Agent Runbook (FULL):** [RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED_CURSOR_MULTI_AGENT.md](runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED_CURSOR_MULTI_AGENT.md) — Standardized multi-agent workflow for Phase 5B FULL implementation (ORCHESTRATOR, FACTS_COLLECTOR, SCOPE_KEEPER, IMPLEMENTER, TEST_ENGINEER, CI_GUARDIAN, DOCS_SCRIBE, RISK_OFFICER) with determinism-first design + CI workflow
- 📖 **Operator Runbook:** [RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md](runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md) — Standardized workflow for consuming Phase 5A Trend Seeds and generating canonical Trend Ledger snapshots with deterministic JSON, markdown summaries, and CI artifact integration

**Key Deliverables:**
- Trend Ledger Schema v0.1.0 (canonical ordering, stable items[], counters)
- Consumer with fail-closed validation (missing fields → hard fail)
- Deterministic serialization (sorted keys, byte-identical output)
- CI workflow (downloads Phase 5A seed → generates ledger → uploads artifacts)
- Markdown summary for operator visibility

**Risk:** LOW (tooling/CI artifacts only, no trading code, no live execution)

### AI Autonomy Phase 4B Milestone 2 (Evidence-First Operator Loop)

🤖 **Cursor Multi-Agent Orchestration** — Evidence Pack + CI Gates + Operator Review

**Phase 4B M2 — Multi-Agent Runbook:**
- 📖 **Operator Runbook:** [runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md) — Standardized workflow for AI Autonomy Layer Runs with Evidence Pack creation, validation, and operator sign-off
- 🎯 **Operator Drill Pack:** [drills/OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md](drills/OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md) — 8 structured drills for operator competency validation (Pre-Flight, Scope Lock, Evidence Pack, CI Gates, Auto-Merge, Incidents, Closeout)
- 📝 **Drill Session Template:** [drills/SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md](drills/SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md) — Standardized template for drill session documentation (metadata, execution log, scorecard, findings)
- 📂 **Drill Runs Guide:** [drills/runs/README.md](drills/runs/README.md) — Guidelines for drill run logs (naming convention, quality checklist, evidence-first documentation)

**Key Deliverables:**
- Evidence-First: All runs documented in Evidence Packs
- CI-Validated: Schema validation + Docs gates + Audit gates
- Multi-Agent Roles: ORCHESTRATOR, FACTS_COLLECTOR, SCOPE_KEEPER, CI_GUARDIAN, EVIDENCE_SCRIBE, RISK_OFFICER
- Governance-Locked: No-live enforcement, SoD checks, deterministic outputs
- Operator Training: Structured drill pack for systematic competency validation

### AI Autonomy Phase 4B Milestone 3 (Control Center Dashboard/Visual)

🎛️ **Control Center + Enhanced Orchestration** — Dashboard + Extended Gates + Policy Checks

**Phase 4B M3 — Control Center Runbooks:**
- 📖 **Development Runbook:** [runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CURSOR_CONTROL_CENTER.md](runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CURSOR_CONTROL_CENTER.md) — Standardized workflow for Control Center Dashboard development and M3 orchestration enhancements (Status/Evidence/CI overview, deterministic rendering, docs-only defaults)
- 📖 **Dashboard Operations Runbook:** [runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md](runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md) — Local dashboard viewing, PR/CI monitoring without --watch (timeout-safe), evidence capture and closeout
- 📖 **Incident Triage Runbook:** [runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_INCIDENT_TRIAGE.md](runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_INCIDENT_TRIAGE.md) — Standardized incident detection, triage, evidence capture and escalation workflow for Control Center operations (severity levels, gate-specific shortcuts, timeout-safe monitoring)
- 📖 **Operator Cheatsheet:** [runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATOR_CHEATSHEET.md](runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATOR_CHEATSHEET.md) — Quick reference for daily Control Center operations (5-10 minute routine, triage shortcuts, evidence minimum)

**Key Deliverables:**
- Control Center Dashboard: Status/Evidence/CI/Run overview (static HTML or Markdown)
- Extended Orchestration: Enhanced gates, policy checks, capability scopes
- Evidence-First: Same M2 guarantees (Evidence Pack, CI validation, operator sign-off)
- Dashboard Modes: Static HTML (no runtime) / Markdown (docs-only) / Local dev server (optional)
- Timeout-Safe Monitoring: No-watch polling patterns for PR/CI checks

## AI Autonomy Control Center

- 🎛️ **Control Center (v0.1):** [AI_AUTONOMY_CONTROL_CENTER.md](control_center/AI_AUTONOMY_CONTROL_CENTER.md) — Dashboard, layer matrix, KPIs, operator quick actions
- 📖 **Operations Runbook (v0.1):** [RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md](runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md) — Daily routine, layer triage, CI gates, troubleshooting
- 🧭 **Navigation:** [CONTROL_CENTER_NAV.md](control_center/CONTROL_CENTER_NAV.md) — All key paths and runbooks

### Terminal Hang Diagnostics (Pager / Hook / Watch Blocking)

**Quick Diagnosis Tool:**
```bash
scripts/ops/diag_terminal_hang.sh
```

**Was wird geprüft:**
- Pager-Environment (PAGER, GH_PAGER, LESS)
- Aktive Prozesse: less, git, gh, pre-commit, python
- Shell/TTY Status und File Descriptors
- Diagnose-Checkliste mit Quick Actions

**Runbooks:**
- **[PAGER_HOOK_HANG_TRIAGE.md](PAGER_HOOK_HANG_TRIAGE.md)** — Operator Runbook mit 5 häufigen Ursachen + Lösungen
- **[TERMINAL_HANG_DIAGNOSTICS_SETUP.md](TERMINAL_HANG_DIAGNOSTICS_SETUP.md)** — Investigation Timeline + Setup-Dokumentation

**Häufige Symptome:**
- Terminal "steht", keine neue Prompt
- Prompt zeigt `>`, `dquote>` oder `quote>` (heredoc/quote nicht geschlossen)
- Keine Ausgabe, kein Fehler, kein CPU-Load

**Quick Fixes:**
- Pager wartet: `q` drücken
- Prozess läuft: `Ctrl-C`
- Heredoc offen: `Ctrl-C`
- Background Job: `fg` dann `Ctrl-C`

**Environment Setup (empfohlen):**
```bash
# In ~/.zshrc oder ~/.bashrc:
export PAGER=cat
export GH_PAGER=cat
export LESS='-FRX'
```

### Cursor Timeout / Hang Triage (Advanced)
- Wenn dein Terminal-Prompt `>` oder `dquote>` zeigt: **Ctrl-C** drücken (Shell-Continuation beenden), dann erneut.
- Runbook öffnen: ``docs&#47;ops&#47;CURSOR_TIMEOUT_TRIAGE.md``
- Evidence Pack erzeugen (funktioniert auch ohne +x):
  - ``bash scripts&#47;ops&#47;collect_cursor_logs.sh``
  - Output: ``artifacts&#47;cursor_logs_YYYYMMDD_HHMMSS.tgz``
- Optional (bei harten Hangs): In der Runbook-Sektion "Advanced Diagnostics (macOS)" die Schritte `sample`, `spindump`, `fs_usage` nutzen (sudo + Privacy beachten).
- Privacy: Logs/Snapshots vor externem Sharing auf sensitive Daten prüfen.

---

## 🎯 Ops Operator Center – Zentraler Einstiegspunkt

**Ein Command für alle Operator-Workflows.**

```bash
# Quick Start
scripts/ops/ops_center.sh status
scripts/ops/ops_center.sh pr 263
scripts/ops/ops_center.sh doctor
scripts/ops/ops_center.sh merge-log
```

### PR Full Workflow Runbook

Für einen vollständigen Ablauf von PR-Erstellung bis Merge und Verifikation steht jetzt ein detailliertes Runbook zur Verfügung. Siehe [OPS_OPERATOR_CENTER.md](OPS_OPERATOR_CENTER.md) ⭐

**Commands:**
- `status` — Repository-Status (git + gh)
- `pr <NUM>` — PR reviewen (safe, kein Merge)
- `doctor` — Health-Checks
- `audit` — Full Security & Quality Audit
- `merge-log` — Merge-Log Quick Reference
- `help` — Hilfe

**Design:** Safe-by-default, robust, konsistent.

---

## 🔒 Full Security & Quality Audit

**Umfassendes Audit-System für Security-Scanning, Dependency-Checks und Code-Qualität.**

### Quick Start

```bash
# Manuelles Audit ausführen
scripts/ops/ops_center.sh audit

# Oder direkt
./scripts/ops/run_full_audit.sh
```

### Was wird geprüft?

1. **Security Scanning** (`pip-audit`)
   - Scannt alle installierten Packages auf bekannte Vulnerabilities (CVEs)
   - Nutzt PyPI Advisory Database
   - Blockiert bei Findings (Exit != 0)

2. **SBOM Export** (Software Bill of Materials)
   - CycloneDX 1.5 Format
   - Vollständige Dependency-Liste mit Versionen und Hashes
   - Für Supply Chain Security & Compliance-Audits

3. **Repo Health** (`ops_center.sh doctor`)
   - Git-Status, Config-Validierung
   - Docs-Integrität, CI-Setup

4. **Code Quality**
   - `ruff format --check` (Format-Compliance)
   - `ruff check` (Linting)

5. **Test Suite**
   - `pytest -q` (Quick-Run aller Tests)

### Output & Artefakte

Alle Audit-Runs erzeugen versionierte Artefakte:

```
reports/audit/YYYYMMDD_HHMMSS/
├── full_audit.log    # Vollständiges Audit-Log
└── sbom.json         # Software Bill of Materials (CycloneDX 1.5)
```

**SBOM Use Cases:**
- Supply Chain Security: Identifikation aller Dependencies
- Compliance: SBOM-Anforderungen (z.B. Executive Order 14028)
- Vulnerability Tracking: Schnelle Prüfung ob betroffene Packages im Einsatz sind

### Knowledge DB In-Memory Fallback (Dev/Prod Hardening)

**Config Flag:** `WEBUI_KNOWLEDGE_ALLOW_FALLBACK`

Die Knowledge Service API kann mit oder ohne ChromaDB (Vector DB) laufen:

- **Dev/Test (Default):** `WEBUI_KNOWLEDGE_ALLOW_FALLBACK=true`
  - In-Memory Fallback aktiv wenn chromadb fehlt
  - API liefert 200/201 mit einfachem Keyword-Matching
  - **Use Case:** CI/lokale Dev ohne chromadb-Installation

- **Prod (Hardening):** `WEBUI_KNOWLEDGE_ALLOW_FALLBACK=false`
  - Kein Fallback erlaubt
  - API liefert **503 Service Unavailable** wenn chromadb fehlt
  - **Use Case:** Prod-Env wo Vector Search explizit required ist

**Empfehlung:**
- Dev/CI: Fallback enabled (Convenience)
- Prod: Fallback disabled + chromadb explizit installiert (Qualität)

### CI Integration

**Automatisches Weekly Audit:**
- Workflow: ``.github&#47;workflows&#47;full_audit_weekly.yml``
- Schedule: Montags 06:00 UTC
- Manueller Trigger: `workflow_dispatch`
- Artifacts: 90 Tage (SBOM: 365 Tage)

**Failure-Verhalten:**
- Hard Fail bei pip-audit findings
- Hard Fail bei Lint-Errors
- Hard Fail bei Test-Failures

**Optional: ChromaDB Extras Workflow:**
- Workflow: ``.github&#47;workflows&#47;knowledge_extras_chromadb.yml``
- Trigger: Jeden Montag 06:30 UTC + manuell via `workflow_dispatch`
- **Zweck:** Zusätzliches Signal für chromadb-backed Knowledge DB Tests
- **Status:** NICHT required für Merge (optional extra validation)
- Installiert chromadb und führt ``tests&#47;test_knowledge_readonly_gating.py`` aus

### Troubleshooting

**Q: Audit failed - wo finde ich Details?**
```bash
# Letztes Audit-Log finden
ls -lt reports/audit/ | head -5

# Log lesen
tail -100 reports/audit/TIMESTAMP/full_audit.log
```

**Q: SBOM für Compliance-Check benötigt?**
```bash
# Letztes SBOM exportieren
ls -t reports/audit/**/sbom.json | head -1
```

**Q: Nur Security-Scan ohne Tests?**
```bash
# pip-audit direkt ausführen
pip-audit --desc
```

---

## 📊 Risk Analytics – Component VaR Reporting

**Operator-Reports für Component VaR Analyse (Phase 2A)**

```bash
# Quick Start mit Fixtures
scripts/ops/ops_center.sh risk component-var --use-fixtures

# Mit eigenen Daten
scripts/ops/ops_center.sh risk component-var --returns data.csv --alpha 0.99
```

**Output:** HTML + JSON + CSV Reports in ``results&#47;risk&#47;component_var&#47;<run_id>&#47;``

**Dokumentation:** [../risk/COMPONENT_VAR_PHASE2A_REPORTING.md](../risk/COMPONENT_VAR_PHASE2A_REPORTING.md) ⭐

**Features:**
- Multi-Format Output (HTML/JSON/CSV)
- Automatische Sanity Checks (Euler property, weights normalization)
- Top-Contributors-Analyse
- Deterministisch und reproduzierbar

---

## 🎭 Shadow Pipeline – Data Quality & OHLCV

**Shadow Pipeline Phase 2: Tick→OHLCV→Quality Monitoring**

```bash
# Quick Smoke Test
scripts/ops/ops_center.sh shadow smoke

# Direct Execution
python3 scripts/shadow_run_tick_to_ohlcv_smoke.py

# Run Tests
python3 -m pytest tests/data/shadow/ -q
```

**Features:**
- Tick Normalization (Kraken WebSocket → standardized ticks)
- OHLCV Bar Building (1m/5m/1h aggregation)
- Data Quality Monitoring (gap detection, spike alerts)
- Defense-in-depth Guards (Import, Runtime, Config)

**Dokumentation:**
- **Quickstart:** [../shadow/SHADOW_PIPELINE_PHASE2_QUICKSTART.md](../shadow/SHADOW_PIPELINE_PHASE2_QUICKSTART.md) ⭐
- **Operator Runbook:** [../shadow/SHADOW_PIPELINE_PHASE2_OPERATOR_RUNBOOK.md](../shadow/SHADOW_PIPELINE_PHASE2_OPERATOR_RUNBOOK.md)
- **Technical Spec:** [../shadow/PHASE_2_TICK_TO_OHLCV_AND_QUALITY.md](../shadow/PHASE_2_TICK_TO_OHLCV_AND_QUALITY.md)
- **Config Example:** ``config&#47;shadow_pipeline_example.toml``

**Safety:** Shadow pipeline is blocked when live mode is active. Safe for dev/testnet contexts only.

---

## 🏥 Ops Doctor – Repository Health Check

Umfassendes Diagnose-Tool für Repository-Health-Checks mit strukturiertem JSON- und Human-Readable-Output.

### Quick Start

## 🎛️ CI & Governance Health Panel (WebUI v0.2)

**Offline-fähiges Dashboard für CI & Governance Health Monitoring mit persistenten Snapshots und interaktiven Controls.**

### Features

- ✅ **Persistent Snapshots:** JSON + Markdown snapshots bei jedem Status-Call (``reports&#47;ops&#47;ci_health_latest.{json,md}``)
- ✅ **Interactive Controls:** "Run checks now" Button, "Refresh status" Button, Auto-refresh (15s toggle)
- ✅ **Offline-fähig:** Snapshots bleiben verfügbar auch wenn WebUI offline ist
- ✅ **Concurrency-safe:** In-memory lock verhindert parallele Runs (HTTP 409 bei Konflikt)
- ✅ **XSS-protected:** HTML escaping für alle dynamischen Inhalte

### Quick Start

```bash
# Start WebUI
uvicorn src.webui.app:app --host 127.0.0.1 --port 8000

# Open Dashboard
open http://127.0.0.1:8000/ops/ci-health

# View persistent snapshot (offline)
cat reports/ops/ci_health_latest.md
jq '.overall_status, .summary' reports/ops/ci_health_latest.json
```

### API Endpoints

- ``GET &#47;ops&#47;ci-health`` — HTML Dashboard (interaktive UI)
- ``GET &#47;ops&#47;ci-health&#47;status`` — JSON Status + Snapshot-Persistenz
- ``POST &#47;ops&#47;ci-health&#47;run`` — Trigger manual check run (idempotent mit lock)

### Operator How-To

**Trigger Manual Check:**
- Open: ``http:&#47;&#47;127.0.0.1:8000&#47;ops&#47;ci-health``
- Click: "▶️ Run checks now"
- Observe: "⏳ Running..." → UI updates ohne page reload

**Enable Auto-Refresh:**
- Toggle: "Auto-refresh (15s)" checkbox
- Dashboard aktualisiert sich automatisch alle 15 Sekunden

**View Offline Status:**
```bash
# Human-readable summary (10-20 Zeilen)
cat reports/ops/ci_health_latest.md

# Machine-readable (full detail)
jq . reports/ops/ci_health_latest.json
```

### Documentation

- **v0.2 Snapshots:** [PR_518_CI_HEALTH_PANEL_V0_2.md](PR_518_CI_HEALTH_PANEL_V0_2.md) — Persistent snapshot feature
- **v0.2 Buttons:** [PR_519_CI_HEALTH_BUTTONS_V0_2.md](PR_519_CI_HEALTH_BUTTONS_V0_2.md) — Interactive controls + auto-refresh
- **Smoke Test:** ``scripts&#47;ops&#47;smoke_ci_health_panel_v0_2.sh`` — Quick validation script

### Checks Performed

- **Contract Guard:** Prüft required CI contexts (via `check_required_ci_contexts_present.sh`)
- **Docs Reference Validation:** Validiert Docs-Referenzen (via `verify_docs_reference_targets.sh`)

### Risk

**Low.** Keine externen API-Calls, keine Secrets benötigt, ausschließlich lokale Checks. Snapshots sind deterministische Runtime-Artefakte (gitignored). In-memory Lock verhindert Race Conditions. Error isolation: Snapshot-Fehler failen API nicht.

---

## Docs Diff Guard (auto beim Merge)

### Required Checks Drift Guard (v1)

- Operator Notes: ``docs&#47;ops&#47;REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md``
- Quick Commands:
  - ``scripts&#47;ops&#47;verify_required_checks_drift.sh`` (offline)
  - ``scripts&#47;ops&#47;ops_center.sh doctor`` → zeigt Drift-Guard/Health-Status (falls eingebunden)

### Workflow Dispatch Guard (Required Check — Phase 5C)

**Status:** ⚠️ **NOT ACTIVE** (Operator action required to add as required check for `main`)

**Purpose:** Prevents `workflow_dispatch` input context regressions (like PR #663, #664).

**Expected Check Context:** ``CI &#47; Workflow Dispatch Guard &#47; dispatch-guard``

**Current State:** Guard is functional and path-filtered, but the check is **not** present in `main` required checks (verified **2026-01-12**).

**Evidence:** ``docs&#47;ops&#47;ci&#47;evidence&#47;PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md``

**Activation (Operator):**
- GitHub → Settings → Branches → Branch protection rules → `main` → **Add required check**: ``CI &#47; Workflow Dispatch Guard &#47; dispatch-guard``
- (Alternative) GitHub → Settings → Rules → Rulesets → `main` ruleset → **Require status checks** → add the same check context

**Quick Commands:**
```bash
# Local validation
python3 scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows --fail-on-warn

# Run tests
python3 -m pytest -q tests/ops/test_validate_workflow_dispatch_guards.py
```

**Documentation:**
- **User Guide:** [docs/ops/ci/WORKFLOW_DISPATCH_GUARD.md](ci/WORKFLOW_DISPATCH_GUARD.md)
- **Enforcement Policy:** [docs/ops/ci/WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md](ci/WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md)
- **GitHub Settings Guide:** [docs/ops/ci/WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md](ci/WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md)
- **Script:** ``scripts&#47;ops&#47;validate_workflow_dispatch_guards.py``
- **CI Workflow:** ``.github&#47;workflows&#47;ci-workflow-dispatch-guard.yml``

**Burn-in Results:**
- Deployed: 2026-01-12
- First Run: Found real bug (PR #664: `offline_suites.yml`)
- False Positive Rate: 0% (0/1)
- True Positive Rate: 100% (1/1)

**Bypass Policy:** Admin-only, requires audit comment in PR (when active).

### Required Checks Hygiene Gate Operations (Phase 5E)

**Operator Runbook für standardisierte Wartung und Änderung von Required Status Checks (Branch Protection).**

**Purpose:** Verhindert "absent check" Szenarien, hält Repo-Quelle der Wahrheit (``config&#47;ci&#47;required_status_checks.json``) synchron mit Branch Protection, standardisiert Evidence-first + Rollback-ready Workflows.

**Runbook:** [RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE_OPERATIONS.md](runbooks/RUNBOOK_PHASE5E_REQUIRED_CHECKS_HYGIENE_GATE_OPERATIONS.md)

**Key Features:**
- ✅ Pre-Flight Checks (Scope/Necessity/Admin-Requirements)
- ✅ Discovery & Truth Capture (Evidence-first)
- ✅ Change Planning (absent-check prevention)
- ✅ PR-based Execution (Audit Trail)
- ✅ Validation Checklist (CI + Policy)
- ✅ Break-Glass / Rollback (Admin-only, time-limited)
- ✅ Operator Templates (PR Description + Evidence Entry)
- ✅ Failure Modes & Triage (merge blocked, mismatch)

**Source of Truth:**
- Expected contexts: ``config&#47;ci&#47;required_status_checks.json``
- Validator: ``scripts&#47;ci&#47;validate_required_checks_hygiene.py``
- Tests: ``tests&#47;ci&#47;test_required_checks_hygiene.py``
- Workflow: ``.github&#47;workflows&#47;required-checks-hygiene-gate.yml``

**Scope:** Ops / CI Governance / Branch Protection Hygiene (docs-only, operational impact HIGH if misused)

### Docs Navigation Health (Link Guard)

**Zweck:** Verhindert kaputte interne Links und Anchors in der Ops-Dokumentation, Root README und Status Overview.

**Quick Start:**
```bash
# Standalone Check
scripts/ops/check_ops_docs_navigation.sh

# Als Teil von ops doctor
scripts/ops/ops_center.sh doctor
```

**Features:**
- Prüft interne Markdown-Links (Format: `[text]\(path\)`) auf existierende Zieldateien
- Validiert Anchor-Links (Format: `[text]\(file.md#heading\)`) gegen tatsächliche Überschriften
- Ignoriert externe Links (http://, https://, mailto:)
- Schnell und offline (keine Netzwerk-Anfragen)

**Scope:** `README.md`, ``docs&#47;ops&#47;*``, ``docs&#47;PEAK_TRADE_STATUS_OVERVIEW.md``

**Tip:** Vor großen Docs-Refactorings einmal laufen lassen, um kaputte Links zu vermeiden.

### Docs Reference Targets Gate

**Zweck:** Validiert, dass alle referenzierten Repo-Pfade in Markdown-Docs (Config/Scripts/Docs) tatsächlich existieren.

**Related:** [Docs Token Policy Gate](#docs-token-policy-gate) — Enforces `&#47;` encoding for illustrative paths (prevents false positives in this gate)

**Quick Start (Empfohlene Nutzung):**
```bash
# Primary: CI Parity Check (nur geänderte Markdown-Dateien) ← STANDARD
scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main

# Optional: Full-Scan Audit (alle Docs, mit Ignore-Patterns für Legacy)
scripts/ops/verify_docs_reference_targets.sh

# Als Teil von ops doctor (warn-only)
scripts/ops/ops_center.sh doctor
```

**Features:**
- Findet referenzierte Pfade in Markdown-Links (`[text]\(path\)`), Inline-Code (`` `path` ``), und Bare-Pfaden
- Validiert Existenz von: ``config&#47;*.toml``, ``docs&#47;*.md``, ``scripts&#47;*.sh``, ``src&#47;*.py``, ``.github&#47;*.yml``
- Ignoriert externe URLs (http/https) und Anchor-Only-Links
- **Ignore-Patterns:** Full-Scan respektiert ``docs&#47;ops&#47;DOCS_REFERENCE_TARGETS_IGNORE.txt`` (Legacy/Archive-Bereiche)
- Exit 0 = OK/nicht anwendbar, Exit 1 = FAIL (CI), Exit 2 = WARN (ops doctor)

**Check Modes:**
1. **CI Parity Mode (Primary):** ``--changed --base origin&#47;main``
   - Validiert nur geänderte Dateien (entspricht CI-Verhalten)
   - Keine Ignore-Patterns (strikte Validierung)
   - Exit 0 = PASS, Exit 1 = FAIL
   - **Nutzung:** Vor Commit, vor PR-Push, bei lokalen Docs-Änderungen

2. **Full-Scan Audit (Optional):** ohne `--changed` Flag
   - Validiert alle Docs (inkl. Legacy)
   - Respektiert Ignore-Patterns aus ``docs&#47;ops&#47;DOCS_REFERENCE_TARGETS_IGNORE.txt``
   - Exit 1 = "PASS-with-notes" (Legacy-Content erwartet Broken-Refs)
   - **Nutzung:** Periodische Audits, Docs-Cleanup-Sessions

**CI Integration:**
- Läuft automatisch bei PRs via ``.github&#47;workflows&#47;docs_reference_targets_gate.yml``
- Exit 0 wenn keine Markdown-Dateien geändert wurden (not applicable)
- Exit 1 bei fehlenden Targets (blockiert Merge)
- CI nutzt immer `--changed` Mode (keine Ignore-Patterns)

**Scope:** Alle `*.md` Dateien (im --changed Mode: nur geänderte Dateien)

**Use Case:** Verhindert kaputte Referenzen z.B. nach Datei-Umbenennungen oder -Verschiebungen.

**Safe Markdown Guide:** [guides/DOCS_REFERENCE_TARGETS_SAFE_MARKDOWN.md](guides/DOCS_REFERENCE_TARGETS_SAFE_MARKDOWN.md) — Operator guide for avoiding false positives (branch names, planned files, CI triage checklist)

### Docs Gates — Operator Pack

**Overview:** Three CI gates enforce docs quality and prevent common errors:

1. **Docs Token Policy Gate** — Encoding policy for inline-code tokens
2. **Docs Reference Targets Gate** — Path existence validation
3. **Docs Diff Guard Policy Gate** — Policy marker enforcement

**🚀 Quick Start (60 Seconds):**

```bash
# Reproduce all 3 gates locally (PR workflow)
./scripts/ops/pt_docs_gates_snapshot.sh --changed

# Full repo audit
./scripts/ops/pt_docs_gates_snapshot.sh --all
```

**📘 Quick Reference:**
- **[RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md](runbooks/RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md)** ⭐ — **START HERE:** Single-page quick reference for all 3 gates (60-second workflow, common fixes, decision tree)

**📚 Detailed Operator Runbooks (400+ lines each):**
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md) — Token Policy Gate comprehensive guide
- [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md) — Reference Targets Gate comprehensive guide
- [RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md](runbooks/RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md) — Diff Guard Policy Gate comprehensive guide
- [RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md](runbooks/RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md) — Diff Guard Policy Gate quick reference

**🛠️ Helper Script:**
- ``scripts&#47;ops&#47;pt_docs_gates_snapshot.sh`` — Snapshot-only reproduction helper (no watch loops)

**🔔 Optional CI Signal:**
- **PR Merge State Signal** (`.github&#47;workflows&#47;ci-pr-merge-state-signal.yml`) — Informational-only workflow that shows BEHIND status in PR checks (never required, always SUCCESS)
  - **Purpose:** Early visibility when branch is behind main
  - **Output:** Job Summary with sync instructions
  - **Status:** Non-blocking (informational only)

**When Any Gate Fails:**
1. Run snapshot helper: `.&#47;scripts&#47;ops&#47;pt_docs_gates_snapshot.sh --changed`
2. Follow "Next Actions" in output
3. Consult relevant operator runbook
4. Re-run to verify fix

**When PR is BEHIND main:**
1. Check "PR Merge State Signal" job summary for sync instructions
2. Merge or rebase main into your branch
3. Re-run snapshot helper to validate after sync

---

### Docs Token Policy Gate

**Zweck:** Enforces `&#47;` encoding policy für illustrative Pfade in Markdown inline-code tokens (prevents `docs-reference-targets-gate` false positives).

**Status:** Active (non-required, informational gate with 30-day burn-in period)

**Key Resources:**
- **Operator Quick Reference:** [runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md) — Quick commands, common failure patterns, decision tree for `--changed` vs `--all`
- **Operator Runbook:** [runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) — When gate triggers, classification rules, triage workflow, allowlist management
- **Validator Script:** ``scripts&#47;ops&#47;validate_docs_token_policy.py`` — CLI tool (exit codes: 0=pass, 1=violations, 2=error)
- **Allowlist:** ``scripts&#47;ops&#47;docs_token_policy_allowlist.txt`` — Generic placeholders, system paths (31 entries)
- **CI Workflow:** ``.github&#47;workflows&#47;docs-token-policy-gate.yml`` — Runs on PRs touching ``docs&#47;**&#47;*.md``
- **Tests:** ``tests&#47;ops&#47;test_validate_docs_token_policy.py`` — 26 unit tests

**Quick Commands:**
```bash
# Run validator on changed files (PR mode)
python3 scripts/ops/validate_docs_token_policy.py --changed

# Run validator on specific directory
python3 scripts/ops/validate_docs_token_policy.py docs/ops/

# Run full test suite
python3 -m pytest tests/ops/test_validate_docs_token_policy.py -v
```

**When Gate Fails:**
1. Read CI log for violations (e.g., ``Line 42: scripts&#47;example.py (ILLUSTRATIVE)``)
2. Fix: Encode ``&#47;`` as `&#47;` for illustrative paths (e.g., `scripts&#47;example.py`)
3. Re-run validator locally: ``python3 scripts&#47;ops&#47;validate_docs_token_policy.py --changed``
4. Push fix

**Token Classifications (7 types):**
- **ILLUSTRATIVE** (needs encoding): `scripts&#47;example.py`
- **REAL_REPO_TARGET** (exempt): ``scripts&#47;ops&#47;ops_center.sh`` (file exists)
- **BRANCH_NAME** (exempt): ``feature&#47;my-branch``
- **URL** (exempt): ``https:&#47;&#47;github.com&#47;...``
- **COMMAND** (exempt): ``python scripts&#47;run.py``
- **LOCAL_PATH** (exempt): ``.&#47;scripts&#47;local.py``, ``~&#47;config.toml``
- **ALLOWLISTED** (exempt): ``some&#47;path`` (in allowlist)

**Allowlist Management:**
- **When to allowlist:** Generic placeholders (``some&#47;path``), system paths (``&#47;usr&#47;local&#47;bin``), third-party paths
- **When NOT to allowlist:** Illustrative paths specific to one doc (encode instead), real repo paths (auto-exempt), typos (fix docs)
- **How to add:** Edit ``scripts&#47;ops&#47;docs_token_policy_allowlist.txt``, add comment with rationale, commit with clear message

**Troubleshooting:**
- **Gate passes but reference-targets-gate fails:** Token Policy only checks inline-code; Reference Targets checks all patterns → See [RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md](runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md)
- **Copy/paste includes `&#47;`:** Browsers decode automatically; if not, manually replace with ``&#47;``

**Related:**
- PR #693: [Merge Log](PR_693_MERGE_LOG.md) — Implementation + tests + runbook
- PR #691: [Merge Log](PR_691_MERGE_LOG.md) — Policy formalization
- PR #690: [Merge Log](PR_690_MERGE_LOG.md) — First application of `&#47;` encoding

## Docs Reference Targets Guardrail — Supported Formats

Der Check `docs-reference-targets-gate` stellt sicher, dass in Docs referenzierte **Repo-Targets** (Dateien) existieren, ohne typische Markdown-/Shell-False-Positives zu triggern.

### Unterstützte Referenzen (werden geprüft)
- **Plain paths** relativ zum Repo-Root, z.B. ``docs&#47;ops&#47;README.md``, ``scripts&#47;ops&#47;ops_center.sh``
- **Markdown-Links**: ``[Text]\(docs&#47;ops&#47;README.md\)``
- **Anchors** werden ignoriert (nur Datei wird geprüft): `RISK_LAYER_ROADMAP.md#overview`
- **Query-Parameter** werden ignoriert: ``docs&#47;ops&#47;README.md?plain=1``
- **Relative Pfade in Docs** werden korrekt resolved (relativ zur jeweiligen Markdown-Datei)

**Beispiele (konzeptionell):**
```
./README.md      # Same directory
../risk/README.md # Parent directory
```

### Ignorierte Muster (werden NICHT als Repo-Targets gezählt)
- **URLs**: ``http:&#47;&#47;…``, ``https:&#47;&#47;…``, z.B. ``<https:&#47;&#47;example.com&#47;docs&#47;ops&#47;README.md>``
- **Globs/Wildcards**: `*`, `?`, `[]`, `< >` (z.B. ``docs&#47;*.md``, ``docs&#47;**&#47;README.md``)
- **Commands mit Spaces** (z.B. ``.&#47;scripts&#47;ops&#47;ops_center.sh doctor``)
- **Directories mit trailing slash** (z.B. ``docs&#47;ops&#47;``)
- **Referenzen innerhalb von Bash-Codeblöcken**:
  ```bash
  # Alles innerhalb dieses Blocks wird NICHT als Target gecheckt
  cat docs/ops/__fixture_missing_target__nope.md
  ```

### Golden Corpus Tests
Das Verhalten ist durch ein "Golden Corpus" an Fixtures abgedeckt (Regressionssicherheit):
- ``tests&#47;fixtures&#47;docs_reference_targets&#47;pass&#47;`` — Valide Referenzen + ignorierte Muster
- ``tests&#47;fixtures&#47;docs_reference_targets&#47;fail&#47;`` — Fehlende Targets (muss detected werden)
- ``tests&#47;fixtures&#47;docs_reference_targets&#47;relative_repo&#47;`` — Isolated Fixture-Repo für relative Pfade

**Pytest Tests:**
```bash
python3 -m pytest -q tests/ops/test_verify_docs_reference_targets_script.py
```

---

Beim `--merge` läuft standardmäßig automatisch ein **Docs Diff Guard**, der große versehentliche Löschungen in ``docs&#47;*`` erkennt und **den Merge blockiert**.

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
- Vollständige Dokumentation: ``docs&#47;ops&#47;README.md`` (Abschnitt "Docs Diff Guard")
- PR Management Toolkit: ``docs&#47;ops&#47;PR_MANAGEMENT_TOOLKIT.md``
- Standalone Script: ``scripts&#47;ops&#47;docs_diff_guard.sh``
- Merge-Log: ``docs&#47;ops&#47;PR_311_MERGE_LOG.md``

```bash
# Alle Checks ausführen
./scripts/ops/ops_doctor.sh

# JSON-Output
./scripts/ops/ops_doctor.sh --json

# Spezifische Checks
./scripts/ops/ops_doctor.sh --check repo.git_root --check deps.uv_lock

# Demo
./scripts/ops/demo_ops_doctor.sh
```

### Features

- ✅ 9 Repository-Health-Checks (Git, Dependencies, Config, Docs, Tests, CI/CD)
- ✅ JSON- und Human-Readable-Output
- ✅ Spezifische Check-Ausführung
- ✅ Exit-Codes für CI/CD-Integration
- ✅ Umfassende Dokumentation

### Dokumentation

- **Vollständige Dokumentation**: [OPS_DOCTOR_README.md](OPS_DOCTOR_README.md)
- **Beispiel-Output**: `ops_doctor_example_output.txt` (example file not included)
- **Implementation Summary**: [OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md](reports/OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md)

### Merge-Log Health Integration

`ops doctor` prüft automatisch die Merge-Log-Infrastruktur:

```bash
# Volle Prüfung (Validator + Tests, ~10s)
ops doctor

# Schnellmodus (nur Validator, <1s)
ops doctor --quick
```

**Geprüft wird:**
- ✅ Merge-Log Generator (executable + markers)
- ✅ Dokumentation (marker format)
- 🧪 Offline Tests (falls `--quick` nicht gesetzt)

**Exit Codes:**
- `0` = Alle Checks bestanden
- `!= 0` = Mindestens ein Check fehlgeschlagen

### Formatter Policy Guardrail

- Zusätzlich verifiziert `ops doctor`, dass das CI-Enforcement aktiv ist (Lint Gate enthält den Drift-Guard-Step).
`ops doctor` prüft automatisch, dass keine `black --check` Enforcement in Workflows/Scripts existiert:

```bash
# Formatter Policy Check (immer aktiv, auch bei --quick)
ops doctor
ops doctor --quick
```

**Source of Truth:**
- ✅ `ruff format --check` (CI + Ops)
- ❌ `black --check` (nicht erlaubt)

**Geprüft wird:**
- ✅ .github/workflows (keine black enforcement)
- ✅ scripts (keine black enforcement)

**Enforcement:**
- 🏥 **ops doctor** (lokal, immer aktiv)
- 🛡️ **CI Lint Gate** (automatisch bei jedem PR, auch docs-only)

**Bei Verstößen:**
```bash
# Manueller Check
scripts/ops/check_no_black_enforcement.sh
```

---

## 🚀 PR Management Toolkit

Vollständiges Toolkit für sicheres PR-Review und Merge mit Safe-by-Default-Design.

### Quick Start

```bash
# Review-only (safe default)
scripts/ops/review_and_merge_pr.sh --pr 259

# Review + Merge (2-step, empfohlen)
scripts/ops/review_and_merge_pr.sh --pr 259 --watch --allow-fail audit
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --update-main

# One-Shot Workflow
PR=259 ./scripts/ops/pr_review_merge_workflow_template.sh
```

### Features

- ✅ **Safe-by-Default**: Review-only ohne `--merge` Flag
- ✅ **Multi-Layer Validation**: Working Tree, Mergeable Status, Review Decision, CI Checks
- ✅ **Intelligent Retry Logic**: Automatische Retries bei `UNKNOWN` Mergeable-Status
- ✅ **Selective Allow-Fail**: Für bekannte Flaky-Checks (z.B. audit)
- ✅ **Watch Mode**: Wartet automatisch auf CI-Check-Completion
- ✅ **Dry-Run Support**: Test-Modus ohne echte Änderungen

### Dokumentation

- **Quick Start**: [PR_MANAGEMENT_QUICKSTART.md](PR_MANAGEMENT_QUICKSTART.md) ⭐
- **Vollständige Dokumentation**: [PR_MANAGEMENT_TOOLKIT.md](PR_MANAGEMENT_TOOLKIT.md)
- **Basis-Tool**: ``scripts&#47;ops&#47;review_and_merge_pr.sh``
- **One-Shot Workflow**: ``scripts&#47;ops&#47;pr_review_merge_workflow.sh``
- **Template Workflow**: ``scripts&#47;ops&#47;pr_review_merge_workflow_template.sh``

---

## 📋 Übersicht – PR Tools

| Skript | Zweck | Output | Network | Safe Default |
|--------|-------|--------|---------|--------------|
| `pr_inventory_full.sh` | Vollständiges PR-Inventar + Analyse | JSON/CSV/Markdown | ✅ Read-only | ✅ Ja |
| `label_merge_log_prs.sh` | Automatisches Labeln von Merge-Log-PRs | GitHub Labels | ✅ Write | ✅ DRY_RUN=1 |

---

## 🔍 PR Inventory (vollständig)

Generiert ein vollständiges PR-Inventar inkl. Analyse, CSV-Export und Markdown-Report.

### Verwendung

```bash
# Standard (alle Defaults)
./scripts/ops/pr_inventory_full.sh

# Mit custom Repository
REPO=owner/name ./scripts/ops/pr_inventory_full.sh

# Mit custom Output-Verzeichnis
OUT_ROOT=$HOME/Peak_Trade/reports/ops ./scripts/ops/pr_inventory_full.sh

# Mit Limit
LIMIT=500 ./scripts/ops/pr_inventory_full.sh

# Alle Optionen kombiniert
REPO=rauterfrank-ui/Peak_Trade \
LIMIT=1000 \
OUT_ROOT=/tmp \
./scripts/ops/pr_inventory_full.sh

# Help anzeigen
./scripts/ops/pr_inventory_full.sh --help
```

### Output-Struktur

```
/tmp/peak_trade_pr_inventory_<timestamp>/
├── open.json              # Alle offenen PRs
├── closed_all.json        # Alle geschlossenen PRs (inkl. merged)
├── merged.json            # Nur gemergte PRs
├── merge_logs.csv         # Merge-Log-PRs als CSV
└── PR_INVENTORY_REPORT.md # Zusammenfassung + Statistiken
```

### Report-Inhalt

Der `PR_INVENTORY_REPORT.md` enthält:

- **Totals**: Open, Closed, Merged, Closed (unmerged)
- **Category Counts**:
  - `merge_log` – PRs mit Pattern `^docs\(ops\): add PR #\d+ merge log`
  - `ops_infra` – Ops/Workflow/CI/Audit/Runbook-PRs
  - `format_sweep` – Format/Lint/Pre-commit-PRs
  - `other` – Alle anderen
- **Latest merge-log PRs**: Top 25 mit Links

### Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `REPO` | ``rauterfrank-ui&#47;Peak_Trade`` | GitHub Repository |
| `LIMIT` | `1000` | Max. PRs pro Abfrage |
| `OUT_ROOT` | ``&#47;tmp`` | Output-Verzeichnis |

### Beispiel-Output

```markdown
# Peak_Trade – PR Inventory Report

- Generated: 2025-12-21 14:30:00

## Totals

- Open PRs: **3**
- Closed (all): **215**
- Merged: **198**
- Closed (unmerged): **17**

## Category counts (closed_all)

- merge_log: **147**
- ops_infra: **23**
- format_sweep: **8**
- other: **37**

## Latest merge-log PRs (top 25)

- [PR #521](https://github.com/rauterfrank-ui/Peak_Trade/pull/521) — Ops WebUI: CI health run-now buttons (v0.2) (merged 2026-01-03)
- [PR #519](https://github.com/rauterfrank-ui/Peak_Trade/pull/519) — Ops WebUI: CI health snapshots (v0.2) (merged 2026-01-03)
- [PR #518](https://github.com/rauterfrank-ui/Peak_Trade/pull/518) — ops(dashboard): add CI & governance health panel (merged 2026-01-03)
- [PR #240](PR_240_MERGE_LOG.md) — test(ops): add run_helpers adoption guard (merged 2025-12-21)
- PR #208 — docs(ops): add PR #207 merge log (2025-12-20T10:15:00Z)
  - https://github.com/rauterfrank-ui/Peak_Trade/pull/208
...
```

---

## 🚨 Incidents & Post-Mortems

* **2025-12-26 — Formatter Drift (Audit) → Tool Alignment**

  * **Root Cause:** Repo nutzt `ruff format`, Legacy/Drift führte zu Audit-Failures (detected by `ruff format --check`).
  * **Fix:** **#354** merged → `black` entfernt, **Single Source of Truth = RUFF**; Guardrail `check_no_black_enforcement.sh` ✅
  * **Campaign:** #283/#303 auto-merge pending; #269 closed (superseded); #259 merge via Web-UI (fehlender OAuth `workflow` scope).
  * **RCA:** ``incidents&#47;2025-12-26_formatter_drift_audit_alignment.md``

---

## 🏷️ Label Merge-Log PRs

Findet alle Merge-Log-PRs und labelt sie automatisch (mit DRY_RUN-Protection).

### Verwendung

```bash
# DRY RUN (Standard): Nur anzeigen, keine Änderungen
./scripts/ops/label_merge_log_prs.sh

# DRY RUN mit custom Label
LABEL="documentation/merge-log" ./scripts/ops/label_merge_log_prs.sh

# ECHT: Labels wirklich anwenden
DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh

# Mit Label-Auto-Creation
ENSURE_LABEL=1 DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh

# Alle Optionen kombiniert
REPO=rauterfrank-ui/Peak_Trade \
LABEL="ops/merge-log" \
LIMIT=1000 \
ENSURE_LABEL=1 \
DRY_RUN=0 \
./scripts/ops/label_merge_log_prs.sh

# Help anzeigen
./scripts/ops/label_merge_log_prs.sh --help
```

### Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `REPO` | ``rauterfrank-ui&#47;Peak_Trade`` | GitHub Repository |
| `LABEL` | ``ops&#47;merge-log`` | Label-Name |
| `LIMIT` | `1000` | Max. PRs pro Abfrage |
| `DRY_RUN` | `1` | 1 = nur anzeigen, 0 = wirklich labeln |
| `ENSURE_LABEL` | `0` | 1 = Label erstellen falls nicht vorhanden |

### Pattern-Matching

Das Skript findet PRs mit folgendem Titel-Pattern (case-insensitive):

```
^docs\(ops\): add PR #\d+ merge log
```

**Beispiele:**
- ✅ `docs(ops): add PR #207 merge log`
- ✅ `Docs(ops): Add PR #123 Merge Log`
- ❌ `feat: add merge log for PR #123`
- ❌ `docs(ops): update merge log`

### Output

```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️  Peak_Trade: Label merge-log PRs
Repo: rauterfrank-ui/Peak_Trade | Label: ops/merge-log | DRY_RUN=1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found merge-log PRs: 147
List: /tmp/peak_trade_merge_log_prs.txt

DRY RUN (no changes). First 30 PRs:
 - PR #208
 - PR #206
 - PR #204
 ...

To actually apply labels:
  DRY_RUN=0 LABEL="ops/merge-log" scripts/ops/label_merge_log_prs.sh
```

---

## 🛡️ Sicherheitsfeatures

### Beide Skripte

- ✅ `set -euo pipefail` für strikte Fehlerbehandlung
- ✅ Preflight-Checks für `gh` CLI und Python
- ✅ `gh auth status` Validierung
- ✅ Help-Text (`--help`, `-h`)
- ✅ Auto-Detection von `python3` / `python`
- ✅ Shared helpers (`run_helpers.sh`) für konsistentes Error-Handling

### `label_merge_log_prs.sh` spezifisch

- ✅ **DRY_RUN=1** als Standard (keine versehentlichen Änderungen)
- ✅ Empty-Result-Check (Exit wenn keine PRs gefunden)
- ✅ Optional: Label-Auto-Creation mit `ENSURE_LABEL=1`

---

## 🧩 Ops Bash Run Helpers (strict/robust)

Für konsistente "fail-fast" vs "warn-only" Semantik in neuen Ops-Skripten nutzen wir:
- ``scripts&#47;ops&#47;run_helpers.sh`` (Quelle der Wahrheit, inkl. Quick Reference im Header)

**Default:** strict (fail fast)
**Robust mode:** `PT_MODE=robust bash <script>.sh` (optional: `MODE=robust`)

**Minimal usage (copy/paste):**
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=run_helpers.sh
source "${SCRIPT_DIR}/run_helpers.sh"

pt_require_cmd gh
pt_section "Strict core"
pt_run_required "Update main" bash -lc 'git checkout main && git pull --ff-only'

pt_section "Main work"
pt_run "Do the thing" bash -lc 'echo "work"'

pt_section "Optional extras"
pt_run_optional "Dry-run labels" bash scripts/ops/label_merge_log_prs.sh
```

**Hinweis:** Bestehende Skripte (`pr_inventory_full.sh`, `label_merge_log_prs.sh`) verwenden die Helpers **nicht** (bleiben im Original-Stil). Nur für neue Skripte gedacht.

---

## 📦 Voraussetzungen

### System-Tools

```bash
# GitHub CLI
brew install gh
gh auth login

# Python (3.x bevorzugt)
python3 --version
# Falls `python` vorhanden ist, ist das äquivalent:
# python --version
```

### Python-Module

Beide Skripte verwenden nur Standard-Library-Module:
- `json`
- `re`
- `csv`
- `pathlib`
- `datetime`
- `sys`

### Bash Helpers

Die Ops-Skripte nutzen ``scripts&#47;ops&#47;run_helpers.sh`` für konsistentes Error-Handling:

```bash
# Automatisch gesourced in pr_inventory_full.sh und label_merge_log_prs.sh
# Bietet: pt_run_required(), pt_run_optional(), pt_require_cmd(), pt_log(), etc.

# Modes:
# - PT_MODE=strict (default): Fehler → Abort
# - PT_MODE=robust: Fehler → Warn + Continue

# Beispiel (robust mode):
PT_MODE=robust bash scripts/ops/pr_inventory_full.sh
```

---

## 🔄 Workflow-Beispiele

### 1. Vollständige PR-Analyse

```bash
# Step 1: Inventory generieren
./scripts/ops/pr_inventory_full.sh

# Step 2: Report öffnen
code /tmp/peak_trade_pr_inventory_$(date +%Y%m%d)*/PR_INVENTORY_REPORT.md

# Step 3: CSV analysieren
open /tmp/peak_trade_pr_inventory_$(date +%Y%m%d)*/merge_logs.csv
```

### 2. Merge-Log-PRs labeln (sicher)

```bash
# Step 1: DRY RUN (was würde passieren?)
./scripts/ops/label_merge_log_prs.sh

# Step 2: Review der gefundenen PRs
cat /tmp/peak_trade_merge_log_prs.txt

# Step 3: Label erstellen (falls nötig) + anwenden
ENSURE_LABEL=1 DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh
```

### 3. Batch-Processing (beide Skripte)

```bash
#!/usr/bin/env bash
# ops_pr_maintenance.sh

# 1) Inventory
echo "=== Generating PR Inventory ==="
OUT_ROOT=$HOME/Peak_Trade/reports/ops ./scripts/ops/pr_inventory_full.sh

# 2) Labeling
echo ""
echo "=== Labeling Merge-Log PRs ==="
ENSURE_LABEL=1 DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh

echo ""
echo "✅ PR Maintenance complete"
```

---

## 🐛 Troubleshooting

### Error: `gh CLI fehlt`

```bash
brew install gh
gh auth login
```

### Error: `gh ist nicht authentifiziert`

```bash
gh auth login
gh auth status
```

### Error: `python fehlt`

```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3
```

### Label existiert nicht

```bash
# Option 1: Auto-Create
ENSURE_LABEL=1 DRY_RUN=0 ./scripts/label_merge_log_prs.sh

# Option 2: Manuell erstellen
gh label create "ops/merge-log" \
  --description "Merge-log documentation PRs" \
  --color "ededed"
```

### DRY_RUN deaktivieren funktioniert nicht

```bash
# Richtig:
DRY_RUN=0 ./scripts/label_merge_log_prs.sh

# Falsch (String wird als truthy interpretiert):
DRY_RUN=false ./scripts/label_merge_log_prs.sh
```

---

## 📝 Logging & Debugging

### Temporäre Dateien

```bash
# PR Nummern (label_merge_log_prs.sh)
cat /tmp/peak_trade_merge_log_prs.txt

# Inventory Output (pr_inventory_full.sh)
ls -lh /tmp/peak_trade_pr_inventory_*/
```

### Debug-Modus aktivieren

```bash
# Bash Debug-Output
bash -x ./scripts/ops/pr_inventory_full.sh

# Mit set -x im Skript
# Füge nach der shebang-Zeile hinzu:
# set -x
```

---

## 🧪 Tests

Beide Skripte haben entsprechende Tests im ``tests&#47;``-Verzeichnis.

### Relevante Test-Dateien

```bash
# Workflow-Tests
tests/test_ops_merge_log_workflow_wrapper.py

# Integration-Tests (falls vorhanden)
tests/integration/test_ops_pr_tools.py
```

### Test-Ausführung

```bash
# Einzelner Test
python3 -m pytest tests/test_ops_merge_log_workflow_wrapper.py -v

# Alle Ops-Tests
python3 -m pytest tests/ -k "ops" -v
```

---

## 📚 Verwandte Dokumentation

- [Peak_Trade Tooling & Evidence Chain Runbook](Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md)
- [CI Large PR Implementation Report](reports/CI_LARGE_PR_IMPLEMENTATION_REPORT.md)
- [Merge Log Workflow](PR_208_MERGE_LOG.md)

---

## 🧪 Knowledge DB Ops Scripts

| Script | Zweck | Use Case |
|--------|-------|----------|
| `knowledge_smoke_runner.sh` | Manual smoke tests (server restart required) | Lokale Entwicklung |
| `knowledge_smoke_runner_auto.sh` | Auto smoke tests (all 3 modes) | Lokale Entwicklung, vollständiger Test |
| `knowledge_prod_smoke.sh` | Remote production smoke tests | Post-Deployment, Staging/Prod, CI/CD |

### knowledge_prod_smoke.sh — Production Deployment Drill

Remote smoke tests gegen live deployments ohne Server-Restart.

**Verwendung:**

```bash
# Basic
BASE_URL=https://prod.example.com ./scripts/ops/knowledge_prod_smoke.sh

# With auth
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --token "$TOKEN"

# Strict mode
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --strict

# Custom prefix
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --prefix /v1/knowledge
```

**Exit Codes:**
- 0 = All checks passed
- 1 = One or more checks failed
- 2 = Degraded in strict mode

**Runbook:** [Knowledge Production Deployment Drill](../runbooks/KNOWLEDGE_PRODUCTION_DEPLOYMENT_DRILL.md)

---

## 📝 Ops Templates

Standardized templates for operational documentation, merge logs, and audit artifacts. All templates follow the **[Placeholder Policy](PLACEHOLDER_POLICY.md)** with consistent `[TBD]` and `TBD(owner)` markers.

### Available Templates

#### Merge Log Templates
- **[Compact Template](templates/MERGE_LOG_TEMPLATE_COMPACT.md)** — Lightweight merge log for straightforward PRs (Summary, Changes, Verification, Risk, How-To)
- **[Detailed Template](templates/MERGE_LOG_TEMPLATE_DETAILED.md)** — Comprehensive merge log for complex PRs (includes Timeline, Test Matrix, Rollback Plan, Incident Notes)

#### Audit Templates
- **[Evidence Index Template](templates/AUDIT_EVIDENCE_INDEX_TEMPLATE.md)** — Track audit evidence items with metadata, hashes, and verification methods
- **[Risk Register Template](templates/AUDIT_RISK_REGISTER_TEMPLATE.md)** — Risk assessment and tracking with likelihood/impact scoring and mitigation plans

### Template Usage

**Creating a merge log from template:**
```bash
# Copy template
cp docs/ops/templates/MERGE_LOG_TEMPLATE_COMPACT.md docs/ops/PR_XXX_MERGE_LOG.md

# Replace [TBD] placeholders with actual values
# Follow the Placeholder Policy: use [TBD] for inline, TBD(owner) for decisions
```

**Template Features:**
- ✅ Placeholder-policy compliant (`[TBD]`, `TBD(owner)` format)
- ✅ Explicit template markers (no confusion with live docs)
- ✅ Structured sections for consistency
- ✅ Version tracking and maintenance info

**See also:** [Placeholder Policy](PLACEHOLDER_POLICY.md)

---

## 📊 Audit Artefakte (v0)

Operational artifacts for audit evidence tracking and risk management. These are **process artifacts** for operational traceability—NOT compliance claims.

- **[Evidence Index](EVIDENCE_INDEX.md)** — Track audit evidence items (CI runs, PR merges, test outputs, drill sessions, incident postmortems)
- **[Risk Register](RISK_REGISTER.md)** — Operational risk register for docs/ops governance (policy drift, placeholder consistency, documentation interpretation)

**Scope:** v0 living documents for ops nachvollziehbarkeit (traceability), no external audit/compliance claims.

---

## 📊 Audit Artefakte (v0)

Operational artifacts for audit evidence tracking and risk management. These are **process artifacts** for operational traceability—NOT compliance claims.

- **[Evidence Index](EVIDENCE_INDEX.md)** — Track audit evidence items (CI runs, PR merges, test outputs, drill sessions, incident postmortems)
- **[Risk Register](RISK_REGISTER.md)** — Operational risk register for docs/ops governance (policy drift, placeholder consistency, documentation interpretation)

**Scope:** v0 living documents for ops nachvollziehbarkeit (traceability), no external audit/compliance claims.

---

## 📊 Audit Artefakte (v0)

Operational artifacts for audit evidence tracking and risk management. These are **process artifacts** for operational traceability—NOT compliance claims.

- **[Evidence Index](EVIDENCE_INDEX.md)** — Track audit evidence items (CI runs, PR merges, test outputs, drill sessions, incident postmortems)
- **[Risk Register](RISK_REGISTER.md)** — Operational risk register for docs/ops governance (policy drift, placeholder consistency, documentation interpretation)

**Scope:** v0 living documents for ops nachvollziehbarkeit (traceability), no external audit/compliance claims.

---

## 📋 Merge Logs

### Workflow

**Standard Process:** Jeder Merge-Log wird als eigener PR erstellt (Review + CI + Audit-Trail).

- **Vollständige Dokumentation:** [MERGE_LOG_WORKFLOW.md](MERGE_LOG_WORKFLOW.md)
- **Template:** [templates/ops/merge_log_template.md](../../templates/ops/merge_log_template.md)

**Quick Start:**

```bash
PR=<NUM>
git checkout -b docs/merge-log-$PR
# Erstelle docs/ops/PR_${PR}_MERGE_LOG.md + link in README
git add docs/ops/PR_${PR}_MERGE_LOG.md docs/ops/README.md
git commit -m "docs(ops): add compact merge log for PR #${PR}"
git push -u origin docs/merge-log-$PR
gh pr create --title "docs(ops): add merge log for PR #${PR}" --body "..."
```

### Batch Generator (Automatisiert)

Für mehrere PRs gleichzeitig oder single-PR mit Auto-Update der docs.

**Tool:** ``scripts&#47;ops&#47;generate_merge_logs_batch.sh``

**Verwendung:**

```bash
# Single PR
ops merge-log 281

# Mehrere PRs (batch)
ops merge-log 278 279 280

# Preview Mode (dry-run, keine Änderungen)
ops merge-log --dry-run 281

# Batch mit best-effort (sammelt Fehler, läuft weiter)
ops merge-log --keep-going 278 279 999
```

**Requirements:**
- `gh` CLI installiert + authentifiziert (`gh auth login`)
- PRs müssen bereits gemerged sein

**Output:**
- Erstellt ``docs&#47;ops&#47;PR_<NUM>_MERGE_LOG.md`` für jedes PR
- Updates automatisch ``docs&#47;ops&#47;README.md`` + ``docs&#47;ops&#47;MERGE_LOG_WORKFLOW.md`` (via Marker)

**Flags:**
- `--dry-run` — Preview Mode: zeigt Änderungen, schreibt nichts
- `--keep-going` — Best-Effort: läuft bei Fehlern weiter, Exit 1 am Ende falls welche
- `--help` — Zeigt Usage

**Validierung:**

```bash
# Setup validieren (offline, <1s)
scripts/ops/validate_merge_logs_setup.sh
```

#### Marker Format (MERGE_LOG_EXAMPLES)

Die folgenden Dateien **müssen** diese Marker enthalten für Auto-Updates:
- ``docs&#47;ops&#47;README.md``
- ``docs&#47;ops&#47;MERGE_LOG_WORKFLOW.md``

**Format:**
```html
<!-- MERGE_LOG_EXAMPLES:START -->
- PR #999 — docs(grafana): fix DS_LOCAL uid templating in execution watch dashboard: docs/ops/PR_999_MERGE_LOG.md
<!-- MERGE_LOG_EXAMPLES:END -->










```

Das Batch-Tool ersetzt den Inhalt zwischen den Markern idempotent.

**Validator:** ``scripts&#47;ops&#47;validate_merge_logs_setup.sh`` prüft:
- Generator ist executable
- Marker sind vorhanden in beiden Dateien
- `ops_center.sh` hat die Integration

**Siehe auch:** [MERGE_LOG_WORKFLOW.md](MERGE_LOG_WORKFLOW.md)

### Liste

- [PR #322](PR_322_MERGE_LOG.md) — docs(risk): Component VaR MVP (Implementation + Tests + Docs) (merged 2025-12-25)
- [PR #323](PR_323_MERGE_LOG.md) — feat(ops): Required Checks Drift Guard v1 (merged 2025-12-25)
- [PR #261](PR_261_MERGE_LOG.md) — chore(ops): add stash triage helper (export-first, safe-by-default) (merged 2025-12-23)
- [PR #250](PR_250_MERGE_LOG.md) — feat(ops): add ops_doctor repo health check tool (merged 2025-12-23)
- [PR #243](PR_243_MERGE_LOG.md) — feat(webui): knowledge API endpoints + readonly/web-write gating + smoke runners (merged 2025-12-22)
- [PR #237](PR_237_MERGE_LOG.md) — chore(ops): add shared bash run helpers (strict/robust) (merged 2025-12-21)
- [PR #235](PR_235_MERGE_LOG.md) — fix(ops): improve label_merge_log_prs.sh to find open PRs (merged 2025-12-21)
- [PR #234](PR_234_MERGE_LOG.md) — chore(ops): PR inventory + merge-log labeling scripts (merged 2025-12-21)
- [PR #123](PR_123_MERGE_LOG.md) — docs: core architecture & workflow documentation (P0+P1) (merged 2025-12-23)

---

## 🔮 Zukünftige Erweiterungen

### Geplant

- [ ] GitHub Actions Integration (automatisches Labeling bei PR-Creation)
- [ ] Slack/Discord-Benachrichtigungen bei Labeling
- [ ] Extended Report mit Contributor-Statistiken
- [ ] CSV-Export für alle Kategorien (nicht nur merge_logs)
- [ ] Label-Bulk-Removal-Skript (Reversal-Tool)

### Nice-to-Have

- [ ] Web-UI für PR-Inventory (Quarto Dashboard)
- [ ] Automatische PR-Cleanup-Empfehlungen
- [ ] Integration mit `knowledge_db` (AI-gestütztes Tagging)
- [ ] Time-Series-Analyse (PR-Volume über Zeit)

---

## 💡 Tipps & Best Practices

### Performance

```bash
# Für große Repos: Limit reduzieren
LIMIT=500 ./scripts/ops/pr_inventory_full.sh

# Parallele Ausführung (wenn mehrere Repos)
for repo in repo1 repo2 repo3; do
  REPO="owner/$repo" ./scripts/ops/pr_inventory_full.sh &
done
wait
```

### Sicherheit

```bash
# Immer zuerst DRY_RUN
./scripts/ops/label_merge_log_prs.sh

# Label-Creation separat testen
ENSURE_LABEL=1 DRY_RUN=1 ./scripts/ops/label_merge_log_prs.sh
```

### Maintenance

```bash
# Alte Inventory-Outputs aufräumen (älter als 30 Tage)
find /tmp -name "peak_trade_pr_inventory_*" -type d -mtime +30 -exec rm -rf {} +

# Cleanup-Skript erstellen
cat > scripts/ops/cleanup_old_inventories.sh <<'EOF'
#!/usr/bin/env bash
find /tmp -name "peak_trade_pr_inventory_*" -type d -mtime +30 -print -exec rm -rf {} +
EOF
chmod +x scripts/ops/cleanup_old_inventories.sh
```

---

## 📁 Datei-Struktur

```
/Users/frnkhrz/Peak_Trade/scripts/
├── ops/
│   ├── pr_inventory_full.sh       # ✅ PR Inventory + Analyse
│   └── label_merge_log_prs.sh     # ✅ Automatisches Labeln
└── OPS_PR_TOOLS_README.md         # ✅ Diese Dokumentation
```

---

**Version:** 1.0.0
**Letzte Aktualisierung:** 2025-12-21
**Maintainer:** Peak_Trade Ops Team

- [PR #246](PR_246_MERGE_LOG.md) — chore(ops): add knowledge deployment drill e2e + fix prod smoke headers (merged 2025-12-22T21:52:11Z)

## 🛡️ Policy Critic & Governance Triage

### Governance Validation Artifacts

Canary tests and validation evidence for governance mechanisms:

- **PR #496 (Canary – Execution Override Validation)** → [CANARY_EXECUTION_OVERRIDE_VALIDATION_20260102.md](CANARY_EXECUTION_OVERRIDE_VALIDATION_20260102.md)
  - Validates ``ops&#47;execution-reviewed`` override mechanism
  - Evidence requirement: Label + Evidence File + Auto-Merge disabled
  - Result: 18/18 checks passed, override accepted

### Policy Critic False-Positive Runbook

Operator-Runbook für Format-only PRs, die vom Policy Critic fälschlicherweise blockiert werden.

**Use Case:** Ein PR ändert nur Formatting (Black, Ruff, Import-Sorting), wird aber vom Policy Critic blockiert.

**Runbook:** [POLICY_CRITIC_TRIAGE_RUNBOOK.md](POLICY_CRITIC_TRIAGE_RUNBOOK.md)

**Key Features:**
- ✅ Format-Only Definition + Beispiele
- ✅ Preflight-Checks (gh pr diff/view)
- ✅ Decision Tree für Admin-Bypass
- ✅ Audit-Trail Template (Accountability)
- ✅ Post-Merge Sanity-Checks (ruff/black/pytest)
- ✅ Do-NOT-Bypass Criteria (Execution/Risk/Config/Deps)
- ✅ Rollback-Plan bei Fehlern

**Quick Start:**

```bash
# 1) Preflight-Checks
gh pr view <PR_NUMBER> --json files
gh pr diff <PR_NUMBER> --stat

# 2) Audit-Kommentar (siehe Runbook)
gh pr comment <PR_NUMBER> --body "<AUDIT_TEMPLATE>"

# 3) Admin-Bypass (nur bei format-only!)
gh pr merge <PR_NUMBER> --admin --squash

# 4) Post-Merge Sanity
git pull --ff-only
ruff check . && black --check .
```

**⚠️ WICHTIG:** Kein Bypass bei Execution/Risk/Config/Deps/Governance Changes!

---

## Stability & Resilience

- **Stability & Resilience Plan v1**: [STABILITY_RESILIENCE_PLAN_V1.md](STABILITY_RESILIENCE_PLAN_V1.md)
  - Production-readiness initiative (data contracts, atomic cache, error taxonomy, reproducibility, config validation, observability, CI smoke gates)
  - Milestone: [Stability & Resilience v1](https://github.com/rauterfrank-ui/Peak_Trade/milestone/1)
  - Issues: [#124](https://github.com/rauterfrank-ui/Peak_Trade/issues/124) - [#134](https://github.com/rauterfrank-ui/Peak_Trade/issues/134)

---

## Related Documentation

### Format-Only Guardrail (CI Implementation)

**Status:** ✅ Active (ab PR #XXX)

Die im Runbook dokumentierte "Safety Fix" Mechanik ist jetzt als **CI-Guardrail** implementiert.

**Komponenten:**

1. **Verifier Script:** ``scripts&#47;ops&#47;verify_format_only_pr.sh``
   - Deterministischer Format-Only Check via git worktree + tree hash comparison
   - Exit 0 = Format-only confirmed, Exit 1 = Not format-only

2. **GitHub Actions Job:** `format-only-verifier` (required check)
   - Läuft auf allen PRs
   - Prüft Label ``ops&#47;format-only``
   - Führt Verifier Script aus (wenn Label gesetzt)
   - **FAIL** wenn Label gesetzt aber Verifier FAIL → verhindert Merge

3. **Policy Critic No-Op:** Conditional skip
   - Policy Critic läuft als no-op **nur wenn:**
     - Label ``ops&#47;format-only`` gesetzt **UND**
     - `format-only-verifier` PASS ✅
   - Sonst: Policy Critic läuft normal (blockierend)

**Operator How-To:**

```bash
# 1) Label setzen (nur nach manual preflight!)
gh pr edit <PR> --add-label "ops/format-only"

# 2) CI prüfen: format-only-verifier muss grün sein
gh pr checks <PR>

# 3) Falls Verifier FAIL:
#    - Label entfernen
#    - PR fixen (non-format changes entfernen)
#    - Oder: regulärer Review-Prozess
gh pr edit <PR> --remove-label "ops/format-only"
```

**Warum das funktioniert:**

- ✅ Kein "Bypass" – Skip nur mit blockierendem Verifier
- ✅ Reduziert False-Positive Friction (Format-PRs laufen durch)
- ✅ Verhindert Bypass-Kultur (kein `--admin` mehr nötig)
- ✅ Erhält Safety Layer (echte PRs triggern weiterhin Policy Critic)
- ✅ Saubere Evidence Chain (Label + Verifier Logs + Audit Trail)

**Workflow:**

```
PR mit Label "ops/format-only"
  │
  ▼
format-only-verifier (required check)
  │
  ├─ Label nicht gesetzt? → SUCCESS (no-op), Policy Critic läuft normal
  │
  ├─ Label gesetzt + Verifier PASS? → SUCCESS, Policy Critic no-op ✅
  │
  └─ Label gesetzt + Verifier FAIL? → FAIL ❌ (PR blockiert, Label entfernen)
```

**Siehe auch:** [Policy Critic Triage Runbook](POLICY_CRITIC_TRIAGE_RUNBOOK.md) (Safety Fix Sektion)

---

## 🧯 Known CI Issues

- [CI Audit Known Issues](CI_AUDIT_KNOWN_ISSUES.md) — Pre-existing Black formatting issue (non-blocking)

## 🗂️ Stash Hygiene & Triage

### Stash Hygiene Policy

Best Practices für sicheres Stash-Management:

- **Policy & Ablauf:** [STASH_HYGIENE_POLICY.md](STASH_HYGIENE_POLICY.md)
  - Keyword-based drop (keine index-basierten Drops)
  - Export-before-delete Workflow
  - Recovery-Branch-Strategie

### Stash Triage Tool

Automatisiertes Stash-Management mit Safe-by-Default-Design:

- **Tool:** [``scripts&#47;ops&#47;stash_triage.sh``](../../scripts/ops/stash_triage.sh)
- **Tests:** [``tests&#47;ops&#47;test_stash_triage_script.py``](../../tests/ops/test_stash_triage_script.py)

**Quick Start:**

```bash
# List all stashes
scripts/ops/stash_triage.sh --list

# Export all stashes (safe, no deletion)
scripts/ops/stash_triage.sh --export-all

# Export + drop (requires explicit confirmation)
scripts/ops/stash_triage.sh --export-all --drop-after-export --confirm-drop
```

**Features:**

- ✅ Safe-by-Default (no deletion without explicit flags)
- ✅ Keyword-Filter für selektiven Export
- ✅ Strukturierter Export (Patch + Metadata)
- ✅ Session Report mit Triage-Übersicht
- ✅ Exit 2 bei unsicherer Nutzung (Drop ohne Confirm)

**Export-Ablage:** ``docs&#47;ops&#47;stash_refs&#47;``

Siehe [STASH_HYGIENE_POLICY.md](STASH_HYGIENE_POLICY.md) für Details zur Automation-Sektion.

## 📋 Merge Logs → Workflow
- PR #262 — Merge Log (meta: merge-log workflow standard): `PR_262_MERGE_LOG.md`

<!-- MERGE_LOG_EXAMPLES:START -->
- PR #278 — merge log for PR #123 + ops references: docs/ops/PR_278_MERGE_LOG.md
- PR #279 — salvage untracked docs/ops assets: docs/ops/PR_279_MERGE_LOG.md
- PR #280 — archive session reports to worklogs: docs/ops/PR_280_MERGE_LOG.md
- PR #307 — docs(ops): document README_REGISTRY guardrail for ops doctor: docs/ops/PR_307_MERGE_LOG.md
- PR #309 — feat(ops): add branch hygiene script (origin/main enforcement): docs/ops/PR_309_MERGE_LOG.md
- PR #311 — feat(ops): add docs diff guard (mass-deletion protection): docs/ops/PR_311_MERGE_LOG.md
- PR #409 — fix(kill-switch): stabilize tests + add legacy adapter for risk-gate: docs/ops/PR_409_MERGE_LOG.md
<!-- MERGE_LOG_EXAMPLES:END -->
- PR #292 — formatter policy drift guard enforced in CI (Merge-Log): docs/ops/PR_292_MERGE_LOG.md
- PR #295 — guard the guardrail (CI enforcement presence) (Merge-Log): docs/ops/PR_295_MERGE_LOG.md

### Policy Guard Pattern
- Template: docs/ops/POLICY_GUARD_PATTERN_TEMPLATE.md

### Ops Doctor Dashboard
- Generate: scripts/ops/generate_ops_doctor_dashboard.sh
- Output: reports/ops/ops_doctor_dashboard.html

### Ops Doctor Dashboard (CI)
- Workflow: ``.github&#47;workflows&#47;ops_doctor_dashboard.yml`` (manual + scheduled)
- Output artifacts: `ops-doctor-dashboard` (HTML + JSON)
- Local generation: ``bash scripts&#47;ops&#47;generate_ops_doctor_dashboard.sh``

### Ops Doctor Dashboard (CI + Pages)
- Workflow: ``.github&#47;workflows&#47;ops_doctor_pages.yml`` (manual + scheduled)
- Run artifacts: `ops-doctor-dashboard` (index.html + index.json)
- Pages: Settings → Pages → Source = GitHub Actions (einmalig aktivieren)


### Ops Doctor Dashboard Badge

- Badge semantics: PASS (exit 0), WARN (exit 2), FAIL (any other non-zero)

## Placeholder & TODO Standards

**Policy:** [PLACEHOLDER_POLICY.md](PLACEHOLDER_POLICY.md) — Repository-wide standards for placeholder markers (TODO, TBD, FIXME, XXX, etc.)

**Features:**
- ✅ Clear marker definitions (TODO vs. FIXME vs. TBD vs. XXX)
- ✅ Ownership & issue-linking conventions
- ✅ Template-first approach for docs/audit
- ✅ Local inventory reports (git-ignored)

**Quick Start:**
```bash
# Generate local placeholder reports
python3 scripts/ops/placeholders/generate_placeholder_reports.py

# View reports (not committed)
cat .ops_local/inventory/TODO_PLACEHOLDER_INVENTORY.md
cat .ops_local/inventory/TODO_PLACEHOLDER_TARGET_MAP.md
```

**Reports include:**
- Pattern summary (counts per marker type)
- Top files by pattern
- Path-prefix analysis (docs/, src/, config/, .github/, other/)

**Note:** Reports are local artifacts (``.ops_local&#47;inventory&#47;``) and NOT committed to Git.

---

## Branch Hygiene (origin/main)
Um zu verhindern, dass versehentlich lokale (unpushed) Commits in einen PR rutschen, erstelle neue Branches **immer von ``origin&#47;main``**:

```bash
git checkout main
scripts/ops/new_branch_from_origin_main.sh feat/my-change
```

Das Script prüft:
- ✅ Working tree ist clean
- ✅ Lokaler `main` ist NICHT ahead von ``origin&#47;main`` (verhindert unpushed commits)
- ✅ Erstellt Branch explizit von ``origin&#47;main``

**Warum?** Siehe PR #305: Branch wurde vom lokalen `main` abgezweigt, der 2 unpushte Commits hatte → 4 Dateien statt 1 im PR.

## Git Operations Runbooks

### Rebase + Cleanup Workflow

Wiederverwendbarer Operator-Workflow für Rebase, Conflict-Triage, Merge, und Branch/Worktree-Cleanup.

**Runbook:** [runbooks/rebase_cleanup_workflow.md](runbooks/rebase_cleanup_workflow.md) ⭐

**Quick Start:**

```bash
# Report-only (keine Löschungen, nur Empfehlungen)
scripts/ops/report_worktrees_and_cleanup_candidates.sh
```

**Features:**
- ✅ Pre-Flight Checks (pwd, git status, repo root)
- ✅ Rebase Workflow (inkl. Konflikt-Resolution)
- ✅ Verification (ruff, pytest, CI-Checks)
- ✅ Safe Cleanup (Reachability-Check vor Branch-Deletion)
- ✅ Restore-Demo (Branch aus SHA rekonstruieren)
- ✅ Troubleshooting (Editor-Hangs, Conflict Markers, Stale Worktrees)

**Golden Rules:**
- Branch = Pointer, Commit bleibt
- Löschen nur nach Reachability-Check (`git merge-base --is-ancestor`)
- Worktrees zuerst, dann Branches
- Dokumentation (Merge-Log) immer mit Link im Index

**Use Cases:**
- Feature-Branch vor Merge auf aktuellen `main` rebased
- Worktrees/Branches nach erfolgreichem Merge aufräumen
- Demonstration: Branch-Pointer kann aus SHA rekonstruiert werden

## Docs Diff Guard (Mass-Deletion Schutz)

Wenn ein PR versehentlich massive Docs-Deletions enthält (z.B. README „-972"), ist das eine Red-Flag.

### Automatische Integration (seit PR #311)

Der Docs Diff Guard ist **automatisch in `review_and_merge_pr.sh` integriert** und läuft vor jedem `--merge`:

```bash
# Default: Guard läuft automatisch (Threshold: 200 Deletions/File unter docs/)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge

# Override: Custom Threshold
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-threshold 500

# Override: Warn-only (kein Fail)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-warn-only

# Override: Guard überspringen (NOT RECOMMENDED)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --skip-docs-guard
```

### Standalone (manuelle Pre-Merge Check)

Alternativ kann das Script auch manuell für lokale Checks genutzt werden:

```bash
# Standard: fail bei Violations
scripts/ops/docs_diff_guard.sh --base origin/main --threshold 200

# Warn-only (ohne Exit 1)
scripts/ops/docs_diff_guard.sh --warn-only

# Custom Threshold
scripts/ops/docs_diff_guard.sh --threshold 500
```

### Wie es funktioniert

- Zählt Deletions pro File unter ``docs&#47;`` (via GitHub PR Files API oder `git diff --numstat`)
- Fails bei >= 200 Deletions per File (default)
- `--warn-only` zum Testen ohne Exit 1
- `--threshold <n>` zum Anpassen

**Use-Case:** PR #310 hatte ursprünglich `-972` in README.md → wäre erkannt worden.

## Risk & Safety Gates (Operator Hub)

Schnellzugriff auf die pre-trade Risk Gates & Operator-Runbooks:

- VaR Gate Runbook: ``docs&#47;risk&#47;VAR_GATE_RUNBOOK.md``
- Stress Gate Runbook: ``docs&#47;risk&#47;STRESS_GATE_RUNBOOK.md``
- Liquidity Gate Runbook: ``docs&#47;risk&#47;LIQUIDITY_GATE_RUNBOOK.md``
- Risk Layer Roadmap: ``docs&#47;risk&#47;roadmaps&#47;RISK_LAYER_ROADMAP.md``

Hinweis: Gates sind standardmäßig konservativ/disabled-by-default ausrollbar; Aktivierung erfolgt über Config-Profile (Paper/Shadow → Monitoring → Live).

### Recon Audit Gate — Quick Commands

Wrapper-basierter CLI-Zugriff auf Reconciliation-Audit-Prüfungen mit standardisierten Exit-Codes:

```bash
# Summary-Text (human-readable)
bash scripts/execution/recon_audit_gate.sh summary-text

# Summary-JSON (machine-readable)
bash scripts/execution/recon_audit_gate.sh summary-json

# Gate-Mode (Exit-Code-Semantik)
bash scripts/execution/recon_audit_gate.sh gate
```

**Exit-Codes:**
- 0: Success (gate-mode: keine Findings)
- 2: Findings vorhanden (gate-mode; kein Fehler)
- 1: Script-Fehler

**Troubleshooting:**
- Bei Python-Runner-Mismatch (pyenv-Systeme) erzwingt der Wrapper pyenv-sichere Interpreter-Erkennung. Details siehe PR #470 Merge-Log.

**CI Smoke:**
- Path-filtered Check läuft bei Änderungen an wrapper/smoke/src/execution/pyproject/uv.lock
- Lokale Ausführung: ``bash scripts&#47;ci&#47;recon_audit_gate_smoke.sh``
- Note: gate exit 2 = findings present (nicht als Fehler behandelt)

**Referenz:** ``docs&#47;ops&#47;PR_470_MERGE_LOG.md``

---

## Merge-Log Amendment Policy (Immutable History)

**Prinzip:** Merge-Logs sind **immutable**. Nachträgliche Änderungen an bereits gemergten Merge-Logs erfolgen **nicht** durch direktes Editieren in `main`, sondern **immer** über einen **separaten Docs-only PR**.

### Wann ist ein Amendment erlaubt?
- **Klarheit/Lesbarkeit:** bessere Summary/Why/Changes-Struktur, präzisere Operator-Schritte
- **Fehlende Referenzen:** Runbook-/PR-/Issue-Links nachtragen
- **Korrekturen ohne Semantik-Änderung:** Tippfehler, Formatierung, eindeutige Faktenkorrektur (z.B. PR-Nummer/Dateiname)

### Wie wird amended?
1. **Neuer Branch** von `main` (Docs-only)
2. Änderung am Merge-Log durchführen **oder** (empfohlen) einen kleinen „Amendment"-Zusatz/Follow-up Log hinzufügen
3. **Commit + PR** (Label: `documentation`)
4. Optional: **Auto-Merge** aktivieren, wenn alle Required Checks grün

### Was ist *nicht* erlaubt?
- Rewriting von technischen Entscheidungen oder Risiko-Semantik, wenn dadurch die ursprüngliche historische Darstellung „umgebogen" wird
  → In dem Fall: **Follow-up PR + neues Merge-Log** oder „Incident/Correction Note" mit Verweis.

### Empfehlung (Ops-Workflow)
- Große Korrekturen: **neues** kurzes Dokument ``docs&#47;ops&#47;merge_logs&#47;<date>_amendment_<ref>.md`` mit Verweis auf das Original
- Kleine Korrekturen: PR gegen das betroffene Merge-Log mit klarer PR-Body-Begründung (Docs-only)

---

## GitHub Auth & Token Helper

Peak_Trade bevorzugt GitHub CLI (`gh`). Wenn ein Script einen Token braucht, nutze den zentralen Helper:

- Safe Debug (zeigt nur Prefix + Länge, kein Leak):
  - ``scripts&#47;utils&#47;get_github_token.sh --debug``
- Validierung (Exit != 0 wenn kein gültiger Token gefunden wird):
  - ``scripts&#47;utils&#47;get_github_token.sh --check``
- Verwendung in Scripts:
  - ``TOKEN="$(scripts&#47;utils&#47;get_github_token.sh)"``

Unterstützte Token-Formate:
- `gho_*`  (GitHub CLI OAuth Token)
- `ghp_*`  (Classic PAT)
- `github_pat_*` (Fine-grained PAT)

Token-Quellen (Priorität):
`GITHUB_TOKEN` → `GH_TOKEN` → macOS Clipboard (`pbpaste`) → `gh auth token`

Empfohlenes Setup:
- `gh auth login --web`
- Danach laufen Scripts ohne PAT-Erstellen/Löschen.

Security:
- Tokens niemals in Logs echo'en oder als "eigene Zeile" ins Terminal pasten.

---

## GitHub Branch Protection & Rulesets

**Operator Runbooks für Branch Protection, Required Checks und Review-Workflows.**

### Runbooks

- **[GitHub Rulesets: PR-Pflicht vs. Approving Reviews (inkl. mergeable UNKNOWN Quickflow)](runbooks/github_rulesets_pr_reviews_policy.md)** ⭐
  - Policy-Matrix: Solo-Dev vs. Team-Standard vs. Safety-Critical
  - Operator Quickflow: `mergeable: UNKNOWN` troubleshooting (6-Step)
  - UI-Klickpfade: Rulesets (modern) vs. Branch Protection Rules (legacy)
  - Best Practices: Required Check Materialisierung, Concurrency-Isolation
  - Referenz: PR #512 (CI required check robustness)

### Verwandte Docs

- CI Required Checks Naming Contract: [ci_required_checks_matrix_naming_contract.md](ci_required_checks_matrix_naming_contract.md)
- Branch Protection Snapshot: [BRANCH_PROTECTION_REQUIRED_CHECKS.md](BRANCH_PROTECTION_REQUIRED_CHECKS.md)
- Required Checks Drift Guard: [REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md](REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md)

---

## Verified Merge Logs
- **PR #745 (docs(ops): add PR #744 merge log)** → `PR_745_MERGE_LOG.md`

- **PR #744 (dashboard(web): watch-only control center v0.2 (read-only))** → `PR_744_MERGE_LOG.md`

- **PR #544 (Phase 8C: VaR Backtest Suite Runner & Report Formatter)** → ``docs&#47;ops&#47;merge_logs&#47;20260104_pr-544_var-backtest-suite-phase-8c.md``
- **PR #528 (restore: docs/fix-reference-targets-priority1 — Rebase & Branch Cleanup Demo)** → ``docs&#47;ops&#47;merge_logs&#47;2026-01-03_pr-528-rebase-cleanup-restore-demo.md``
- **PR #512 (CI required checks hardening: fail-open changes + PR concurrency)** → ``docs&#47;ops&#47;PR_512_MERGE_LOG.md``
- **PR #509 (Optuna/MLflow Tracking + Parameter Schema Restore from BK1)** → ``docs&#47;ops&#47;PR_509_MERGE_LOG.md``
- **PR #504 (WP5A Phase 5 NO-LIVE Drill Pack, governance-safe docs)** → ``docs&#47;ops&#47;PR_504_MERGE_LOG.md``
- **PR #501 (Cursor Timeout / Hang Triage Quick Start — Frontdoor)** → ``docs&#47;ops&#47;PR_501_MERGE_LOG.md``
- **PR #499 (Cursor timeout triage runbook; self-contained + log collector)** → ``docs&#47;ops&#47;PR_499_MERGE_LOG.md``
- **PR #497 (Canary Execution Override Validation Artifact, docs-only)** → ``docs&#47;ops&#47;PR_497_MERGE_LOG.md``
- **PR #491 (bg_job runner delivery + truth corrections)** → ``docs&#47;ops&#47;PR_491_MERGE_LOG.md``
- **PR #489 (docs(ops): standardize bg_job execution pattern in Cursor multi-agent workflows)** → ``docs&#47;ops&#47;PR_489_MERGE_LOG.md``
- **PR #488 (docs(ops): standardize bg_job execution pattern in cursor phases runbook)** → ``docs&#47;ops&#47;PR_488_MERGE_LOG.md``
- **PR #486 (chore(gitignore): ignore .logs from bg jobs)** → ``docs&#47;ops&#47;PR_486_MERGE_LOG.md``
- **PR #485 (docs(ops): docs reference targets parity + ignore list + priority fixes)** → ``docs&#47;ops&#47;PR_485_MERGE_LOG.md``
- **PR #483 (Merge Logs for PR #481 and #482, docs-only)** → ``docs&#47;ops&#47;PR_483_MERGE_LOG.md`` (meta: references #481, #482)
- **PR #482 (WP4B Operator Drills + Evidence Pack, Manual-Only)** → ``docs&#47;ops&#47;PR_482_MERGE_LOG.md``
- **PR #481 (Policy-Safe Hardening for Live Gating Docs + WP4A Templates)** → ``docs&#47;ops&#47;PR_481_MERGE_LOG.md``
- **PR #479 (Appendix A — Phase Runner Prompt Packs 0–3)** → docs/ops/PR_479_MERGE_LOG.md
- **PR #470 (Recon Audit Gate Wrapper: pyenv-safe Python Runner)** → ``docs&#47;ops&#47;PR_470_MERGE_LOG.md``
- **PR #462 (WP0D LedgerEntry Mapping + Reconciliation Wiring, Phase-0 Integration Day)** → ``docs&#47;ops&#47;PR_462_MERGE_LOG.md`` | [Integration Report](integration_days/PHASE0_ID0_WP0D_INTEGRATION_DAY_REPORT.md)
- **PR #458 (WP0E Contracts & Interfaces, Phase-0 Gate Report)** → ``docs&#47;ops&#47;PR_458_MERGE_LOG.md``
- **PR #456 (Phase-0 A0 Integration Sweep, finalize status)** → ``docs&#47;ops&#47;PR_456_MERGE_LOG.md``
- **PR #454 (Docs Reference Targets Gate style guide)** → ``docs&#47;ops&#47;PR_454_MERGE_LOG.md``
- **PR #448 (Docs Reference Gate – Escape path separators, Phase 3)** → ``docs&#47;ops&#47;PR_448_MERGE_LOG.md``
- **PR #447 (Docs Reference Gate – Deprecate inspect_offline_feed, Phase 2)** → ``docs&#47;ops&#47;PR_447_MERGE_LOG.md``
- **PR #446 (Docs Reference Gate – Fix moved script paths, Phase 1)** → ``docs&#47;ops&#47;PR_446_MERGE_LOG.md``
- **PR #442 (Audit remediation summary for PR #441, verified)** → ``docs&#47;ops&#47;PR_442_MERGE_LOG.md``
- **PR #426** → ``docs&#47;ops&#47;PR_426_MERGE_LOG.md``
- **PR #424** → ``docs&#47;ops&#47;PR_424_MERGE_LOG.md``
- **PR #418 (Kupiec POF Phase-7 convenience API, verified)** → ``docs&#47;ops&#47;PR_418_MERGE_LOG.md``
- **PR #413 (VaR Validation Phase 2 (Kupiec + Traffic Light), verified)** → ``docs&#47;ops&#47;PR_413_MERGE_LOG.md``
- **PR #409 (Kill Switch Legacy Adapter, verified)** → ``docs&#47;ops&#47;PR_409_MERGE_LOG.md``

**Style Guide:** [MERGE_LOGS_STYLE_GUIDE.md](MERGE_LOGS_STYLE_GUIDE.md) — Gate-safe formatting, de-pathify rules, Unicode hygiene


## Merge Logs

Post-merge documentation logs for operational PRs.

- [PR #664](PR_664_MERGE_LOG.md) — fix(ci): offline_suites workflow_dispatch input context (merged 2026-01-12) <!-- PR-664-MERGE-LOG -->
- [PR #663](PR_663_MERGE_LOG.md) — fix(ci): Phase 5B workflow dispatch condition (merged 2026-01-12) <!-- PR-663-MERGE-LOG -->
- [PR #628](PR_628_MERGE_LOG.md) — docs(ops): AI Autonomy 4B M2 drill session template + scorecard standard (merged 2026-01-09) <!-- PR-628-MERGE-LOG -->
- [PR #551](PR_551_MERGE_LOG.md) — fix(pr-531): restore green CI (normalize research markers/IDs) (merged 2026-01-04) <!-- PR-551-MERGE-LOG -->
- [PR #599](PR_599_MERGE_LOG.md) — docs(ops): add audit artifacts v0 (evidence index + risk register) (merged 2026-01-07) <!-- PR-599-MERGE-LOG -->
- [PR #596](PR_596_MERGE_LOG.md) — docs(ops): add placeholder standards v0 (policy + deterministic generator) (merged 2026-01-07) <!-- PR-596-MERGE-LOG -->
- [PR #429](PR_429_MERGE_LOG.md) — docs(risk): Phase 11 – VaR Backtest Suite UX & Docs-Verkabelung (merged 2025-12-29) <!-- PR-429-MERGE-LOG -->
- PR 1080 — [PR_1080_MERGE_LOG.md](merge_logs/PR_1080_MERGE_LOG.md)

### Closeout Logs

Documentation for PRs closed without merge (superseded, redundant, or obsolete).

- [PR #321](PR_321_CLOSEOUT_LOG.md) — feat/risk: parametric Component VaR MVP (CLOSED / SUPERSEDED BY PR #408, 2026-01-03)

## Specs
- Project Summary Outline V2: `docs/ops/specs/PEAK_TRADE_PROJECT_SUMMARY_OUTLINE_V2.md`
