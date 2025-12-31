# Phase-0 Integration Day Plan (A0-Only)

**Version:** 1.0  
**Date:** 2025-12-31  
**Status:** DRAFT (Docs-Only Run)  
**Source:** docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md Appendix F.6

---

## Anchoring Note (Appendix E)

**Run Scope:** Docs-only preparation for Phase-0 Foundation. This run creates specifications; code implementation follows in separate PR.  
**Out-of-Scope:** Code changes (src/, tests/), live enablement, activation instructions.  
**Stop Criteria:** Agent modifies src/tests/, adds live-enablement, creates broken links, deviates from Frontdoor/Roadmap without clear "Assumption".  
**Evidence Required:** 8 markdown files, link-hygiene passed, gate-self-check complete.

---

## Integration Objective

**Goal:** Integrate 5 WP Task-Packet specifications + 3 Shared-Files into ONE docs-only PR with zero merge conflicts and full link-hygiene compliance.

**Constraints:**
- Docs-only (no src/, no tests/)
- No live-enablement language
- All links must point to existing or PR-created files
- All statements must trace back to Frontdoor/Roadmap

---

## Integration Sequence

### Step 1: A0 Initialization (COMPLETE)
- [x] Create `docs/execution/phase0/` directory
- [x] Create branch "docs/phase0-foundation-prep"
- [x] Initialize 3 shared-files:
  - `PHASE0_OWNERSHIP_MATRIX.md`
  - `PHASE0_INTEGRATION_DAY_PLAN.md` (this file)
  - `PHASE0_GATE_REPORT_TEMPLATE.md`
- [x] Initialize 5 empty WP task-packet files

### Step 2: Agent Execution (PARALLEL-SAFE)
- [ ] A1 fills `WP0E_TASK_PACKET.md` (Contracts & Interfaces)
- [ ] A2 fills `WP0A_TASK_PACKET.md` (Execution Core v1)
- [ ] A3 fills `WP0B_TASK_PACKET.md` (Risk Layer v1.0)
- [ ] A4 fills `WP0C_TASK_PACKET.md` (Order Routing/Adapter Layer)
- [ ] A5 fills `WP0D_TASK_PACKET.md` (Recon/Ledger/Accounting Bridge)

**Conflict Prevention:** Each agent edits ONLY their own file. No cross-edits.

### Step 3: A0 Link-Hygiene Sweep
- [ ] Verify all intra-PR links (e.g., `WP0E_TASK_PACKET.md` → `WP0A_TASK_PACKET.md`)
- [ ] Verify all external links (e.g., links to Frontdoor/Roadmap)
- [ ] Check for broken links (docs-reference-targets-gate compliance)
- [ ] Fix any link issues or request agent corrections

### Step 4: A0 Integration Notes Consolidation
- [ ] Collect "Integration Notes" from all WP task-packets
- [ ] Identify cross-WP dependencies
- [ ] Document integration sequence (for future implementation run)
- [ ] Update Ownership Matrix with status

### Step 5: A0 Gate Report Pre-Fill
- [ ] Fill `PHASE0_GATE_REPORT_TEMPLATE.md` with WP status
- [ ] Mark docs-only readiness
- [ ] List any open questions / assumptions
- [ ] Prepare GO/NO-GO recommendation

### Step 6: PR Finalization
- [ ] Commit all files
- [ ] Run linter (ruff format --check docs/)
- [ ] Verify CI expectations (docs-reference-targets-gate, policy-critic-gate)
- [ ] Create PR with full PR-Contract (Frontdoor Section 5)
- [ ] Request review (A5 as Policy Critic)

---

## Merge Sequence (Within PR)

**Order (for clarity; all parallel-safe since no file overlaps):**

1. **Shared-Files First (A0):**
   - `PHASE0_OWNERSHIP_MATRIX.md`
   - `PHASE0_INTEGRATION_DAY_PLAN.md`
   - `PHASE0_GATE_REPORT_TEMPLATE.md`

2. **Task-Packets (Sequential for dependencies):**
   - `WP0E_TASK_PACKET.md` (Contracts — foundation)
   - `WP0A_TASK_PACKET.md` (Execution Core — depends on WP0E)
   - `WP0B_TASK_PACKET.md` (Risk Layer — depends on WP0E)
   - `WP0C_TASK_PACKET.md` (Order Routing — depends on WP0A/WP0B)
   - `WP0D_TASK_PACKET.md` (Recon/Ledger — depends on WP0A/WP0C)

**Note:** Since this is docs-only, merge sequence is informational (for future implementation planning). All files can be committed in one batch.

---

## Conflict Resolution Rules

