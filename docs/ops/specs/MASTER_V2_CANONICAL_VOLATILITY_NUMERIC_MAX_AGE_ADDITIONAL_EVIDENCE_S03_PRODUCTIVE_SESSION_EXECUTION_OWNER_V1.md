# MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_S03_PRODUCTIVE_SESSION_EXECUTION_OWNER_V1

## Capability

Sole typed productive session execution owner for Additional-Evidence S03 under
Authorization-v2.

OWNER=`research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1`

CANONICAL_EXECUTION_OWNER_SYMBOL=`run_additional_evidence_s03_productive_session_v1`

CLI mode (existing accumulation CLI owner extended, not a second generic runner):

`additional-evidence-s03-session-run`

## Root cause of prior block

`NO_LAWFUL_ADDITIONAL_EVIDENCE_S03_SESSION_EXECUTION_OWNER`

The existing `productive-preregistered-session-run` path is hard-bound to
campaign authorization v1 and exhausted S01/S02 session ids. Auth-v2 alone does
not execute sessions. A parallel ad-hoc orchestrator is forbidden.

## Reuse-before-new

Reused:

- Auth-v2 parser / validator / atomic consumer
- Preregistration v2 validator + contract digest
- Public-MD allowlist / transport boundary helpers from preregistered runner
- Confirm-token fingerprint helper (PSO surface; no plaintext persistence)
- Side-effect ordering vocabulary from Auth-v2

New typed owner package only wires S03 bindings, monotonic 10860s duration,
session lock, S03 evidence schema, terminal verdict, and offline probe.

NO_SECOND_EXECUTION_AUTHORITY=true  
NO_SECOND_DECISION_AUTHORITY=true  
AUTH_V2_IS_SOLE_SESSION_AUTHORITY=true  
CONSUME_BEFORE_SIDE_EFFECTS=true  
SESSION_LOCK_BEFORE_NETWORK=true  
ONE_ACTIVE_SESSION_PER_SCOPE=true  
MONOTONIC_DURATION_AUTHORITY=true  
WALLCLOCK_ONLY_FOR_AUDIT=true  
PUBLIC_MARKET_DATA_ONLY=true  
COUNTERFACTUAL_RUNTIME_IS_NON_AUTHORITY=true  
REQUESTED_DURATION_SECONDS=10860  
HARD_STOP=true  

## Auth-v2 consume-before-side-effects sequence

1. Repository / preregistration / Auth-v2 preflight  
2. Interactive confirm-token (getpass; memory-only)  
3. Atomic Auth-v2 consume  
4. Verify single consumption record; reject second consume  
5. Session lock  
6. Runtime init / public-MD boundary checks  
7. Evidence writers  
8. Terminal verdict + integrity manifest  
9. Ownership-checked lock cleanup  

## Lock lifecycle

Lock binds campaign/session/preregistration/authorization digests, repository
SHA, PID, owner identity, created_at_utc, monotonic start, scope, venue,
instrument. Foreign or live same-session locks fail-closed. No silent stale
takeover. Removal requires ownership proof.

## 10860s monotonic semantics

DURATION_CLOCK=monotonic  
ARTIFICIAL_DELAY_FOR_AGE_CREATION=false  
SYNTHETIC_TIMESTAMP_AGING=false  
MARKET_TIME_FABRICATION=false  
DUPLICATE_SAMPLE_CANNOT_ADVANCE_MARKET_TIME=true  
RUNTIME_CYCLE_CANNOT_ADVANCE_MARKET_TIME=true  

A run shorter than 10860 monotonic seconds cannot be sufficient S03 evidence.

## Public-MD-only bounds

OKX EEA public futures market data, GET-only, existing host/path allowlist.
Private API, credentials, non-GET, orders, testnet/live trading rejected.

## S03 evidence schema

Under campaign evidence root sessions/S03:

- session_metadata.json  
- heartbeat.jsonl  
- connectivity_events.jsonl  
- market_samples.jsonl  
- volatility_records.jsonl  
- volatility_drift_comparisons.jsonl  
- decision_sensitivity.jsonl  
- exit_risk_safety_independence.jsonl  
- counterfactual_decisions.jsonl  
- terminal_verdict.json  
- integrity_manifest.json  

S01/S02 paths are forbidden mutation targets.

## Counterfactual non-authority

Runtime decisions use old volatility observationally; fresh volatility is
counterfactual only. COUNTERFACTUAL_RUNTIME_AUTHORITY_OCCURRED must remain false.

## Exit / risk / safety / reconciliation independence

Observational records assert safety/risk/mandatory-exit/reconciliation remain
available independent of alpha age gates. Exit precedence and reversal
reduce-first sequences are preserved observationally without redefining
Master-V2 trading logic.

## Capability merge invariants

NO_AUTHORIZATION_CONSUMED  
NO_REAL_SESSION_STARTED  
NO_NETWORK_ACTIVITY  
NO_PRODUCTION_EVIDENCE_CREATED  
NO_POLICY_SELECTED  
NO_THRESHOLD_ENFORCED  

PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY=false  
READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION=false  

Real Auth-v2 consumption and wallclock S03 execution require a separate
explicit operator GO after this capability merges.
