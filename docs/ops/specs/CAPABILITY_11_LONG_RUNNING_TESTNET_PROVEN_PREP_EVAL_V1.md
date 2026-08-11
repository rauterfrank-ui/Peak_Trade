---
docs_token: DOCS_TOKEN_CAPABILITY_11_LONG_RUNNING_TESTNET_PROVEN_PREP_EVAL_V1
status: active
scope: Phase 11 LONG_RUNNING_TESTNET_PROVEN prep/eval — pre-run readiness only; no productive campaign execute; §11.12.8 remains closed; §11.13 unstarted
capability: CAPABILITY_11_LONG_RUNNING_TESTNET_PROVEN_PREP_EVAL_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-11
---

# Capability — LONG_RUNNING_TESTNET_PROVEN Prep/Eval V1

## Goal

Bind repository-side prerequisites so that after merge a **separate** Owner-GO
`EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW` can execute the
bounded long-running productive Testnet campaign from immutable `origin/main`.

```text
LONG_RUNNING_TESTNET_PROVEN_PREP_PATH_READY=true
LONG_RUNNING_TESTNET_PROVEN=false
SECTION_11_12_8_CLOSED=true
SECTION_11_12_8_REOPENED=false
CAP_11_12_TESTNET_PROGRAM_CLOSED=true
PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED
SECTION_11_13_STARTED=false
LIVE_AUTHORIZED=false
MERGE_AUTHORIZATION_IS_NOT_EXECUTE_AUTHORIZATION=true
PRODUCTIVE_CAMPAIGN_STARTED_BY_THIS_PACKAGE=false
CORE_LOGIC_CHANGE=false
```

## Out of scope

- Productive campaign execution
- Network/order side effects during validation
- Claiming `LONG_RUNNING_TESTNET_PROVEN=true`
- Reopening §11.12.8
- Starting §11.13 / Live
- Trading-core mutation
- Historical sealed-evidence mutation

## Owners

| Surface | Owner |
| --- | --- |
| Prep/eval capability | `ops.capability_11_long_running_testnet_proven_prep_eval_v1` |
| Reused productive consumer/executor | `ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1` |
| Reused unlock / HTTP client | `ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1` |
| SSOT | Master Runbook §11.12.9.21 |

## Execute authorization

```text
CANONICAL_EXECUTE_OWNER_GO_SCOPE=EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
```

Legacy aliases remain accepted on the reused consumer for the same Demo XPerp
surface only and do **not** reopen §11.12.8.

## Evidence

- Package: `docs/evidence/capability_11_long_running_testnet_proven_prep_eval_v1/`
- Generator: `scripts/ops/generate_capability_11_long_running_testnet_proven_prep_eval_v1.py`
- Verifier: `scripts/ops/verify_capability_11_long_running_testnet_proven_prep_eval_v1.py`
- Tests: `tests/ops/test_capability_11_long_running_testnet_proven_prep_eval_v1.py`
