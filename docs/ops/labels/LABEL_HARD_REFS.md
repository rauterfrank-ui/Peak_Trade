# LABEL_HARD_REFS — GitHub Labels (Peak_Trade)

Status: ACTIVE  
Scope: repo-wide labels (issues + pull requests)

---

## Purpose

Separate:
- **Operational Hard-Refs**: references in .github and scripts (automation dependencies)
- **Docs References**: references in docs (policy text/examples)

Only operational hard-refs block rename or delete. Docs references must stay consistent with LABEL_DECISION but are not automation dependencies.

---

## Source Artifacts

- tmp labels refs txt (broad scan output)
- tmp labels operational refs tsv (label-specific operational ref counts)

---

## Operational Hard-Refs (Authoritative)

Definition:
- references in .github or scripts that programmatically expect a label name (gh flags, queries, actions inputs, policy checks, scripts)

Authoritative metric:
- tmp labels operational refs tsv (label -> op_ref_count)

Rule:
- labels with op_ref_count greater than 0 are KEEP unless a migration plan exists.

---

## Docs References (Non-operational)

Definition:
- references under docs are expected to include examples, taxonomy, runbooks, and policy text.
- docs references must be updated when decisions change, but do not by themselves block label changes.

---

## Refresh Procedure

1) Run the broad scan (generates tmp labels refs txt)
2) Run per-label operational refs scan (generates tmp labels operational refs tsv)
3) Update LABEL_DECISION and any taxonomy/runbook docs that contain label names
