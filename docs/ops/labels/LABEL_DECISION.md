# LABEL_DECISION — GitHub Labels (Peak_Trade)

Status: ACTIVE  
Scope: repo-wide labels (issues + pull requests)  
Policy: Decision is docs-only. GitHub label changes require explicit Operator approval.

---

## Snapshot Inputs (Deterministic)

Local artifacts (authoritative):
- tmp labels json
- tmp labels refs txt
- tmp labels audit tsv
- tmp labels operational refs tsv
- tmp labels decision tsv
- tmp labels decision candidates deprecate txt

Interpretation:
- Operational Hard-Refs = references in .github or scripts (automation dependencies).
- Docs References = references in docs (policy text/examples). Not automation dependencies, but must remain consistent.

Decision rules:
- KEEP: used greater than 0 OR operational hard-refs present
- DEPRECATE: used equals 0, but legacy/compatibility may be required
- MIGRATE: semantically needed, but taxonomy change planned (Operator-only)
- DELETE: only after migration, operational hard-refs equals 0, Operator approval, rollback plan

---

## Decision List (Current Snapshot)

### KEEP (operational hard-refs in .github/scripts)

These labels are referenced programmatically and must not be renamed or deleted without a dedicated migration and verification plan.

| Label | used_count | op_ref_count | Rationale |
|---|---:|---:|---|
| DX | 0 | 4 | operational hard-refs in .github/scripts |
| backtest | 0 | 392 | operational hard-refs in .github/scripts |
| bug | 0 | 211 | operational hard-refs in .github/scripts |
| cache | 0 | 106 | operational hard-refs in .github/scripts |
| chore | 0 | 241 | operational hard-refs in .github/scripts |
| ci | 0 | 730 | operational hard-refs in .github/scripts |
| config | 0 | 1770 | operational hard-refs in .github/scripts |
| documentation | 0 | 83 | operational hard-refs in .github/scripts |
| duplicate | 0 | 13 | operational hard-refs in .github/scripts |
| invalid | 0 | 40 | operational hard-refs in .github/scripts |
| observability | 0 | 26 | operational hard-refs in .github/scripts |
| ops/execution-reviewed | 0 | 9 | operational hard-refs in .github/scripts |
| ops/format-only | 0 | 16 | operational hard-refs in .github/scripts |
| ops/merge-log | 0 | 2 | operational hard-refs in .github/scripts |
| question | 0 | 14 | operational hard-refs in .github/scripts |
| reproducibility | 0 | 2 | operational hard-refs in .github/scripts |
| resilience | 0 | 3 | operational hard-refs in .github/scripts |
| stability | 0 | 51 | operational hard-refs in .github/scripts |

### KEEP (canonical taxonomy labels; unused OK)

| Label | used_count | op_ref_count | Rationale |
|---|---:|---:|---|
| prio:GREY | 0 | 0 | canonical taxonomy label (unused OK) |
| prio:P0 | 0 | 0 | canonical taxonomy label (unused OK) |
| prio:P1 | 0 | 0 | canonical taxonomy label (unused OK) |
| prio:P2 | 0 | 0 | canonical taxonomy label (unused OK) |
| prio:P3 | 0 | 0 | canonical taxonomy label (unused OK) |
| status:blocked | 0 | 0 | canonical taxonomy label (unused OK) |
| status:done | 0 | 0 | canonical taxonomy label (unused OK) |
| status:in_progress | 0 | 0 | canonical taxonomy label (unused OK) |
| status:next | 0 | 0 | canonical taxonomy label (unused OK) |
| stream:A | 0 | 0 | canonical taxonomy label (unused OK) |
| stream:B | 0 | 0 | canonical taxonomy label (unused OK) |
| stream:C | 0 | 0 | canonical taxonomy label (unused OK) |
| stream:D | 0 | 0 | canonical taxonomy label (unused OK) |
| stream:E | 0 | 0 | canonical taxonomy label (unused OK) |
| stream:F | 0 | 0 | canonical taxonomy label (unused OK) |
| stream:G | 0 | 0 | canonical taxonomy label (unused OK) |
| type:bug | 0 | 0 | canonical taxonomy label (unused OK) |

### DEPRECATE (KEEP) — legacy/default compatibility labels

| Label | used_count | op_ref_count | Rationale |
|---|---:|---:|---|
| enhancement | 0 | 0 | legacy/default label; keep for compatibility; avoid using |
| good first issue | 0 | 0 | legacy/default label; keep for compatibility; avoid using |
| help wanted | 0 | 0 | legacy/default label; keep for compatibility; avoid using |
| wontfix | 0 | 0 | legacy/default label; keep for compatibility; avoid using |

### DEPRECATE — unused, no operational hard-refs

| Label | used_count | op_ref_count | Rationale |
|---|---:|---:|---|
| data-layer | 0 | 0 | unused; no operational hard-refs; candidate for later migrate or delete with approval |
| epic | 0 | 0 | unused; no operational hard-refs; candidate for later migrate or delete with approval |
| priority:high | 0 | 0 | unused; no operational hard-refs; candidate for later migrate or delete with approval |
| priority:low | 0 | 0 | unused; no operational hard-refs; candidate for later migrate or delete with approval |
| priority:medium | 0 | 0 | unused; no operational hard-refs; candidate for later migrate or delete with approval |

---

## Notes

- bug is currently unused but has operational hard-refs; therefore KEEP until a dedicated migration plan exists.
- This document performs no label edits, renames, or deletes.
