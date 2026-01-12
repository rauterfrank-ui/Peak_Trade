# Document Map: Workflow Documentation Integration

**Session:** 2026-01-12 Workflow Docs Integration  
**ORCHESTRATOR:** Multi-Agent Session  
**SCOPE_KEEPER:** KEEP EVERYTHING from both documents

---

## Documents in Scope

### Document 1: WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md

**Location:** `/Users/frnkhrz/Peak_Trade/WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` (repo root)  
**Purpose:** Comprehensive overview of all workflow and runbook documentation in Peak_Trade  
**Owner:** Operations / Documentation Team  
**Last Updated:** 2026-01-12  
**Version:** v1.0  
**Size:** 824 lines  
**Language:** German

**Scope & Content:**
- **Executive Summary:** 18+ CLI command sections, 12+ runbooks, Control Center with Layer Matrix (L0-L6), 100+ PR Merge Logs
- **Section 1 (CLI Cheatsheet):** 18 main sections covering backtests, portfolios, sweeps, live workflows, monitoring, alerts, web dashboard
- **Section 2 (Wave3 Control Center Cheatsheet v2):** PR-Queue Management (Top 10), Pre-Flight Checks, Decision Tree, Evidence v0.1
- **Section 3 (AI Autonomy Control Center Operator Cheatsheet):** Daily routine (5-10 min), timeout-safe monitoring, triage shortcuts
- **Section 4 (Detailed Runbooks):** LIVE_OPERATIONAL_RUNBOOKS.md (12+ runbooks), RUNBOOKS_LANDSCAPE_2026_READY.md, RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md
- **Section 5 (Operations Structure):** `docs/ops/` directory overview (Control Center, Evidence, CI/CD, Merge Logs, Runbooks, Guides, Wave Management)
- **Section 6 (Workflow Documentation):** WORKFLOW_NOTES.md summary
- **Section 7 (Current Work Focus):** Control Center (Wave3), PR-Management, Evidence v0.1
- **Section 8 (Quick-Access Overview):** Central entry points (10 key documents)
- **Section 9 (Important CLI Commands):** Daily operations, shadow/testnet sessions, monitoring & alerts, backtests & research, system checks
- **Section 10 (Status Summary):** Documentation status table, architecture principles, tool availability
- **Section 11 (Checklists):** Daily operator checklist, pre-session, post-session, PR-merge, incident-response
- **Section 12 (References & Cross-Links):** Governance & Safety, CI/CD, Evidence & Audit, Phase Documentation
- **Section 13 (Changelog):** Version history
- **Section 14 (Support & Contact):** Escalation paths

**Authority:** **AUTHORITATIVE** (2026-ready, comprehensive, current operational reference)

**Target Audience:**
- Operators (daily routine, monitoring)
- Developers (CLI commands, backtests)
- PR Managers (Wave3 queue, merge workflow)
- Research Team (experiment workflows)

**Unique Content (not in WORKFLOW_NOTES.md):**
- Wave3 Control Center details (PR queue, Top 10 PRs)
- AI Autonomy Control Center operator cheatsheet
- Detailed runbook catalog (12+ runbooks with command examples)
- Operations structure (`docs/ops/` hierarchy)
- Current work focus (Wave3, Evidence v0.1)
- Comprehensive checklists (5 types)
- CLI command reference (100+ commands)
- Status summary tables (documentation, architecture, tools)
- Cross-links to governance, CI/CD, evidence, audit

---

### Document 2: docs/WORKFLOW_NOTES.md

**Location:** `/Users/frnkhrz/Peak_Trade/docs/WORKFLOW_NOTES.md`  
**Purpose:** ChatGPT ↔ Claude Code ↔ Repo Workflow documentation (legacy snapshot)  
**Owner:** Frank (Project Owner) + ChatGPT Co-Pilot  
**Last Updated:** 2025-12-03  
**Version:** (implicit v0.1, no explicit version)  
**Size:** 178 lines  
**Language:** German

