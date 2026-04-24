# Workflow Documentation – Frontdoor

**Purpose:** Central navigation hub for Peak_Trade workflow and runbook documentation  
**Last Updated:** 2026-01-12  
**Target Audience:** Operators, Developers, PR Managers, Research Team

---

## 🎯 Quick Navigation

### 📘 Authoritative: Operational Reference (2026-Ready)

**[WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md](../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md)**

**Status:** ✅ AUTHORITATIVE, 2026-READY, CURRENT OPERATIONAL REFERENCE  
**Version:** v1.0 (2026-01-12)  
**Size:** 824 lines  
**Use Case:** Day-to-day operations, runbook navigation, CLI reference, PR management

**Key Content:**
- **18+ CLI Command Sections:** Complete command reference for all operations
- **12+ Standard & Incident Runbooks:** [LIVE_OPERATIONAL_RUNBOOKS.md](LIVE_OPERATIONAL_RUNBOOKS.md) catalog
- **Wave3 Control Center:** PR queue management (Top 10), decision trees
- **AI Autonomy Control Center:** Operator cheatsheet (daily routine, triage)
- **Operations Structure:** Complete [docs/ops/](./ops/README.md) hierarchy and navigation
- **Evidence System:** Evidence index, schema, templates (v0.1)
- **5 Checklists:** Daily operator, pre-session, post-session, PR-merge, incident-response
- **Status Tables:** Documentation status, architecture principles, tool availability
- **Cross-Links:** Governance, CI/CD, evidence, audit, phase documentation

**When to Use:**
- Daily operations and monitoring
- Finding the right runbook for your situation
- CLI command lookup
- PR management workflow
- Evidence and audit trail navigation
- Control Center operations

---

### 📙 Legacy: Historical Context & Chat Workflow (Dec 2025 Snapshot)

**[docs/WORKFLOW_NOTES.md](./WORKFLOW_NOTES.md)**

**Status:** 🕰️ LEGACY SNAPSHOT (Dec 2025), HISTORICAL CONTEXT  
**Version:** (implicit v0.1)  
**Size:** 178 lines  
**Use Case:** Understanding historical technical state, Frank/ChatGPT/Claude workflow mechanics, continuation context for chat-based development sessions

**[Peak_Trade_WORKFLOW_NOTES.md (Legacy Snapshot 2025-12-03, KEEP EVERYTHING)](./ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md)**

**Status:** 🕰️ LEGACY SNAPSHOT (Dec 2025), ARCHIVED (KEEP EVERYTHING)  
**Use Case:** Stable, linkable archival copy of the legacy workflow notes (token-policy-safe, docs-gates-compatible)

**Key Content:**
- **Technical Layer Status (Dec 2025):** Data Layer, Strategy Layer, Core Layer, Backtest Layer, Strategy Registry, Runner implementation details
- **Frank/ChatGPT/Claude Code Workflow:** Role split, typical workflow cycle, block-by-block iteration mechanics
- **Prompt Style Rules:** Conventions for generating Claude Code prompts (German, technical precision, structured sections)
- **Continuation Instructions:** How to resume chat-based development sessions

**When to Use:**
- Understanding the state of technical layers as of Dec 2025
- Learning the Frank/ChatGPT/Claude Code collaboration mechanics
- Generating prompts for Claude Code in the established style
- Resuming a chat-based development session with historical context
- Historical reference for architecture decisions

---

### Installation & Setup (2026-ready)

- [Vollständiger Installation-&-Roadmap-Snapshot (2026-01-12)](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md)
- [Installation Quickstart](./INSTALLATION_QUICKSTART.md)

---

## 🗺️ Related Documentation

