---
docs_token: DOCS_TOKEN_V32_D29_F1_M9_PER_INGRESS_PRODUCTIVE_AUTHORIZATION_APPLY_ADJUDICATION_AND_MAX_BUILD_V1
status: active
scope: D29 F1/M9 per-ingress explicit authorization and apply boundary adjudication (fail-closed)
capability: V32_D29_F1_M9_PER_INGRESS_PRODUCTIVE_AUTHORIZATION_APPLY_ADJUDICATION_AND_MAX_BUILD_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# V32 D29 — F1/M9 Per-Ingress Productive Authorization / Apply Adjudication and Max Build V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_D29_F1_M9_PER_INGRESS_PRODUCTIVE_AUTHORIZATION_APPLY_ADJUDICATION_AND_MAX_BUILD_V1
BOUND_ORIGIN_MAIN_SHA=df116eb6eff8f43aabf865d0a003c9a85e949d66
PREDECESSOR=V32_D28_D29_SCOPED_OPTIMIZATION_PRODUCTIVE_JOIN_F1_M9_MAX_BUILD_V1
AUTHORITY_EFFECT=PER_INGRESS_ADJUDICATION_AND_BINDING_ONLY
EXTERNAL_EFFECT_AUTHORIZED=false
TRADING_DECISION_AUTHORITY_CHANGED=false
PRODUCTIVE_APPLY_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
```

Decision:
`config/governance/v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1_decision_v1.json`

Edge registry:
`config/governance/v32_d29_f1_m9_per_ingress_authority_edge_registry_v1.json`

Owners:

- `src/governance/v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1.py`
- `src/governance/v32_d29_f1_m9_per_ingress_productive_authorization_apply_closure_v1.py`
- `src/governance/f1_m9_per_ingress_productive_authorization_binding_v1.py`
- `src/governance/f1_m9_per_ingress_authorization_chain_resolver_v1.py`

## 1. Scope

Forensic authority census and typed per-ingress binding for the **already scoped** F1/M9 pair
(`F1-M9-VOLATILITY-MAX-AGE-SECONDS`). Composes the existing M10 chain through runtime transport
to the Double Play presence gate consumer. Stops before productive apply.

Invariants preserved:

- scoped join ≠ explicit authorization ≠ materialization ≠ apply ≠ external effect
- `GLOBAL_OPTIMIZATION_JOIN_AUTHORIZED=false`
- `PROMOTION_AUTHORIZED=false`
- MV2 + Double Play remain sole trading-decision authority per slot

## 2. Stage decomposition (no implicit promotion between stages)

| Stage | CURRENT status |
| --- | --- |
| PROPOSAL_REVIEW_ADMISSION | PROVEN_CURRENT |
| EXPLICIT_PRODUCTIVE_AUTHORIZATION | PROVEN_CURRENT (Owner input required per ingress) |
| PRODUCTIVE_CONFIGURATION_MATERIALIZATION | PROVEN_CURRENT (does not imply apply) |
| PRODUCTIVE_APPLY | POLICY_EDGE_PROVEN (execution: OWNER_MERGE_GO_REQUIRED) |
| RUNTIME_CONSUMPTION | PROVEN_CURRENT (transport + non-enforcing consumer) |
| EXTERNAL_EFFECT | FORBIDDEN |

## 3. Per-ingress Owner inputs (explicit authorization)

Owner record schema: `explicit_productive_authorization_owner_input&#47;v1` — fields enumerated in
`OWNER_AUTHORIZATION_RECORD_FIELD_KEYS` on `explicit_productive_authorization_v1`.

Admission alone never authorizes. Authorization identity is deterministic per ingress:
`authorization_id = uuid5(NAMESPACE_URL, ingress_digest)`.

Expiry/revocation semantics: **OPEN** (not defined on CURRENT main).

## 4. Per-ingress binding dimensions

Typed binding (`f1_m9_per_ingress_productive_authorization_binding&#47;v1`) seals:

`scoped_join_pair_id`, `surface_id`, `productive_target_id`, `ingress_digest`, candidate/evidence
digests, owner authorization digests, risk refs, `registry_digest`, `binding_digest`.

Missing/mismatch/stale registry digest ⇒ `DENIED_FAIL_CLOSED`.

## 5. Apply boundary

`governed_productive_configuration_v1.runtime_apply_authority=NONE` and
`runtime_apply_possible_v1()=false`. No dedicated productive-apply owner module on CURRENT main.

## 6. Blocker succession

Closed (successor WP):
`V32_D29_F1_M9_EXPLICIT_OWNER_PRODUCTIVE_APPLY_POLICY_AND_AUTHORITY_EDGE_V1`

Next true blocker after policy edge:
`F1_M9_PRODUCTIVE_APPLY_EXECUTION_REQUIRES_OWNER_MERGE_GO`

## 7. Non-goals

- Productive apply activation
- Numeric value selection or `PRODUCTIVE_NUMERIC_VALUES_SET>0`
- Global join boolean flip
- F2/F5 join
- Optimization direct runtime write
- External effect

## 8. Verification

`tests/governance/test_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1.py`
