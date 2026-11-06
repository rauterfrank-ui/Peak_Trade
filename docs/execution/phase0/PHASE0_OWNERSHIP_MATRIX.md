# Phase-0 Ownership Matrix (A0-Only)

**Version:** 1.0  
**Date:** 2025-12-31  
**Status:** DRAFT (Docs-Only Run)  
**Source:** docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md + docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md

---

## Anchoring Note (Appendix E)

**Scope:** Docs-only preparation for Phase-0 Foundation. No src/ or tests/ changes in this run.  
**Out-of-Scope:** Code implementation, live enablement, activation instructions.  
**Stop Criteria:** Any agent modifies src/tests/, adds live-enablement, creates broken links, or deviates from Frontdoor/Roadmap without "Assumption" marker.  
**Evidence:** 8 markdown files in docs/execution/phase0/, link-hygiene passed, gate-self-check.

---

## Work Package Ownership

| WP-ID | Owner | Work Package | Ownership (Docs) | Shared-Files (A0-Only) | Out-of-Scope |
|-------|-------|--------------|------------------|------------------------|--------------|
| **WP0E** | A1 (Exec-Agent) | Contracts & Interfaces | `docs/execution/phase0/WP0E_TASK_PACKET.md` | This matrix, integration plan, gate report | Code implementation, src/ changes |
| **WP0A** | A2 (Pipeline-Agent) | Execution Core v1 | `docs/execution/phase0/WP0A_TASK_PACKET.md` | This matrix, integration plan, gate report | Code implementation, src/ changes |
| **WP0B** | A3 (Risk-Agent) | Risk Layer v1.0 | `docs/execution/phase0/WP0B_TASK_PACKET.md` | This matrix, integration plan, gate report | Code implementation, src/ changes |
| **WP0C** | A4 (Routing-Agent) | Order Routing/Adapter Layer | `docs/execution/phase0/WP0C_TASK_PACKET.md` | This matrix, integration plan, gate report | Code implementation, src/ changes |
| **WP0D** | A5 (Recon-Agent) | Recon/Ledger/Accounting Bridge | `docs/execution/phase0/WP0D_TASK_PACKET.md` | This matrix, integration plan, gate report | Code implementation, src/ changes |

---

## Shared-Files (A0-Only Access)

These files may ONLY be modified by A0 (Orchestrator). Agents provide text as patch suggestions if edits needed.

| File | Owner | Purpose |
|------|-------|---------|
| `PHASE0_OWNERSHIP_MATRIX.md` | A0 | Define file ownership + boundaries |
| `PHASE0_INTEGRATION_DAY_PLAN.md` | A0 | Integration sequence + conflict resolution |
| `PHASE0_GATE_REPORT_TEMPLATE.md` | A0 | GO/NO-GO readiness template |

---

## File Modification Rules (Docs-Only)

### Agent Rules
1. **One File Per Agent:** Each agent modifies ONLY their assigned WP*_TASK_PACKET.md
2. **No Cross-Edits:** Agents do NOT edit other agents' task packets
3. **No Shared-File Direct Edits:** Agents provide patches to A0 for shared-files
4. **Link Hygiene:** All links must point to existing files (or files created in this PR)

### A0 Rules
1. **Shared-Files Owner:** A0 is sole editor of OWNERSHIP_MATRIX, INTEGRATION_DAY_PLAN, GATE_REPORT_TEMPLATE
2. **Integration Sweep:** A0 performs link-hygiene check before PR finalization
3. **Conflict Resolution:** If agents need same section → A0 integrates manually

---

## Reference Files (Source-of-Truth, Read-Only)

These files exist in the repo and are **read-only** for this run:

| File | Status | Purpose |
|------|--------|---------|
| `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md` | ✅ EXISTS | Process source-of-truth (Appendix E, F) |
| `docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md` | ✅ EXISTS | Content source-of-truth (Phase-0 WPs) |
| `docs/execution/WP0E_COMPLETION_REPORT.md` | ✅ EXISTS | Reference for WP0E scope (Contracts already implemented) |
| `docs/execution/WP0A_COMPLETION_REPORT.md` | ✅ EXISTS | Reference for WP0A scope (Execution Core already implemented) |

---

## Dependency Graph (Docs-Only)

```
WP0E (Contracts)
   ↓
WP0A (Execution Core)
   ↓
WP0B (Risk Runtime) ← depends on WP0E contracts
   ↓
WP0C (Order Routing) ← depends on WP0A + WP0B
   ↓
WP0D (Recon/Ledger) ← depends on WP0A + WP0C
```

**Integration Sequence:** WP0E → WP0A → WP0B → WP0C → WP0D (sequential for clarity; parallel-safe if no overlaps)

---

## Conflict Prevention

### If Two Agents Need Same Info:
1. Agent identifies conflict and notifies A0 (Lock-Request)
2. A0 creates shared definition in Integration Day Plan
3. Agents reference A0's definition (no duplication)

### If Link Target Unclear:
1. Agent asks A0: "Does file X exist?"
2. A0 verifies + updates this matrix
3. Agent proceeds with confirmed link

---

## Link Hygiene Checklist (A0 Final Sweep)

Before PR finalization, A0 verifies:
- [ ] All intra-PR links point to files created in this PR
- [ ] All external links point to existing repo files
- [ ] No links to non-existent targets
- [ ] No links to src/ or tests/ (out-of-scope)
- [ ] No "TODO: add link" placeholders

---

## Status Tracking

| WP | Agent | Status | Last Updated | Evidence |
|----|-------|--------|--------------|----------|
| WP0E | A1 | PENDING | - | - |
| WP0A | A2 | PENDING | - | - |
| WP0B | A3 | PENDING | - | - |
| WP0C | A4 | PENDING | - | - |
| WP0D | A5 | PENDING | - | - |

---

**Ownership Matrix Status:** INITIALIZED (A0)  
**Next:** Agents fill their respective WP*_TASK_PACKET.md files.
