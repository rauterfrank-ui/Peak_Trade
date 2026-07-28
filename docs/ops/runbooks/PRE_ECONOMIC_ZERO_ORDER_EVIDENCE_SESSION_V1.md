# PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1

```text
status: ACTIVE
capability: GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1
implementation_readiness_capability: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1
session_contract: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1
owner: ops.pre_economic_zero_order_evidence_session_contract_v1
implementation_owner: ops.pre_economic_zero_order_evidence_session_runner_v1
authority_effect: NONE
activation_effect: NONE
economic_gate_effect: NONE
```

> **Evidence-stage contract + implementation readiness — not Shadow activation, not Economic PASS, not Runtime.**
> This contract ratifies a governed, strictly bounded, fully passive Zero-Order
> *evidence* stage that may sit between Integrated Offline Replay and
> `ECONOMIC_VALIDITY_OFFLINE_GATE`. It does **not** authorize Shadow (STEP 29U),
> Zero-Order Runtime (STEP 29T), Runtime Rewire (STEP 29R), Paper, Testnet, Live,
> orders, broker writes, scheduler start, or economic-gate PASS.
>
> `PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1` proves that the
> technical runner / emitter / telemetry / abort / verifier surfaces exist and
> can complete an offline dry-run. It does **not** execute or authorize a real
> 6h session.

## Machine tokens

```text
GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1=true
PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1=true
PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1=true
AUTHORITY_EFFECT=NONE
ACTIVATION_EFFECT=NONE
ECONOMIC_GATE_EFFECT=NONE
ORDERS_ALLOWED=false
BROKER_WRITES_ALLOWED=false
MAX_DURATION_SECONDS=21600
EXPLICIT_OPERATOR_GO_REQUIRED=true
DEFAULT_STATE=BLOCKED
RUNTIME_EXECUTION=BLOCKED
RUNTIME_AUTHORITY=NONE
SESSION_EXECUTION_AUTHORIZED=false
SIX_HOUR_SESSION_EXECUTED=false
SIX_HOUR_SESSION_READY=false
SESSION_EVIDENCE=NOT_AUTHORIZED
CONSUMER_ELIGIBILITY=false
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS_UNCHANGED=true
SHADOW_ACTIVATION_AUTHORIZED=false
PAPER_ACTIVATION_AUTHORIZED=false
TESTNET_ACTIVATION_AUTHORIZED=false
LIVE_AUTHORIZED=false
```

## Owner surfaces

| Surface | Path |
|---|---|
| Contract evaluator | `src/ops/pre_economic_zero_order_evidence_session_contract_v1.py` |
| Contract CLI (evaluate only) | `scripts/ops/run_pre_economic_zero_order_evidence_session_contract_v1.py` |
| Session runner (dry-run / offline) | `src/ops/pre_economic_zero_order_evidence_session_runner_v1.py` |
| Session verifier / readiness binding | `src/ops/pre_economic_zero_order_evidence_session_verifier_v1.py` |
| Session CLI | `scripts/ops/run_pre_economic_zero_order_evidence_session_v1.py` |
| Session config | `config/ops/pre_economic_zero_order_evidence_session_v1.toml` |
| Contract tests | `tests/ops/test_pre_economic_zero_order_evidence_session_contract_v1.py` |
| Implementation readiness tests | `tests/ops/test_pre_economic_zero_order_evidence_implementation_readiness_v1.py` |
| Semantics SSOT (sequence) | `docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md` |

## Canonical policy sequence

### Before

```text
INTEGRATED_OFFLINE_REPLAY
→ ECONOMIC_VALIDITY_OFFLINE_GATE
→ PROMOTION / STEP 29R / 29T / 29U
```

### After (this capability)

```text
INTEGRATED_OFFLINE_REPLAY
→ PRE_ECONOMIC_ZERO_ORDER_EVIDENCE
→ ECONOMIC_VALIDITY_OFFLINE_GATE
→ PROMOTION / STEP 29R / 29T / 29U
```

## Stage semantics

1. Produces **evidence only** (decision/risk/safety/telemetry observation packets).
2. Holds **no** Promotion-, Shadow-, Runtime-, or Trading-authority (`authority_effect=NONE`, `activation_effect=NONE`).
3. Works **Zero-Order only** (`orders_allowed=false`).
4. Broker-/Order-endpoints remain **technically blocked** (`broker_writes_allowed=false`).
5. Maximum duration **21600 seconds (6h)**; longer requests fail closed.
6. Executable only after **explicit Operator-GO** (never inferred).
7. Fail-closed abort on:
   - Order-Intent
   - Broker-Write
   - unknown session state
   - telemetry loss
   - Kill-State error
   - Risk-Engine error
   - incomplete decision-logic binding
   - HEARTBEAT_TIMEOUT / TELEMETRY_FAILURE / EVIDENCE_WRITE_FAILURE /
     INTEGRITY_FAILURE / CONFIG_MISMATCH / UNEXPECTED_EXCEPTION /
     TIME_BUDGET_EXCEEDED / SIGNAL_ABORT / OPERATOR_ABORT
