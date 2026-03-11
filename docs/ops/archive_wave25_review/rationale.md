# Wave 25 — Classification Rationale

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave25-archive-historical-consolidation-review

---

## Bucket Definitions

| Bucket | Meaning |
|--------|---------|
| KEEP_ACTIVE_UNTIL_PROVEN_SAFE | Do not archive; operational or evidence-critical |
| HISTORICAL_REFERENCE_CANDIDATE | Historical value; no operational refs; could move to archive later |
| ARCHIVE_CANDIDATE | Review artifact; low risk; could consolidate to archive |
| DISCARD_CANDIDATE_NEEDS_PROOF | Would need proof before discard; none in this wave |

---

## KEEP_ACTIVE_UNTIL_PROVEN_SAFE — Rationale

- **Indexes (docs/INDEX.md, RUNBOOK_INDEX, audit/README):** Canonical navigation; any change breaks operator workflows.
- **Runbooks (AUDIT_RUNBOOK_COMPLETE, runbooks/, PRE_FLIGHT, WORKFLOW_RUNBOOK_OVERVIEW):** Operational procedures; referenced by CI, drills, handover.
- **Merge logs (PR_*_MERGE_LOG, merge_logs/):** Evidence chain; EVIDENCE_INDEX, runbooks reference; INDEX lists as Historical but still in active use.
- **Archives (docs/ops/_archive, docs/ops/archives/):** Already archived; runbooks reference paths (workflow_docs_integration, KILL_SWITCH_SUMMARY, etc.).
- **Audit reports (docs/audit/GOVERNANCE_DATAFLOW_REPORT, REPO_AUDIT_REPORT):** INDEX and audit/README link; evidence chain.
- **Untracked local docs (docs/GOVERNANCE_DATAFLOW_REPORT.md, docs/REPO_AUDIT_REPORT.md):** Explicit Wave 25 preservation; do not add, modify, delete, or stage.

---

## HISTORICAL_REFERENCE_CANDIDATE — Rationale

- **docs/_worklogs/2025-12-23_untracked_salvage/*** (9 files): Strategy layer vnext, PR reports, completion summary. No index or runbook references. Historical context only. Safe to move to archive in a future wave after index update.

---

## ARCHIVE_CANDIDATE — Rationale

- **out/ops/branch_archive_phase2_review/** through **phase12_salvage_now_batch/**: Review artifacts from branch-archive waves. No operational references. cursor_ma_ops_cli mentions `out/ops/` as helper path but does not depend on branch_archive_phase* specifically. Lowest risk for future consolidation (e.g., move to docs/ops/_archive/branch_archive_waves/ or similar).

---

## DISCARD_CANDIDATE_NEEDS_PROOF

- **None** in this wave. No items recommended for discard without additional proof of redundancy or obsolescence.

---

## Conservative Principle

Where provenance or usage was ambiguous, classification defaulted to **KEEP_ACTIVE_UNTIL_PROVEN_SAFE**.
