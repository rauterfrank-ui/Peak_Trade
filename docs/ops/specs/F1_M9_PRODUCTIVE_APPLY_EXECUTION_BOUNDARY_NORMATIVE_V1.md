---
docs_token: DOCS_TOKEN_F1_M9_PRODUCTIVE_APPLY_EXECUTION_BOUNDARY_NORMATIVE_V1
status: active
scope: F1/M9 productive apply execution boundary (D29 policy edge + scoped apply orchestration)
workpackage_id: F1_M9_PRODUCTIVE_APPLY_EXECUTION_MAX_BUILD_V1
last_updated: 2026-09-24
---

# F1/M9 Productive Apply Execution Boundary V1

```text
WORKPACKAGE_ID=F1_M9_PRODUCTIVE_APPLY_EXECUTION_MAX_BUILD_V1
PREDECESSOR=V32_D29_F1_M9_EXPLICIT_OWNER_PRODUCTIVE_APPLY_POLICY_AND_AUTHORITY_EDGE_V1
AUTHORITY_EFFECT=EXECUTION_BOUNDARY_ORCHESTRATION_ONLY
REAL_PRODUCTIVE_APPLY_AUTHORIZED=false
PRODUCTIVE_APPLY_OCCURRED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
EXTERNAL_EFFECT_AUTHORIZED=false
```

Decision: `config/governance/f1_m9_productive_apply_execution_boundary_v1_decision_v1.json`

Owner: `src/governance/f1_m9_productive_apply_execution_boundary_v1.py`

## Chain (proven on CURRENT main)

```text
F1/M9 candidate + ingress
  → explicit productive authorization (A)
  → governed productive configuration materialization (B)
  → per-ingress binding + runtime transport (C)
  → D29 explicit Owner Apply policy edge (D)
  → F1/M9 productive apply execution boundary (E)
  → scoped apply adjudicator + ephemeral/durable ledger witness (E.1)
  → authorized parameter seam → presence gate consumer (F)
```

Stages A–D alone **do not** imply productive apply. Stage E in `EXECUTION_PROOF` exercises
apply adjudication on caller-provided ledger paths without `REAL_PRODUCTIVE_APPLY_AUTHORIZED`.

## Execution phases

| Phase | Real apply | Typical ledger |
| --- | --- | --- |
| `EXECUTION_PROOF` | **No** (`productive_apply_occurred=false`) | Caller ephemeral (tests) |
| `AUTHORIZED_PRODUCTIVE_APPLY` | Blocked until Owner sets `real_productive_apply_authorized=true` in decision | Governed durable paths (future GO) |

## Closed / next blocker

```text
CLOSED_EXECUTION_BLOCKER=F1_M9_PRODUCTIVE_APPLY_EXECUTION_REQUIRES_OWNER_MERGE_GO
NEXT_TRUE_BLOCKER=F1_M9_REAL_PRODUCTIVE_APPLY_REQUIRES_EXPLICIT_OWNER_GO
```

## Non-goals

- Real productive apply in this slice
- Global optimization join, promotion, self-deploy
- Threshold value hot-path authorization
- Live/Testnet/orders/credentials

## Verification

`tests/governance/test_f1_m9_productive_apply_execution_boundary_v1.py`
