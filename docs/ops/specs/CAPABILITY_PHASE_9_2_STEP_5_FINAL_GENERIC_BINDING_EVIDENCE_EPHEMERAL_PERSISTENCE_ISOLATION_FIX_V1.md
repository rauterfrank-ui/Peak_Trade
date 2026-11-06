---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_5_FINAL_GENERIC_BINDING_EVIDENCE_EPHEMERAL_PERSISTENCE_ISOLATION_FIX_V1
status: active
scope: Isolate Step-5 final-generic evidence materialize failure-injection persistence; no network session; no auth/token semantics change
capability: PHASE_9_2_STEP_5_FINAL_GENERIC_BINDING_EVIDENCE_EPHEMERAL_PERSISTENCE_ISOLATION_FIX_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-06
---

# Capability — Step-5 Final Generic Binding Evidence Ephemeral Persistence Isolation Fix V1

## Root cause

`materialize_step5_final_generic_binding_evidence_v1` wrote failure-injection
single-use ledgers under the shared path
`var/tmp/step5_final_generic_failure_injection`. Rematerialize then failed
`happy_path_once` with `AUTHORIZATION_ALREADY_CONSUMED` /
`AUTHORIZATION_REPLAY_REJECTED`.

## Fix

- Per materialize call: exclusive ephemeral `TemporaryDirectory` persistence root
  (or explicit injected root for tests).
- Legacy shared path is never selected by the materializer.
- Temporary roots are cleaned in `finally`; they are not committed evidence.
- No change to authorization, confirm-token, single-use, replay, network-start,
  core trading, or config semantics.

## Depends on

Logically stacked on PR #5765
(`PHASE_9_2_STEP_5_FINAL_GENERIC_SESSION_AUTHORIZATION_CONSUME_AND_NETWORK_START_BINDING_V1`).

## Evidence

`docs/evidence/capability_phase_9_2_step_5_final_generic_binding_evidence_ephemeral_persistence_isolation_fix_v1`
