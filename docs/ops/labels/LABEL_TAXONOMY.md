# LABEL_TAXONOMY — GitHub Labels (Peak_Trade)

Status: ACTIVE  
Scope: repo-wide labels (issues + pull requests)

---

## Canonical Prefixes

Canonical label families (preferred):
- type:
- area:
- risk:
- status:
- prio:
- stream:
- ops:

Canonical taxonomy labels may be unused without requiring changes.

---

## Canonical Examples

- type:bug — canonical label for bug classification
- status:next — next work item
- prio:P1 — priority
- stream:A — workstream assignment

---

## Legacy / Compatibility Labels

GitHub defaults and older labels may exist for compatibility.
Decision status and migration plans are tracked in LABEL_DECISION.

Examples:
- bug (legacy/default) — may remain in repo; do not use unless explicitly decided
- enhancement, wontfix, question

---

## Migration Notes (Optional, Operator-only)

Example migration (only if explicitly decided and approved):
- MIGRATE bug to type:bug

Important:
- bug currently has operational hard-refs in .github or scripts and is therefore KEEP until those refs are migrated.
- See LABEL_DECISION for current state and constraints.
