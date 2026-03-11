# Wave 25 — Safe Future Archive Plan

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave25-archive-historical-consolidation-review

---

## Scope

This plan defines a **future** archive wave. **No actions are taken in Wave 25.** No feature, dataflow, service, or runtime changes are allowed.

---

## First Safe Archive Wave (Future)

### Tier 1: Lowest Risk — out/ops/branch_archive_phase*

**What:** Consolidate `out/ops/branch_archive_phase2_review/` through `out/ops/branch_archive_phase12_salvage_now_batch/` into a single archive location.

**Proposed target:** `docs&#47;ops&#47;_archive&#47;branch_archive_waves&#47;` or `out&#47;ops&#47;_archive&#47;branch_archive_phases_2_12&#47;`

**Conditions:**
- Verify `cursor_ma_ops_cli` and any scripts do not hardcode paths to these phase dirs
- Add README in archive explaining provenance
- No index updates required (these are not linked from INDEX or runbooks)

**Risk:** LOW

---

### Tier 2: Historical Reference — docs/_worklogs

**What:** Move `docs/_worklogs/2025-12-23_untracked_salvage/` to archive.

**Proposed target:** `docs&#47;ops&#47;_archive&#47;worklogs&#47;2025-12-23_untracked_salvage&#47;` or `docs&#47;_worklogs&#47;_archive&#47;`

**Conditions:**
- Confirm no late-added references to these files
- If docs/INDEX or KNOWLEDGE_BASE_INDEX ever linked _worklogs, update those links
- Add redirect or README if discoverability matters

**Risk:** LOW (no current refs found)

---

## What Must Stay Active

- All items in `must_keep_active.md`
- docs/GOVERNANCE_DATAFLOW_REPORT.md, docs/REPO_AUDIT_REPORT.md (untracked) <!-- pt:ref-target-ignore -->
- docs/ops/merge_logs/, docs/ops/PR_*_MERGE_LOG.md
- docs/ops/_archive/, docs/ops/archives/ (already archived; do not move again)
- All runbooks, indexes, evidence chain artifacts

---

## Index Updates Required (Future Wave Only)

If Tier 1 or Tier 2 is executed:
- **Tier 1:** None (out/ops not in docs index)
- **Tier 2:** Check docs/INDEX, KNOWLEDGE_BASE_INDEX for _worklogs links; update if present

---

## Execution Order (Future)

1. **Wave 26 (or later):** Execute Tier 1 (branch_archive_phase* consolidation)
2. **Wave 27 (or later):** Execute Tier 2 (docs/_worklogs archive) after Tier 1 verification
3. **No discard** without explicit proof of redundancy

---

## Guardrails (Non-Negotiable)

- No deletions
- No renames without index update
- No moves of evidence chain, runbooks, or indexes
- No feature/runtime/dataflow mutation
