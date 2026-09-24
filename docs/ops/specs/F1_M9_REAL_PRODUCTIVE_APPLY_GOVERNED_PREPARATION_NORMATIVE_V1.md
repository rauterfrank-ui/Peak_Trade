---
docs_token: DOCS_TOKEN_F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_NORMATIVE_V1
status: active
scope: F1/M9 real productive apply governed preparation (no apply in this slice)
workpackage_id: F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_V1
last_updated: 2026-09-24
---

# F1/M9 Real Productive Apply Governed Preparation V1

```text
WORKPACKAGE_ID=F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_V1
PREDECESSOR=F1_M9_PRODUCTIVE_APPLY_EXECUTION_MAX_BUILD_V1 (#6795)
REAL_PRODUCTIVE_APPLY_AUTHORIZED=false
PRODUCTIVE_APPLY_OCCURRED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
CANONICAL_PRODUCTIVE_CANDIDATE_RESOLVED=false
NUMERIC_THRESHOLD_SEPARATE_AUTHORIZATION_REQUIRED=true
```

Decision (extends): `config/governance/f1_m9_productive_apply_execution_boundary_v1_decision_v1.json`

## Purpose

Prepare digest-bound decision semantics, durable ledger paths, canonical candidate adjudication,
and execution-boundary completion for a **later** separate Owner GO real apply.

This slice **does not** authorize or execute real productive apply.

## Decision binding (fail-closed)

Real apply requires **both**:

1. `real_productive_apply_authorized=true` in the execution-boundary decision, and
2. `authorized_owner_apply_record_digest` equal to the sealed Owner Apply record digest.

Chat Owner GO alone is never read by code paths.

Binding owner: `src/governance/f1_m9_real_productive_apply_decision_binding_v1.py`

## Canonical candidate adjudication

Owner: `src/governance/f1_m9_canonical_productive_candidate_adjudication_v1.py`

Uses tracked config/evidence only. Does not select from fixtures, research grids, or untracked
runtime artifacts. CURRENT tracked productive campaign evidence is counterfactual accumulation
(`THRESHOLD_SELECTION` forbidden in preregistration) — **no single productive candidate**.

## Owner Apply record materialization

Owner: `src/governance/f1_m9_owner_apply_record_materialization_v1.py`

Materializes a digest-sealed record **only when** canonical candidate + explicit productive
authorization are fully resolved. Record materialization ≠ apply.

## Durable ledgers (paths only)

Relative paths in decision:

- `runtime/governance/f1_m9_scoped_owner_productive_apply_v1/apply_ledger.jsonl`
- `runtime/governance/f1_m9_scoped_owner_productive_apply_v1/revocation_ledger.jsonl`

Resolver: `src/governance/f1_m9_productive_apply_durable_ledger_paths_v1.py`

Preparation merge does **not** initialize or append ledger lines.

## Execution boundary extension

`AUTHORIZED_PRODUCTIVE_APPLY` may complete in **tests** when decision binding permits;
module-level `PRODUCTIVE_APPLY_OCCURRED` remains `false` until a later governed real apply GO.

## Numeric threshold

F1/M9 apply transition sets `candidate_value_applied=false` and `threshold_value_ratified=false`.
A concrete productive numeric max-age on the hot path requires a **separate** F1/M9 threshold
Owner record (`concrete_threshold_value_authorized=false` in CURRENT decisions).

## Next blocker

```text
NEXT_TRUE_BLOCKER=F1_M9_CANONICAL_PRODUCTIVE_CANDIDATE_AND_BOUND_REAL_APPLY_OWNER_GO
```

## Verification

`tests/governance/test_f1_m9_real_productive_apply_governed_preparation_v1.py`
