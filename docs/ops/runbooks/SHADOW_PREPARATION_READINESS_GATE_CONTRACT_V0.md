# Shadow Preparation Readiness Gate Contract v0

## Status

**Preparation and classification only.**

Producer family: `ops.shadow_preparation_readiness_gate_v0`

This contract inventories and classifies existing shadow-named repository
surfaces and emits a deterministic machine-readable Shadow-preparation readiness
result. It proves that **canonical STEP 29U Shadow Mode does not currently
exist** and that activation remains unauthorized.

```text
SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0=true
PREPARATION_ONLY=true
NOT_STEP_29U_IMPLEMENTATION=true
AUTHORITY_EFFECT=NONE
NON_ACTIVATING=true
```

## Non-activation guarantees (mandatory)

This contract:

- is **preparation only**;
- is **not** STEP 29U implementation;
- does **not** authorize Shadow;
- does **not** authorize Paper, Testnet, Scheduler, Runtime, Live, or Orders;
- does **not** start, schedule, simulate, or execute any Shadow/Paper/Testnet
  session, worker, runtime bridge, or order path;
- has **no** method that enables or starts a process.

All activation flags remain **false**:

```text
SHADOW_ACTIVATION_AUTHORIZED=false
PAPER_ACTIVATION_AUTHORIZED=false
TESTNET_ACTIVATION_AUTHORIZED=false
SCHEDULER_ACTIVATION_AUTHORIZED=false
RUNTIME_ACTIVATION_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_AUTHORIZED=false
```

A **separate operator GO** is required for any activation-stage work.

## Authority boundaries (unchanged)

- **Master V2** and **Double Play** remain the sole decision/composition
  authorities.
- **Safety** remains an independent veto authority.
- **Runtime Bridge** remains `BOUND_NOT_ACTIVATED`.
- Economic sequencing remains binding:
  `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false` (FAIL/BLOCKED).
- This producer has `authority_effect=NONE` and cannot modify another owner.

## Historical surface non-equivalence

Historical shadow-named surfaces are **not** canonical by name. Existing
Phase-24 (`ShadowOrderExecutor`, `scripts/run_shadow_execution.py`), Phase-31
(`ShadowPaperSession`), Shadow-247 wrappers/preflight, `shadow_no_order_proof`,
`src/data/shadow/__init__.py`, paper/shadow WebUI readmodels, and related
surfaces are classified as non-equivalent to STEP 29U unless an existing
ratified canonical binding explicitly proves otherwise.

Classifications used by this contract include:

- `NON_CANONICAL_STEP29U`
- `HISTORICAL`
- `PREPARATION_ONLY`
- `EVIDENCE_ONLY`
- `OFFLINE_REPLAY`
- `EXECUTOR_WITHOUT_CANONICAL_BINDING`
- `UNKNOWN_FAIL_CLOSED` (fail-closed — evaluation rejects ambiguous surfaces)

## Dashboard blocker (still OPEN)

```text
DASHBOARD_BLOCKER_ID=MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY
DASHBOARD_BLOCKER_STATE=OPEN
DASHBOARD_BLOCKER_RESOLVED=false
DASHBOARD_BLOCKER_WAIVED=false
DASHBOARD_BLOCKER_ACCEPTED_AS_DONE=false
```

Closing PR #5529 did **not** resolve, waive, or accept the dashboard defect.
`MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY` remains **OPEN** in every
produced readiness result. This contract must not resolve or waive that
blocker.

## Canonical STEP 29U / 29V status

```text
CANONICAL_SHADOW_MODE_EXISTS=false
CANONICAL_STEP_29U_BOUND=false
CANONICAL_STEP_29V_PAPER_MODE_EXISTS=false
SHADOW_PREPARATION_COMPLETE=false
AUTHORITY_EFFECT=NONE
NOT_STEP_29U_IMPLEMENTATION=true
```

