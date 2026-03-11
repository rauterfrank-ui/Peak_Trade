# Wave 25 — Must Keep Active

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave25-archive-historical-consolidation-review

---

## Items That Must NOT Be Archived

These items have operational evidence, index linkage, runbook references, or are canonical operator-facing docs. **Do not archive, move, or rename** until proven safe by a future, explicit review.

### Critical (Index / Runbook / Operator-Facing)

| Path | Reason |
|------|--------|
| docs/INDEX.md | Canonical documentation index; linked from README |
| docs/ops/RUNBOOK_INDEX.md | Canonical runbook navigation; linked from INDEX |
| docs/audit/README.md | Canonical audit navigation; links to audit reports |
| docs/audit/AUDIT_RUNBOOK_COMPLETE.md | Operational runbook; linked from RUNBOOK_INDEX |
| docs/ops/runbooks/ | All operational runbooks; RUNBOOK_INDEX points here |
| PRE_FLIGHT_CHECKLIST_RUNBOOK_OPS.md | Pre-flight runbook; linked from RUNBOOK_INDEX |
| WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md | Workflow overview; linked from RUNBOOK_INDEX |

### Evidence Chain / Merge Logs

| Path | Reason |
|------|--------|
| docs/ops/PR_*_MERGE_LOG.md | Evidence chain; INDEX lists as Historical but still referenced |
| docs/ops/merge_logs/*.md | Evidence chain; EVIDENCE_INDEX, runbooks reference |
| docs/ops/_archive/ | Referenced by runbooks (workflow_docs_integration, installation_roadmap, etc.) |
| docs/ops/archives/ | Referenced by runbooks (KILL_SWITCH_SUMMARY, RUNBOOK_COMMIT_SALVAGE, etc.) |

### Audit Reports (Indexed)

| Path | Reason |
|------|--------|
| docs/audit/GOVERNANCE_DATAFLOW_REPORT.md | INDEX Historical; audit/README links |
| docs/audit/REPO_AUDIT_REPORT.md | INDEX Historical; audit/README links |

### Untracked Local Docs (Explicit Preservation)

| Path | Reason |
|------|--------|
| docs/GOVERNANCE_DATAFLOW_REPORT.md | Untracked; explicit Wave 25 preservation requirement |
| docs/REPO_AUDIT_REPORT.md | Untracked; explicit Wave 25 preservation requirement |

---

## Operational Evidence (out/ops, Not in Archive Candidate Set)

- **out/ops/p135_shadow_readonly_evidence_pack_*** — Shadow execution evidence
- **out/ops/pilot_ready_snapshot_*** — Pilot readiness snapshots
- **out/ops/provider_model_binding_spec_*** — Spec verification artifacts
- **out/ops/pr_webui_ops_cockpit_*** — PR workflow artifacts

These are **operational evidence** and are **not** archive candidates. Do not move or delete.

---

## Summary

- **14** items explicitly flagged as KEEP_ACTIVE_UNTIL_PROVEN_SAFE
- **0** functional mutations in this wave
- docs/GOVERNANCE_DATAFLOW_REPORT.md, docs/REPO_AUDIT_REPORT.md: **untracked, untouched**
