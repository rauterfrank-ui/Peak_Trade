# PREREGISTRATION_PROBE_FIXTURE_REPOSITORY_SHA_BINDING_V1

```text
status: ACTIVE
capability: PREREGISTRATION_PROBE_FIXTURE_REPOSITORY_SHA_BINDING_V1
owner: ops.preregistration_probe_fixture_repository_sha_binding_v1
hardens: WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1
authority_effect: NONE
order_effect: NONE
```

Closes the remaining pre-preregistration eligibility unknowns by:

1. Ratifying the normative Desktop forensic 1h runbook identity.
2. Binding Canonical Strategy Probe and Forced Wiring Fixture evidence to the
   checked-out full git SHA (`git rev-parse HEAD`) fail-closed.

## Normative runbook identity

```text
RUNBOOK_NORMATIVE_FILENAME=Peak_Trade_Full_System_Paper_Shadow_1h_Runbook_v4_forensic_safe(6).md
RUNBOOK_SHA256=a7529ef8ba8c5950f6372822b71ac2a5304ae037013288d48d53306d4105ff5a
LOCAL_OPERATOR_COPY_BYTE_IDENTICAL=true
LOCAL_OPERATOR_COPY_FILENAME=Peak_Trade_Full_System_Paper_Shadow_1h_Runbook_v4_forensic_safe.md
```

The local operator copy is byte-identical to the normative filename identity above.
No second runbook truth is introduced.

## Repository SHA binding

```text
REPOSITORY_SHA_SOURCE=git_rev_parse_HEAD
REPOSITORY_SHA_FULL_LENGTH_REQUIRED=true
REPOSITORY_SHA_FAIL_CLOSED=true
```

Probe/fixture `session_manifest.json`, `completion_verdict.json`, and
`integrity_manifest.json` must embed `repository_sha` as exactly 40 lowercase
hex characters. Missing, empty, short, non-hex, uppercase, mismatched, or
cross-artifact conflicting values FAIL.

## Hard invariants / non-claims

```text
GO_FOR_PREREGISTRATION=false
GO_FOR_AUTHORIZATION=false
GO_FOR_1H_RUN=false
HARD_STOP=true
ECONOMIC_VALIDITY_PASS=false
PROMOTION_ELIGIBLE=false
FORCED_FIXTURE_WALLCLOCK_REACHABLE=false
ORDERS_AUTHORIZED=false
LIVE_AUTHORIZED=false
```

This capability does **not** start Preregistration, Authorization, or a 1h run.
