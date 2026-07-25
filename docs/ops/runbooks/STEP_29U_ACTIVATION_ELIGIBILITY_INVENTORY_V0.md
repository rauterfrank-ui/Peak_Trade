# STEP 29U Activation Eligibility Inventory v0

```text
status: DRAFT
capability: STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0
owner: ops.step_29u_activation_eligibility_inventory_v0
authority_effect: NONE
```

> **Inventory only — not Activation.**  
> This contract inventories fail-closed prerequisites for any *future*,
> separately authorized Step-29U activation consideration. It does **not**
> activate, arm, schedule, connect, submit, promote, or mutate runtime state.
> It is **not** Activation Binding and **not** Activation Readiness approval.

## Machine tokens

```text
STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0=true
CAPABILITY_TYPE=OFFLINE_NON_ACTIVATING_FAIL_CLOSED_INVENTORY
ACTIVATION_ELIGIBLE=false
STEP_29U_ACTIVATED=false
RUNTIME_ACTIVATED=false
SCHEDULER_ACTIVATED=false
NETWORK_USED=false
ORDERS_CREATED=false
ORDERS_SUBMITTED=false
OPERATOR_GO_PRESENT=false
IMPLEMENTATION_AUTHORIZATION_IS_NOT_ACTIVATION_GO=true
```

## Owner surfaces

| Surface | Path |
|---|---|
| Evaluator | `src/ops/step_29u_activation_eligibility_inventory_v0.py` |
| CLI | `scripts/ops/run_step_29u_activation_eligibility_inventory_v0.py` |
| Tests | `tests/ops/test_step_29u_activation_eligibility_inventory_v0.py` |
| Binding inventory SSOT | `docs/ops/runbooks/STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md` |

## Operator command

```bash
python scripts/ops/run_step_29u_activation_eligibility_inventory_v0.py
python scripts/ops/run_step_29u_activation_eligibility_inventory_v0.py --json --output-path PATH
```

Expected current canonical result:

```text
STATUS=PASS
EVALUATOR_VALID=true
ACTIVATION_ELIGIBLE=false
STEP_29U_ACTIVATED=false
```

Exit code `0` means evaluator health PASS. It does **not** mean activation
eligible.

## Semantic boundary

May answer only:

- which formal prerequisite IDs exist;
- which canonical source owns each;
- SATISFIED / UNSATISFIED / ABSENT / INVALID;
- evidence/provenance and blockers;
- whether activation eligibility is established (currently always false while
  mandatory blockers remain, including absent future Operator-GO).

Must not answer whether/when activation should occur, capital allocation,
Runtime/Scheduler/Network/Orders enablement, or whether an operator should
grant later authorization.

## Prerequisite IDs

1. `STEP_29U_BINDING_PROVEN`
2. `STEP_29U_POST_MERGE_SOAK_PROVEN`
3. `STEP_29U_AUDIT_PROVENANCE_COMPLETE`
4. `RUNTIME_BRIDGE_BOUND`
5. `RUNTIME_REMAINS_NOT_ACTIVATED`
6. `SCHEDULER_REMAINS_LOCKED`
7. `NETWORK_REMAINS_PROHIBITED`
8. `ORDERS_REMAIN_PROHIBITED`
9. `ECONOMIC_VALIDITY_PROVEN`
10. `SAFETY_AUTHORITY_VALID`
11. `RECONCILIATION_PRECONDITIONS_PROVEN`
12. `ACTIVATION_AUTHORITY_CONTRACT_PRESENT`
13. `EXPLICIT_FUTURE_OPERATOR_GO_PRESENT`
14. `BTC_EXCLUDED`
15. `SPOT_EXCLUDED`
16. `KRAKEN_LEGACY_EXCLUDED`

## Fail-closed rules

- Unknown / missing / malformed sources → ABSENT or INVALID, never satisfied.
- Digest mismatch / wrong soak head → INVALID.
- Runtime/Scheduler/Network/Orders true in soak input → INVALID.
- BTC/Spot/Kraken-legacy observed → INVALID for exclusion prerequisites.
- This implementation GO must not be inferred as future activation GO.
- `activation_eligible` cannot be true while blockers exist.
- `step_29u_activated` always remains false in this capability.

## Explicit non-claims

```text
NOT_ACTIVATION=true
NOT_ACTIVATION_BINDING=true
NOT_ACTIVATION_READINESS_APPROVAL=true
DOES_NOT_AUTHORIZE_LATER_ACTION=true
NEXT_ACTION=SEPARATE_OPERATOR_REVIEW_AND_MERGE_ONLY
ACTIVATION_REMAINS_FORBIDDEN_WITHOUT_NEW_EXPLICIT_OPERATOR_GO=true
```