8. `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` remains a hard prerequisite for:
   - STEP 29R Runtime Rewire
   - STEP 29T Zero-Order Runtime
   - STEP 29U Shadow
   - Paper / Testnet / Live

## Required decision-logic bindings (readiness)

All must be bound before any future authorized session may claim session readiness:

- Double Play
- Co-System
- AI Layer
- Kill-State
- Risk Engine
- Parameter-Adaption
- Telemetry / Evidence

Missing any binding → fail-closed `INCOMPLETE_DECISION_LOGIC_BINDING`.

## Implementation readiness vs session authorization

```text
PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1=true
IMPLEMENTATION_READINESS_MAY_PASS=true
SESSION_EXECUTION_AUTHORIZED=false
SIX_HOUR_SESSION_EXECUTED=false
SESSION_EVIDENCE=NOT_AUTHORIZED
RUNTIME_EXECUTION=BLOCKED
RUNTIME_AUTHORITY=NONE
CONSUMER_ELIGIBILITY=false
```

Implementation Readiness proves the technical surfaces (runner, emitter,
telemetry/heartbeat contract, abort hooks, verifier, config, offline dry-run).
It is **not** Session Completion and **not** Operator-GO.

A real 6h evidence session requires a **separate** explicit step:

```text
PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION
```

No automatic transition is implied by this capability or by merge of its PR.

## Evidence schema (dry-run / future authorized session)

Artifacts under the session evidence root:

- `session_manifest.json`
- `lifecycle_events.json`
- `heartbeat_summary.json`
- `abort_summary.json`
- `terminal_result.json`
- `integrity_manifest.json`
- `effective_config_snapshot.json`
- `evidence_manifest.sha256`
- `run_result.json` (runner summary)

Required semantic fields include at least:

`contract_version`, `session_id`, `mode`, `zero_order_enforced`,
`orders_attempted`, `orders_submitted`, `runtime_authority`,
`operator_go_present`, `start_timestamp`, `end_timestamp`, `elapsed_seconds`,
`heartbeat_count`, `expected_heartbeat_count`, `abort_reason`, `terminal_state`,
`completeness`, `integrity_status`, `config_digest`, `implementation_digest`,
`evidence_root`, `generated_files`, `consumer_eligibility`.

Binding invariants for this capability's proofs:

```text
orders_attempted=0
orders_submitted=0
zero_order_enforced=true
runtime_authority=NONE
operator_go_present=false
consumer_eligibility=false
```

Incomplete / tampered / stale / contradictory evidence → `BLOCKED` / `INVALID`.
Abort is never a successful 6h completion.

## Telemetry states

```text
INITIALIZING → READY → RUNNING → HEARTBEAT* → COMPLETED
                                 ↘ ABORTING → ABORTED
Invalid transitions / post-terminal events / non-monotone sequence or time
→ FAIL-CLOSED (INVALID / ABORTED)
```

## Immutable safety non-goals

```text
NOT_SHADOW_ACTIVATION=true
NOT_ECONOMIC_PASS=true
NOT_PAPER_AUTHORIZATION=true
NOT_TESTNET_AUTHORIZATION=true
NOT_LIVE_AUTHORIZATION=true
NOT_RUNTIME_REWIRE=true
NOT_STEP_29T_ZERO_ORDER_RUNTIME=true
NOT_STEP_29U_SHADOW=true
NOT_PROMOTION_AUTHORITY=true
NOT_ORDER_AUTHORITY=true
NOT_BROKER_WRITE_AUTHORITY=true
NOT_IMPLICIT_OPERATOR_GO=true
NOT_SIX_HOUR_SESSION_BY_THIS_CAPABILITY=true
```

## Operator commands

```bash
# Contract evaluate only (never starts a session)
python scripts/ops/run_pre_economic_zero_order_evidence_session_contract_v1.py
python scripts/ops/run_pre_economic_zero_order_evidence_session_contract_v1.py --json

# Offline dry-run for implementation readiness proof only
python scripts/ops/run_pre_economic_zero_order_evidence_session_v1.py dry-run \
  --allow-implementation-dry-run --session-id pez_dry --max-cycles 3 --json

# Verify evidence root (read-only)
python scripts/ops/run_pre_economic_zero_order_evidence_session_v1.py verify \
  --evidence-root out/ops/pre_economic_zero_order_evidence_session_v1/pez_dry --json

# Demonstrate 21600s rejection without authorization
python scripts/ops/run_pre_economic_zero_order_evidence_session_v1.py \
  reject-production-duration --json
```

Dry-run never starts a real 6h session and never submits orders.

## Explicit non-claims

```text
NOT_ACTIVATION=true
NOT_ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=true
DOES_NOT_WEAKEN_SHADOW_GATE=true
DOES_NOT_WEAKEN_ECONOMIC_GATE_FOR_29R_29T_29U=true
NO_NETWORK=true
NO_ORDERS=true
NO_BROKER_WRITES=true
NO_RUNTIME_STARTED=true
SIX_HOUR_SESSION_EXECUTED=false
SESSION_EXECUTION_AUTHORIZED=false
ORDERS_ALLOWED=false
ECONOMIC_GATE_WEAKENED=false
SHADOW_GATE_WEAKENED=false
```
