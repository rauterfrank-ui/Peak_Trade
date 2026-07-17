# Discovery Reconciliation — DRIFT_B02

## Source
- `docs/product/evidence/global_runbook_next_workstream_discovery_v1_20260717T025036Z/selected_next_slice.json`
- `docs/governance/drift_cleanup_plan_v1.md` Section B-02 / DOC-12
- `docs/governance/authority_conflict_matrix_v1.md` AUTH-022

## Exact definition
Unify R&amp;D strategy docs status vocabulary to canonical tokens:
`stub` | `research-only` | `missing`.

## Divergent before
FEHLENDE claimed TODO/NotImplementedError for Ehlers/LdP/Bouchaud/Gatheral and Meta-Labeling null/empty placeholders while productive modules existed.

## Target grammar
- Canonical set: stub, research-only, missing
- Legacy aliases normalized only in `normalize_rd_strategy_status_v0`
- Ambiguous tokens (TODO, NotImplemented*) fail-closed

## Non-goals
No Master V2 / Double Play / Risk / Sizing / Execution / Live / Dashboard / Runtime activation changes.

## DoD applied
- FEHLENDE §5.2.1 status table
- Meta-Labeling bullets corrected
- NON-OPERATIONAL explicit
- Grammar owner + contract tests
