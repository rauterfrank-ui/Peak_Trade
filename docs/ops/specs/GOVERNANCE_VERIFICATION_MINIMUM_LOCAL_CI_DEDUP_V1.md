---
docs_token: DOCS_TOKEN_GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1
status: active
scope: Governance verification orchestration only; no trading&#47;activation&#47;order semantics
policy_id: GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Governance Verification — Minimum Local CI Dedup V1

## Goal

Reduce local verification to the necessary minimum and forbid redundant
re-execution of checks that GitHub Required Checks already bind as the
broad integration&#47;regression layer.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
NETWORK_SESSION_STARTED=false
CREDENTIAL_ACCESS=false
ORDER_SUBMIT_REACHABLE=false
CAPABILITY_11_13_STARTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Target architecture

```text
Capability&#47;owner test once locally
→ PASS + EXIT=0 binds local test evidence for that exact stand
→ Evidence seals&#47;references the bound proof (no suite re-start)
→ Verifier validates artifacts&#47;claims&#47;hashes&#47;bindings statically
→ Pre-PR checks only additional Non-GitHub local invariants
→ Push&#47;PR
→ GitHub Required Checks provide binding broad regression
```

## Decision principle (every local check)

Before executing a local check:

1. **A** — Is this check already executed as a GitHub Required Check?
2. **B** — Does a local repetition add information mandatory before push?

If `A=true` and `B=false`: **do not execute locally**.

If the exact same stand already has a full `PASS` with `EXIT=0` for the
same selector&#47;command: **do not re-execute**.

## Reuse binding (fail-closed)

A local PASS may be reused only when all of the following hold:

- identical commit **or** unambiguously bound worktree&#47;diff
- identical test selector&#47;command
- full run completed
- result `PASS`
- `EXIT=0`

Otherwise the proof is invalid and the suite must run once.

## Local checks retained (why GitHub does not replace them)

| Check | Why retained |
| --- | --- |
| Final diff freeze + `FINAL_DIFF_SHA256` | Local orchestration; not a required GitHub context |
| Canonical CI selector on final diff | Determines `NO_OP`&#47;`FOCUSED`&#47;`FULL` and timing necessity |
| Ruff format&#47;check on Python diff | Pre-push first diagnosis (GitHub must not be first lint diagnosis) |
| Docs token policy on `.md` diff | Pre-push first diagnosis for token policy |
| Docs reference targets on `.md` diff | Pre-push first diagnosis for link targets |
| One bound capability&#47;owner test | Creates the reusable local PASS binding |
| Static evidence + manifest verify | Durable evidence integrity |
| Safety&#47;activation&#47;credential&#47;order hard-stops | Must never be weakened |

## Redundant local re-executions removed

| Pattern | Why removed |
| --- | --- |
| Capability suite re-run only to seal evidence | Seal&#47;reference the bound PASS |
| Capability suite re-run inside static verifier | Verify artifacts statically |
| Pre-PR re-run of the identical bound suite | Reuse bound PASS; GitHub remains broad layer |
| Local full-suite mirror of GitHub `tests (3.11)` | No extra pre-push information when bound FOCUSED PASS exists |
| Timing-proof re-run of identical already-measured stand | Reuse wallclock from bound PASS when still valid |

## Hard stops preserved

This policy does **not** authorize:

- weakening Safety&#47;Governance&#47;Activation&#47;Credential&#47;Order hard-stops
- starting Capability 11.13
- claiming reuse without an identical-stand binding
- replacing GitHub Required Checks with local opinion

## Canonical owners

| Surface | Owner |
| --- | --- |
| Machine-readable policy | `docs&#47;ops&#47;specs&#47;GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.json` |
| Orchestrator | `scripts&#47;ops&#47;verification_minimum_local_ci_dedup_v1.py` |
| Pre-PR envelope verifier | `scripts&#47;ops&#47;verify_pre_pr_validation_result_v0.py` |
| Required checks SSOT | `config&#47;ci&#47;required_status_checks.json` |
| Runbook binding | Master Runbook §15.3 |
| Contract tests | `tests&#47;ci&#47;test_verification_minimum_local_ci_dedup_v1.py` |

## Generic (not Cap-11.12-specific)

This policy is capability-generic. It must not invent Cap-11.12-only
bypass paths. Cap 11.13 remains out of scope and must not be started.