### Operations & Runbooks
- **Chat-led open features / gap discovery:** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](./ops/runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — backlog triage (NO-LIVE; assistant-led sessions, not shell-command lists)
- **Chat continuity bootstrap (new ChatGPT/Cursor session):** [PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md](./ops/runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md) — copy-paste session bootstrap, including Bounded-Pilot / First-Live navigation context; **navigation-only** (no live authorization, gate bypass, or runtime, trading, evidence, approval, or live-entry semantics change).
- **Unimplemented features (ordered backlog):** [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](./ops/runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) — deep-scan snapshot + logical staging (NO-LIVE)
- **Release checklist / Go–No-Go (Finish Plan [PR 8](./ops/roadmap/FINISH_PLAN.md#pr-8-release-checklist-gono-go-rubric-docs-only), docs-only, NO unlocks):** [Release docs (index)](./ops/release/README.md) · [Checklist & rubric](./ops/release/runbooks/RELEASE_CHECKLIST_AND_GO_NO_GO_RUBRIC.md)
- **Observability / status reports (Finish Plan [PR 7](./ops/roadmap/FINISH_PLAN.md#pr-7-observabilitystatus-report-hardening-code-docs), snapshot-only, NO unlocks):** [Live Status Reports](./LIVE_STATUS_REPORTS.md) (Daily/Weekly) · [`generate_live_status_report.py`](../scripts/generate_live_status_report.py) (CLI) · [`prj_status_report.py`](../scripts/ci/prj_status_report.py) (CI PR-J artifacts)
- **Live-Ops runbook pack (Finish Plan [PR 6](./ops/roadmap/FINISH_PLAN.md#pr-6-live-ops-runbook-pack-docs-only), docs-only, NO unlocks):** [Live Operational Runbooks](./LIVE_OPERATIONAL_RUNBOOKS.md) (Start/Stop, Standard- & Incident-Katalog) · [Incident Simulation & Drills](./INCIDENT_SIMULATION_AND_DRILLS.md) (kontrollierte Übungen) · [Safety Policy Testnet & Live](./SAFETY_POLICY_TESTNET_AND_LIVE.md) (Anforderungen vor Testnet/Live)
- [Live Operational Runbooks](./LIVE_OPERATIONAL_RUNBOOKS.md) – 12+ runbooks for live operations and incident handling
- [Runbooks Landscape 2026-Ready](./runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md) – Comprehensive runbook catalog and quick-reference matrix
- [Ops README](./ops/README.md) – Complete ops tools and documentation index
- [Master V2 First Live Enablement Readiness Ladder (canonical)](./ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) – Bindende kanonische Steuerdatei fuer den aktuellen Clarification-Workstream
- [Tech-Debt Top-3 ROI bis Finish Runbook](./ops/runbooks/RUNBOOK_TECH_DEBT_TOP3_ROI_FINISH.md) – 3 kleine PRs (C/B/E) bis Finish, Cursor Multi-Agent, NO-LIVE
- [RUNBOOK_BRANCH_CLEANUP_RECOVERY.md](./ops/runbooks/RUNBOOK_BRANCH_CLEANUP_RECOVERY.md) – Branch cleanup recovery (tags + bundles)
- [Execution Watch Dashboard v0.2 Runbook](./ops/runbooks/RUNBOOK_EXECUTION_WATCH_DEMO_STACK.md) – Start/verify the read-only execution watch dashboard
- [Phase 7 Finish/Closeout Runbook](./ops/runbooks/RUNBOOK_PHASE7_WORKFLOW_DOCS_FINISH_CLOSEOUT_2026-01-12_CURSOR_MULTI_AGENT.md) – Workflow docs closeout + repo hygiene inventory (snapshot-based)
- [Finish Plan (MVP→v1.0)](./ops/roadmap/FINISH_PLAN.md)
- [Finish Runbook A (MVP)](./ops/runbooks/RUNBOOK_FINISH_A_MVP.md) – Backtest → Artifacts → Report → Watch‑Only Dashboard (snapshot-only, NO‑LIVE)
- [Finish C Master Runbook](./ops/runbooks/finish_c/RUNBOOK_FINISH_C_MASTER.md) – Finish C (docs gates maintenance + evidence workflow)

### Control Center
- [AI Autonomy Control Center](./ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md) – Primary control center entry point (Layer L0-L6)
- [Control Center Navigation](./ops/control_center/CONTROL_CENTER_NAV.md) – Navigation for control center artifacts

### Configuration
- [Config-Import-Leitfaden (Peak / Pydantic / Registry / simple)](./project_docs/CONFIG_IMPORT_GUIDE.md) — zentraler Einstieg für Loader- und Import-Semantik

### CLI & Commands
- [CLI Cheatsheet](./CLI_CHEATSHEET.md) – Complete CLI command reference (18 sections, 690 lines)
- [Dev Workflow Shortcuts](./DEV_WORKFLOW_SHORTCUTS.md) – Quick command snippets for development

### Evidence & Audit
- [Evidence Index](./ops/EVIDENCE_INDEX.md) – Central evidence registry
- [Evidence Schema](./ops/EVIDENCE_SCHEMA.md) – Evidence artifact schema and validation rules

### Archives & Cleanup
- [Repo Cleanup Inventory (Snapshots)](./ops/_archive/repo_cleanup/2026-01-12/README.md) – Snapshot-based repo hygiene inventory (no actions without approval)

### Governance & Safety
- **NO-LIVE default posture** (research/backtest/paper/shadow; no live orders by default): [Governance and Safety Overview](./GOVERNANCE_AND_SAFETY_OVERVIEW.md) · [Finish Plan — Stop Rules](./ops/roadmap/FINISH_PLAN.md#stop-rules-non-negotiable)
- **Kill-Switch posture + Docs Gates (MVP evidence):** [Governance and Safety Overview](./GOVERNANCE_AND_SAFETY_OVERVIEW.md) · [README Kill Switch](../README_KILL_SWITCH.md) · [Finish Plan — Level A MVP](./ops/roadmap/FINISH_PLAN.md#finish-level-a-level-a-mvp)
- [Governance and Safety Overview](./GOVERNANCE_AND_SAFETY_OVERVIEW.md) – Governance framework and roles
- [Safety Policy Testnet and Live](./SAFETY_POLICY_TESTNET_AND_LIVE.md) – Safety policies for testing and live operations

---

## 📊 Document Comparison

| Aspect | WORKFLOW_RUNBOOK_OVERVIEW | WORKFLOW_NOTES |
|--------|---------------------------|----------------|
| **Status** | ✅ Authoritative (2026) | 🕰️ Legacy (Dec 2025) |
| **Size** | 824 lines | 178 lines |
| **Scope** | Operational workflows, runbooks, CLI, PR management | Technical layers, chat workflow mechanics |
| **Audience** | Operators, Developers, PR Managers | Frank, ChatGPT Co-Pilot |
| **Update Frequency** | Quarterly or after major changes | As needed for chat sessions |
| **Primary Use Case** | Day-to-day operations | Historical context, chat continuity |

---

## 🚀 Getting Started

### For Operators (Daily Routine)
1. Start with [WORKFLOW_RUNBOOK_OVERVIEW](../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md) Section 3 (AI Autonomy Control Center Operator Cheatsheet)
2. Follow the daily routine (5-10 minutes)
3. Use checklists in Section 11 as needed

### For Developers (CLI Commands)
1. Bookmark [CLI Cheatsheet](./CLI_CHEATSHEET.md) for quick command lookup
2. Refer to [WORKFLOW_RUNBOOK_OVERVIEW](../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md) Section 9 for complete command reference with examples

### For PR Managers (Wave3 Queue)
1. Start with [WORKFLOW_RUNBOOK_OVERVIEW](../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md) Section 2 (Wave3 Control Center Cheatsheet v2)
2. Follow decision trees for MERGEABLE / CONFLICTING PRs
3. Use PR-merge checklist (Section 11)

### For Research Team
1. [CLI Cheatsheet](./CLI_CHEATSHEET.md) Sections 2.1, 3-5 (Portfolio recipes, sweeps, market scans)
2. [WORKFLOW_RUNBOOK_OVERVIEW](../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md) Section 9 (Backtests & Research commands)

---

## 📝 Maintenance

**WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md:**
- Update quarterly or after major workflow/runbook changes
- Version bump on significant structural changes
- Maintain changelog (Section 13)

**docs/WORKFLOW_NOTES.md:**
- Update as needed for chat-based development session continuity
- Consider archiving and creating new snapshot if technical state diverges significantly

---

## 📞 Support

For questions or issues:
1. Check the appropriate workflow document (Authoritative vs. Legacy)
2. Consult relevant runbook from [LIVE_OPERATIONAL_RUNBOOKS.md](./LIVE_OPERATIONAL_RUNBOOKS.md)
3. Review [Control Center](./ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md) for operational context
4. Escalate via [Ops README](./ops/README.md) contacts if needed

---

**Last Updated:** 2026-01-12  
**Next Review:** Q2 2026 or after major workflow changes
