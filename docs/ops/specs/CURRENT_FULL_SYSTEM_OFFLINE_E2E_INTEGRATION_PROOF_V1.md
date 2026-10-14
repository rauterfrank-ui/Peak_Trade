# CURRENT_FULL_SYSTEM_OFFLINE_E2E_INTEGRATION_PROOF_V1

Bounded offline integration proof for CURRENT Full-Core exchange boundary closure.

```text
WORK_PACKAGE_ID=CURRENT_FULL_SYSTEM_OFFLINE_E2E_INTEGRATION_PROOF_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
REAL_EXCHANGE_POST_AUTHORIZED=false
REAL_EXCHANGE_GET_AUTHORIZED=false
LIVE_READY=false
```

## Scope

- Composes existing production joins (PRE_EXTERNAL capital guard, cycle-host lifecycle
  orchestration, optional one-shot fake HTTP POST transport) under an isolated durable
  state root.
- Fake exchange transport only; `REAL_EXCHANGE_GET_COUNT=0`, `REAL_EXCHANGE_POST_COUNT=0`.
- Does not enable productive cycle-host lifecycle wiring by default (`DISABLED` preserved).

## Owner module

`src/ops/full_core_live_path_composition_root_v1/current_full_system_offline_e2e_integration_proof_v1.py`

## Evidence

Offline pytest: `tests/ops/test_current_full_system_offline_e2e_integration_proof_v1.py`

## Proof honesty (offline)

| Claim | Status |
| --- | --- |
| `NATURAL_ENTER_CURRENT_PROOF` | PASS via GAP-TRUE-01 production path (no fabricated enter) |
| `PRE_EXTERNAL_CURRENT_PROOF` | PASS via same closure envelope |
| `FULL_CHAIN_WIRED` | true (GAP-TRUE-01 → pilot bind → one-shot fake POST → OFFLINE_INJECTED recon) |
| `FULL_CHAIN_OFFLINE_PROVEN` | true (witness `FAKE_POST_COUNT=1`, standing `REAL_*=0`) |
| `CRASH_RESTART_PROOF` | PASS (subprocess worker + durable witness; exit 91/93 crash points) |
| `LIVE_K1_GET_PROVEN` / `LIVE_POST_PROVEN` | NOT_PROVEN (explicitly out of scope) |

Capital guard on the production chain reuses pilot post-bind evidence (`capital_guard_prevalidated`)
when the offline owner-authorization fixture already sealed pilot admission; full-core
`OFFLINE_STUB` join remains covered by downstream lifecycle tests.

Multiprocess entry: `scripts/ops/run_current_full_system_offline_e2e_crash_worker_v1.py`
