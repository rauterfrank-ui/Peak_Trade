---
docs_token: DOCS_TOKEN_V32_D29_F1_M9_EXPLICIT_OWNER_PRODUCTIVE_APPLY_POLICY_AND_AUTHORITY_EDGE_V1
status: active
scope: D29 F1/M9 explicit Owner productive apply policy and authority edge (fail-closed; no apply execution)
capability: V32_D29_F1_M9_EXPLICIT_OWNER_PRODUCTIVE_APPLY_POLICY_AND_AUTHORITY_EDGE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# V32 D29 — F1/M9 Explicit Owner Productive Apply Policy and Authority Edge V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_D29_F1_M9_EXPLICIT_OWNER_PRODUCTIVE_APPLY_POLICY_AND_AUTHORITY_EDGE_V1
PREDECESSOR=V32_D29_F1_M9_PER_INGRESS_PRODUCTIVE_AUTHORIZATION_APPLY_ADJUDICATION_AND_MAX_BUILD_V1
AUTHORITY_EFFECT=POLICY_EDGE_AND_BINDING_ONLY
EXTERNAL_EFFECT_AUTHORIZED=false
PRODUCTIVE_APPLY_OCCURRED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
TRADING_DECISION_AUTHORITY_CHANGED=false
```

Decision:
`config/governance/v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1_decision_v1.json`

Owner:
`src/governance/v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1.py`

## 1. Purpose (ADJUDICATED_CURRENT_FACT)

Closes D29 blocker
`F1_M9_PER_INGRESS_PRODUCTIVE_APPLY_REQUIRES_EXPLICIT_OWNER_APPLY_INPUT_AND_AUTHORITY_EDGE`
by defining a typed, provenance-bound Owner Apply **policy edge** at
`governed_productive_configuration_v1.runtime_apply_authority` for the scoped F1/M9 pair only.

This slice **does not** execute productive apply, flip global join, promote, or set numeric values.

## 2. Epistemic classes

| Item | Class |
| --- | --- |
| Master Runbook optimization boundaries | CANONICAL_AUTHORITY |
| D29 predecessor max-build + F1/M9 apply modules on main | ADJUDICATED_CURRENT_FACT |
| Concept PDF promotion wording | NAVIGATION_ONLY |
| Inferred D1–D23 DoD | UNKNOWN_OR_CONTRADICTORY (out of scope) |

## 3. Owner Apply input contract

Schema: `f1_m9_owner_apply_authorization_record/v1`  
Module: `src/governance/f1_m9_owner_apply_authorization_record_v1.py`

Bindings (fail-closed): `scoped_join_pair_id`, `registry_digest`, `ingress_digest`,
`binding_digest`, `owner_authorization_record_digest`, `authorization_id/digest`,
`configuration_id/digest`, `candidate_parameter_value_digest`, productive target contract digest,
`not_before` / `expires_at`, `authorizer_identity`.

## 4. Authority edge

| Edge | Producer | Consumer (execution adjudicator) |
| --- | --- | --- |
| `PRODUCTIVE_APPLY_BOUNDARY` | `governed_productive_configuration_v1` | `f1_m9_scoped_owner_apply_authority_v1` |

Policy evaluation owner:
`evaluate_explicit_owner_productive_apply_policy_edge_v1` (no configuration mutation).

## 5. Stage separation (negative proofs)

| Stage | Implies apply? |
| --- | --- |
| Explicit productive authorization | **No** |
| Configuration materialization | **No** |
| Runtime transport | **No** |
| Policy edge bound | **No** (binding only) |
| F1/M9 apply execution | Separate; requires `OWNER_MERGE_GO` |

## 6. Closed / next blocker

```text
CLOSED_D29_BLOCKER=F1_M9_PER_INGRESS_PRODUCTIVE_APPLY_REQUIRES_EXPLICIT_OWNER_APPLY_INPUT_AND_AUTHORITY_EDGE
NEXT_TRUE_BLOCKER=F1_M9_PRODUCTIVE_APPLY_EXECUTION_REQUIRES_OWNER_MERGE_GO
```

## 7. Non-goals

- Productive apply execution / ledger witness in this slice
- Threshold value authorization
- Global join boolean, promotion, self-deploy
- P5 cutover, F2/F5 join, M4 reexecution, M10/M11 expansion
- Live/Testnet/order/credential/external effect

## 8. Verification

`tests/governance/test_v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1.py`