**Scope & Content:**
- **Section 1 (Technical Status):** Data Layer, Strategy Layer, Core Layer, Backtest Layer, Strategy Registry, Runner status (as of Dec 2025)
- **Section 2 (Workflow):** Role split (Frank/ChatGPT/Claude Code), typical workflow cycle, style rules for prompts
- **Section 3 (Next Block):** Planned next work (Docs & Architecture)
- **Section 4 (Usage Instructions):** How to use this file as a snapshot and continuation point

**Authority:** **LEGACY SNAPSHOT** (Dec 2025, historical context, not current operational reference)

**Target Audience:**
- Frank (owner, continuation context)
- ChatGPT Co-Pilot (prompt generation context)
- Claude Code (execution context)

**Unique Content (not in WORKFLOW_RUNBOOK_OVERVIEW):**
- Detailed technical layer status (Data/Strategy/Core/Backtest/Registry/Runner) as of Dec 2025
- Explicit role split (Frank/ChatGPT/Claude Code)
- Prompt style rules and conventions
- Workflow cycle mechanics (block-by-block iteration)
- Continuation instructions

---

## Overlap Analysis

### Shared Themes
- Both documents describe **workflows** in Peak_Trade
- Both are in **German**
- Both reference **docs/** and **scripts/** paths

### Content Overlap
- **WORKFLOW_RUNBOOK_OVERVIEW Section 6** summarizes WORKFLOW_NOTES.md (50 lines summary)
- No direct text duplication (different perspectives)

### Non-Overlapping Content

**WORKFLOW_RUNBOOK_OVERVIEW (unique):**
- Operational runbooks (12+ detailed runbooks)
- Control Center operations (Wave3, AI Autonomy)
- PR-Management workflows (Top 10 queue)
- Evidence system (index, schema, templates)
- CI/CD gates and checks
- Checklists (5 types)
- Comprehensive CLI reference
- Status tables and metrics
- 2026-ready operational reference

**WORKFLOW_NOTES (unique):**
- Technical layer implementation details (Data/Strategy/Core/Backtest)
- Frank/ChatGPT/Claude Code role mechanics
- Prompt generation conventions
- Block-by-block iteration workflow
- Dec 2025 technical snapshot

---

## Positioning Strategy

### Authoritative vs. Legacy

**WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md:**
- **Status:** AUTHORITATIVE, 2026-READY, OPERATIONAL REFERENCE
- **Use Case:** Day-to-day operations, runbook navigation, CLI reference, PR management
- **Audience:** Operators, Developers, PR Managers
- **Update Frequency:** Quarterly or after major workflow/runbook changes

**docs/WORKFLOW_NOTES.md:**
- **Status:** LEGACY SNAPSHOT (Dec 2025), HISTORICAL CONTEXT
- **Use Case:** Understanding historical technical state, Frank/ChatGPT/Claude workflow mechanics, continuation context for chat-based development sessions
- **Audience:** Frank (owner), ChatGPT Co-Pilot, historical reference
- **Update Frequency:** As needed for chat-based development session continuity

### Integration Strategy

**Option A (Recommended):** Preserve both with clear positioning
- Keep WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md as primary operational reference
- Keep docs/WORKFLOW_NOTES.md as legacy/historical snapshot with explicit "Dec 2025 snapshot" notice
- Link both from a new **docs/WORKFLOW_FRONTDOOR.md** with clear "Authoritative vs. Legacy" labels
- Add both to `docs/ops/README.md` navigation

**Option B (Alternative):** Merge technical layer details into WORKFLOW_RUNBOOK_OVERVIEW
- Risk: Loses the historical snapshot context
- Benefit: Single source of truth
- Verdict: REJECTED (violates SCOPE_KEEPER: KEEP EVERYTHING)

**Selected Strategy:** **Option A** (Preserve both, clear positioning, navigation integration)

---

## Next Steps (Phase 2)

1. **BACKTICK_AUDIT.md:** Identify all inline backticks with "/" in both documents
2. **Classify:** Real path / branch / placeholder / URL / local path / command
3. **Gate Impact:** Determine which tokens would fail docs-reference-targets-gate
4. **Fix Matrix:** Propose fixes (HTML entity slash, zero-width breaks, or other escaping)

---

**SCOPE_KEEPER Sign-Off:** ✅ NO CONTENT DELETION from either document, both preserved in full
