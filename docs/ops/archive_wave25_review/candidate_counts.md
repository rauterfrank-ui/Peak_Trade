# Wave 25 Candidate Counts

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave25-archive-historical-consolidation-review  
**Mode:** Review-only

---

## Initial Bucket Counts (from candidate_inventory.tsv)

| Bucket | Count | Description |
|--------|-------|-------------|
| KEEP_ACTIVE_UNTIL_PROVEN_SAFE | 14 | Indexes, runbooks, evidence chain, untracked local docs, archives |
| HISTORICAL_REFERENCE_CANDIDATE | 9 | docs/_worklogs/2025-12-23_untracked_salvage/* |
| ARCHIVE_CANDIDATE | 52 | out/ops/branch_archive_phase2–12 artifacts |
| DISCARD_CANDIDATE_NEEDS_PROOF | 0 | None in this wave |

---

## Area Breakdown

| Area | Count | Notes |
|------|-------|------|
| docs/_worklogs | 9 | Strategy layer vnext, PR reports, completion summary |
| out/ops (branch_archive_phase*) | 52 | Phase 2–12 review artifacts, salvage assessments |
| docs/audit | 2 | GOVERNANCE_DATAFLOW_REPORT, REPO_AUDIT_REPORT (indexed) |
| docs (untracked) | 2 | docs/GOVERNANCE_DATAFLOW_REPORT.md, docs/REPO_AUDIT_REPORT.md |
| docs/ops | 4 | Merge logs, _archive, archives (patterns) |
| docs | 2 | INDEX.md, canonical |
| root | 2 | Pre-flight runbook, workflow overview |

---

## Excluded from Candidate Universe

- **out/ops/** evidence packs (p135_*, pilot_ready_snapshot_*, etc.): Operational evidence chain, NOT archive candidates
- **docs/ops/runbooks/**: Operational runbooks, CRITICAL
- **docs/analysis/**: Analysis READMEs, mixed usage
- **Root PHASE* files**: Not fully inventoried; require separate triage (see TRIAGE_2026-01-13)

---

## Validation

- Total candidates in inventory: **75** (14 keep + 9 historical + 52 archive)
- No deletions, moves, or renames performed
- docs/GOVERNANCE_DATAFLOW_REPORT.md, docs/REPO_AUDIT_REPORT.md: untracked, untouched