Canonical STEP 29U Shadow Mode and STEP 29V Paper Mode do not currently exist
in the repository as ratified **bindings**. The semantic definition of STEP 29U
is owned exclusively by the canonical runbook section
`## STEP 29U — Shadow` in
`docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`.

That runbook section may define STEP 29U as semantically ratified but
operationally unbound. This readiness contract does **not** duplicate that
normative body and does **not** become a second STEP 29U SSOT.

### Readiness producer role (narrow)

`ops.shadow_preparation_readiness_gate_v0`:

- classifies preparation truth;
- proves absence / non-readiness;
- cannot bind STEP 29U;
- cannot implement STEP 29U;
- cannot activate Shadow, Paper, Testnet, Scheduler, Runtime, Live, or Orders.

```text
READINESS_PRODUCER_CLASSIFIES_PREPARATION_TRUTH=true
READINESS_PRODUCER_PROVES_ABSENCE_OR_NON_READINESS=true
READINESS_PRODUCER_CANNOT_BIND_STEP_29U=true
READINESS_PRODUCER_CANNOT_IMPLEMENT_STEP_29U=true
READINESS_PRODUCER_CANNOT_ACTIVATE_STEP_29U=true
```

## Owners and artifacts

| Role | Path |
|------|------|
| Producer | `src/ops/shadow_preparation_readiness_gate_v0.py` |
| Config (static, non-activating) | `config/ops/shadow_preparation_readiness_gate_v0.toml` |
| Contract doc (this file) | `docs/ops/runbooks/SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md` |
| Related charter (non-activating) | `docs/ops/runbooks/SHADOW_247_GOVERNANCE_CHARTER_V0.md` |
| Focused tests | `tests/ops/test_shadow_preparation_readiness_gate_v0.py` |

## Fail-closed conditions

Evaluation fails closed when:

- config is missing or invalid;
- a required canonical reference cannot be established;
- contradictory activation state is supplied;
- any activation flag is true;
- dashboard blocker state is missing or claims resolved/waived/accepted;
- historical surfaces are ambiguously classified (`UNKNOWN_FAIL_CLOSED`);
- `authority_effect` is not `NONE`.


## STEP 29U Mindestkontrakt gap inventory (preparation only)

This producer emits a deterministic, machine-readable inventory of required
STEP 29U Mindestkontrakt components. Inventory status values are closed-enum:

- `PRESENT`
- `MISSING`
- `UNBOUND`
- `DOCS_ONLY`
- `LEGACY_NON_CANONICAL`

```text
MINDESTKONTRAKT_GAP_INVENTORY_V0=true
NOT_STEP_29U_IMPLEMENTATION=true
STEP_29U_IMPLEMENTED=false
SHADOW_ACTIVATABLE=false
SHADOW_MODE_ALLOWED=false
SEPARATE_GO_REQUIRED_FOR_IMPLEMENTATION=true
SEPARATE_GO_REQUIRED_FOR_ACTIVATION=true
CANONICAL_STEP_29V_PAPER_MODE_EXISTS=false
```

The inventory proves preparation gaps only. It does **not** implement STEP 29U,
bind Master V2 / Double Play to a Shadow session, create a lifecycle, simulate
orders/fills, or authorize activation. Historical Shadow/Paper surfaces remain
non-canonical (`LEGACY_NON_CANONICAL` / historical surface classifications).

STEP 29V Paper Mode remains canonically undefined
(`CANONICAL_STEP_29V_PAPER_MODE_EXISTS=false`). This contract does not define
STEP 29V semantics.

## Next permitted action

Continue offline Shadow-preparation classification only. No STEP 29U
implementation. No activation. Separate operator GO required for any
activation-stage work.

## Explicit exclusions

Does not modify: Master V2, Double Play, Dynamic Scope, Risk/Sizing, Safety,
Runtime Bridge implementation, scheduler runner/models/jobs, WebUI/dashboard
implementation, economic-policy thresholds, order/execution adapters, or any
PR #5529 dashboard code.