### Rule 1: No File Overlaps
Each agent owns ONE file. No conflicts possible if agents follow ownership.

### Rule 2: Shared Definition Requests
If Agent needs definition from shared-file:
1. Agent asks A0 via "Lock-Request"
2. A0 adds definition to this Integration Day Plan
3. Agent references A0's definition (no duplication)

### Rule 3: Cross-WP References
If WP-A needs to reference WP-B:
- Use relative link: `[WP0B](./WP0B_TASK_PACKET.md)`
- Ensure target file exists in PR
- A0 verifies link-hygiene before PR submission

---

## Integration Checklist (A0 Final)

### Pre-PR Submission
- [ ] All 8 files created and committed
- [ ] All agents completed their assignments
- [ ] Link-hygiene sweep passed (no broken links)
- [ ] No src/ or tests/ changes
- [ ] No live-enablement language
- [ ] All statements traceable to Frontdoor/Roadmap
- [ ] Gate report pre-filled

### CI Expectations
- [ ] `ruff format --check docs/` passes
- [ ] `docs-reference-targets-gate` passes
- [ ] `policy-critic-gate` passes (no live-enablement violations)
- [ ] `docs-diff-guard-policy-gate` passes

---

## Cross-WP Dependencies (Docs-Only)

### WP0E (Contracts) → WP0A/B/C/D
**Provides:** Type definitions, interfaces, protocols  
**Integration Note:** All other WPs reference WP0E contracts. Implementation run must build WP0E first.

### WP0A (Execution Core) → WP0C/D
**Provides:** Order state machine, ledger interfaces  
**Integration Note:** WP0C (routing) and WP0D (recon) depend on WP0A ledger/state definitions.

### WP0B (Risk Layer) → WP0C
**Provides:** Risk hook interface, risk decisions  
**Integration Note:** WP0C (routing) integrates risk checks before order submission.

### WP0C (Order Routing) → WP0D
**Provides:** Order execution results, fill events  
**Integration Note:** WP0D (recon) consumes WP0C execution results for reconciliation.

---

## Implementation Run Sequence (Future)

**Note:** This is docs-only. Implementation happens in separate PR(s).

**Recommended Implementation Order:**
1. **WP0E First (Blocker):** Implement contracts, types, interfaces
2. **Parallel (after WP0E):** WP0A (Execution Core) + WP0B (Risk Layer)
3. **Sequential (after WP0A/B):** WP0C (Order Routing) → WP0D (Recon/Ledger)

**Evidence Requirements (Implementation Run):**
- Unit tests per WP (pytest)
- Integration smoke tests
- Evidence reports in `reports/execution/*` (gitignored)
- Completion reports (like existing WP0E/WP0A completion reports)

---

## Open Questions / Assumptions

### Assumption 1: Existing WP0E/WP0A Code
**Question:** WP0E and WP0A completion reports exist. Are they part of Phase-0 or already complete?  
**Assumption:** They are already implemented. This docs-run focuses on WP0B/C/D specs + consolidation.  
**Action:** A0 reviews completion reports and aligns task-packets with existing implementations.

### Assumption 2: Observability Scope (WP0D vs separate WP)
**Question:** Roadmap mentions "Observability Minimum" as WP0D, but user assigned WP0D to "Recon/Ledger".  
**Assumption:** User's assignment takes precedence. Observability is deferred or part of WP0A/B/C cross-cutting.  
**Action:** A0 clarifies with user if ambiguity persists.

---

## Stop Conditions (Abort Integration)

If ANY of these occur, stop immediately and escalate to user:
1. Any agent modified `src/` or `tests/`
2. Any agent added live-enablement instructions
3. Any agent created links to non-existent targets (without creating target in PR)
4. Unresolvable conflict between agents (e.g., both want same section)
5. Deviation from Frontdoor/Roadmap without clear "Assumption" + justification

---

## Integration Day Status

| Stage | Status | Completed | Notes |
|-------|--------|-----------|-------|
| 1. A0 Initialization | ✅ COMPLETE | 2025-12-31 | Shared-files + empty WP files created |
| 2. Agent Execution | ⏳ IN PROGRESS | - | Agents filling task-packets |
| 3. Link-Hygiene Sweep | 🔜 PENDING | - | After agent completion |
| 4. Integration Notes | 🔜 PENDING | - | After link-hygiene |
| 5. Gate Report Pre-Fill | 🔜 PENDING | - | After integration notes |
| 6. PR Finalization | 🔜 PENDING | - | After gate report |

---

**Integration Day Plan Status:** INITIALIZED (A0)  
**Next:** Await agent task-packet completion, then proceed with link-hygiene sweep.
