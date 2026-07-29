# PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1

```text
status: ACTIVE
capability: PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1
owner: ops.paper_shadow_observation_operator_go_session_preregistration_v1
authority_effect: NONE
activation_effect: NONE
runtime_effect: NONE
order_effect: NONE
```

> **Capability implementation — not wallclock session execution.**
> Provides versioned Session-Preregistration, scoped Operator-GO, Confirm-Token
> verification, two-stage enabled/armed state machine, Authorization-Readiness
> producer, Authorization artifact, and offline verifier.
> Binds to `INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1`.

## Hard invariants

```text
PAPER_SHADOW_OBSERVATION_AUTHORIZED=false   # repository default; only a verified GO artifact may set true
ORDERS_AUTHORIZED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
AUTO_PROMOTION_AUTHORIZED=false
ECONOMIC_VALIDITY_PASS=false
SESSION_EXECUTED=false
NETWORK_USED=false
CREDENTIALS_USED=false
WALLCLOCK_SESSION_EXECUTION_ALLOWED=false
```

## Epistemology

| Claim | Meaning |
|---|---|
| Readiness | Technical + governance preconditions for observation readiness |
| Authorization readiness | A concrete prereg + GO + token + scope assessment may pass |
| Authorization | Only from a verified, unexpired, unconsumed, scoped GO artifact |
| Execution | **Out of scope.** Authorization is not Execution |

`PAPER_SHADOW_OBSERVATION_READINESS_PASS` does **not** imply authorization.  
`PAPER_SHADOW_OBSERVATION_AUTHORIZED` does **not** start a session.  
Wallclock market-data binding remains outside this capability.

## Owners

| Surface | Path |
|---|---|
| Package | `src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/` |
| Config | `config/ops/paper_shadow_observation_operator_go_session_preregistration_v1.toml` |
| CLI | `scripts/ops/assess_paper_shadow_observation_operator_go_session_preregistration_v1.py` |
| Observation binding | `src/ops/integrated_paper_shadow_observation_session_v1/` |
| Gate-split owner | `ops.integrated_paper_shadow_economic_validity_pipeline_v1` |

## Pipeline position

```text
… → PAPER_SHADOW_OBSERVATION_READINESS_PASS
  → OPERATOR_PAPER_SHADOW_OBSERVATION_GO   # this capability (contract/verify only)
  → INTEGRATED_PAPER_SHADOW_OBSERVATION    # later execution capability; not here
  → …
```

## Explicit non-goals

- Wallclock observation session start
- OKX/network connection
- Credentials
- Orders / Testnet / Live
- Scheduler / daemon start
- Runtime-Bridge activation
- ECONOMIC_VALIDITY_PASS / Promotion
- Automatic authorization from docs or config existence
- Synthetic Force-PASS

## Offline operator command

```bash
python scripts/ops/assess_paper_shadow_observation_operator_go_session_preregistration_v1.py --mode discover --json
```

CLI refuses `start` / `run` / `execute` arguments.

## Next step

A later capability (session execution) may be selected only after a fresh
read-only post-merge system review. This capability does not authorize that step.


## Scoped wallclock MD-observe (successor)

`network_authorized=true` is legitimate only with
`network_scope=okx_eea_futures_public_md_observe_v1`.
`session_execution_authorized=true` is legitimate only with
`session_execution_scope=paper_shadow_observation_wallclock_v1`.
GO alone still does not start a session. Execution is owned by
`INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1`.
Defaults remain false / empty.
