# INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1

```text
status: ACTIVE
capability: INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1
owner: ops.integrated_paper_shadow_observation_wallclock_session_execution_v1
authority_effect: NONE
activation_effect: NONE
runtime_effect: NONE
order_effect: NONE
economic_gate_effect: NONE
```

> **Technical wallclock capability — not productive authorization.**
> Implements fail-closed OKX-EEA public REST market-data observation with
> atomic authorization consumption, evidence, and PASS/FAIL/ABORT semantics.
> Repository defaults do **not** authorize a productive session.
> No real network was used to land this capability.
> No productive preregistration, Operator-GO, confirm token, or authorization
> artifact is created by this capability PR.

## Pipeline position

```text
… → PAPER_SHADOW_OBSERVATION_READINESS_PASS
  → OPERATOR_PAPER_SHADOW_OBSERVATION_GO
  → INTEGRATED_PAPER_SHADOW_OBSERVATION   # this capability (wallclock MD-observe)
  → INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE
  → …
```

IPSO (`INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1`) remains the
offline observation contract owner and stays non-executing by default.
This capability is the sole wallclock execution successor.

## Hard invariants

```text
orders_authorized=false
testnet_authorized=false
live_authorized=false
auto_promotion_authorized=false
credentials_authorized=false
paper_execution_authorized=false
ECONOMIC_VALIDITY_PASS=false
PROMOTION_PASS=false
network_scope=okx_eea_futures_public_md_observe_v1   # required when network_authorized
session_execution_scope=paper_shadow_observation_wallclock_v1
transport=rest_poll_v1
host=eea.okx.com
instrument=ETH-USD_UM_XPERP-310404
max_session_duration_seconds=21600
execution_class=ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION
```

## Authorization

Requires a verified bundle from
`PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1`
with exact network and session-execution scopes.
GO alone does not start a session.
Consumption is atomic and happens before the first network byte.
Consumed bundles are single-use; start failure after consumption is ABORT.

## Transport

- REST polling only (WebSocket out of scope)
- Host: `https://eea.okx.com`
- GET only; public paths allowlisted
- No credentials, no private endpoints, no orders

## Observation semantics

Reuses IPSO / shadow-no-order / Master-V2 decision→risk→safety composition and
analytical portfolio economics labeled
`ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION`.
This is not Paper Execution and not venue fills.

## CLI

```bash
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py preflight
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py verify-evidence --evidence-root <path>
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py run ...
```

`preflight` and `verify-evidence` are offline.
`run` via CLI refuses real network in this repository path; tests use the
library runtime with injected fake transport and fake clocks.

## Explicit non-goals

- Productive preregistration / Operator-GO / confirm token issuance
- Real 6h session execution in this PR
- Paper / Testnet / Live orders
- Economic Validity PASS
- Auto-promotion
- Dashboard authority
- Zero-Order as substitute
