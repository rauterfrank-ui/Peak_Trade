# LABEL_AUDIT_REPORT — GitHub Labels (Peak_Trade)

Status: ACTIVE  
Scope: repo-wide labels (issues + pull requests)

---

## Purpose

Deterministic audit report for:
- current label inventory
- usage counts per label
- candidates with used_count equals 0
- operational hard-refs per label (automation dependencies)

This report is generated from local snapshot artifacts under tmp.

---

## Snapshot Artifacts

- tmp labels json
- tmp labels audit tsv
- tmp labels candidates used0 txt
- tmp labels operational refs tsv
- tmp labels decision tsv

---

## Notes

- used_count equals 0 does not imply deletable; operational hard-refs can still exist.
- bug is currently unused but has operational hard-refs; therefore KEEP until migration plan exists.
- For authoritative decisions, see LABEL_DECISION.

---

## How to Regenerate

Run Phase 1 (Audit) from RUNBOOK_LABEL_GOVERNANCE.
Then review / convert tmp artifacts into docs:
- LABEL_DECISION contains the authoritative decision list.
