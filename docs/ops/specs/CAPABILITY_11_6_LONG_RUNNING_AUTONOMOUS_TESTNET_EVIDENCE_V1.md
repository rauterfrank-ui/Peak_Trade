---
docs_token: DOCS_TOKEN_CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_EVIDENCE_V1
status: active
scope: Phase 11 Cap 11.6 long-running autonomous Testnet evidence contracts only; no activation
capability: CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_EVIDENCE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability 11.6 — Long-Running Autonomous Testnet Evidence V1

## Goal

Implement the Phase 11 **Long-running autonomous Testnet evidence**
contract layer (Master Runbook §11.19 capability sequence + §11.12.8 /
§11.12 Testnet closure evidence fields / §11.15 observability) on top of
CLOSED Cap 11.1–11.5 (contracts-only, not activated), without activating
Testnet/Live, without loading exchange credentials, without starting a
network session, without submitting exchange orders, without claiming §11.12 Testnet closure proven flags
(`TESTNET_ORDER_LIFECYCLE_PROVEN`, `TESTNET_RECONCILIATION_PROVEN`,
`TESTNET_RESTART_PROVEN`, `TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN`,
`TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN`, `TESTNET_KILL_SWITCH_PROVEN`,
`TESTNET_AUTONOMOUS_RECOVERY_PROVEN`, `TESTNET_EVIDENCE_VERIFIED`), and without
starting Cap 11.7 Live private read-only surfaces.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
EXCHANGE_CREDENTIAL_USE_AUTHORIZED=false
REAL_CAPITAL_MOVEMENT_AUTHORIZED=false
NETWORK_SESSION_STARTED=false
TESTNET_EXECUTION_ADAPTER_ACTIVATED=false
TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_6=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_6=false
CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED=true
LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED=false
TESTNET_EVIDENCE_VERIFIED=false
CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED=false
```

## In scope

- Long-running autonomous Testnet campaign evidence fixture contracts (§11.12.8)
- Testnet evidence-closure field contracts without proven overclaim (§11.12)
- Observability and audit evidence fixture contracts (§11.15)
- Cap 11.1 / 11.2 / 11.3 / 11.4 / 11.5 dependency retention proofs
- Ownership matrix for Cap 11.6 evidence fields
- Negative reachability / anti-activation proofs
- Explicit refusal of Cap 11.7 Live private read-only surfaces

## Out of scope

- Cap 11.7+ Live private read-only and shadow reconciliation
- Real long-running Testnet campaign execution
- Real Testnet order submission or network trading session
- Real private API / credential materialization
- Live execution adapters becoming reachable
- Authorization consumption or activation
- Trading / strategy / risk / safety core mutation
- Claiming §11.12 Testnet closure proven flags (`TESTNET_*_PROVEN`,
  `TESTNET_EVIDENCE_VERIFIED`)

## Productive owners

| Surface | Owner |
| --- | --- |
| Capability package | `ops.capability_11_6_long_running_autonomous_testnet_evidence_v1` |
| Long-running campaign evidence | Cap 11.6 package |
| Testnet evidence closure | Cap 11.6 package |
| Observability / audit evidence | Cap 11.6 package |
| Predecessor lifecycle contracts | Cap 11.1 (retained, unchanged) |
| Predecessor credential/auth/account boundary | Cap 11.2 (retained, unchanged) |
| Predecessor private-readonly / reconciliation | Cap 11.3 (retained, unchanged) |
| Predecessor Testnet lifecycle closure | Cap 11.4 (retained, unchanged) |
| Predecessor restart / recovery / kill-switch | Cap 11.5 (retained, unchanged) |

## Call graph

### BEFORE

```text
Canonical Stateful Trading Core
→ Cap 11.1 Intent / Lifecycle Contracts
→ Cap 11.2 Credential / Authorization / Account-Identity Boundary
→ Cap 11.3 Private Read-Only Venue Integration Contracts
→ Cap 11.4 Testnet Execution Adapter and Lifecycle Closure Contracts
→ Cap 11.5 Testnet Restart / Recovery / Kill-Switch Closure Contracts
→ SimulatedExecutionPort (sole reachable)
→ Accounting / Portfolio / Reconciliation / Evidence
```

### AFTER

```text
Canonical Stateful Trading Core (unchanged)
→ Cap 11.1 contracts retained
→ Cap 11.2 boundary retained
→ Cap 11.3 private-readonly / reconciliation retained
→ Cap 11.4 Testnet lifecycle closure retained
→ Cap 11.5 restart / recovery / kill-switch retained
→ Cap 11.6 Long-Running Autonomous Testnet Evidence Contracts
   ├─ LongRunningCampaignEvidenceRecordV1 (fixture-only)
   ├─ TestnetEvidenceClosureFieldRecordV1 (fixture-only)
   └─ ObservabilityDomainEvidenceRecordV1 (fixture-only)
→ SimulatedExecutionPort (sole reachable)
→ Accounting / Portfolio / Reconciliation / Evidence
```

## Safety claims

```text
TESTNET_EXECUTION_REACHABLE=false
LIVE_EXECUTION_REACHABLE=false
REAL_EXECUTION_ADAPTER_CONSTRUCTED=false
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE=false
NETWORK_SESSION_STARTED=false
TESTNET_EXECUTION_ADAPTER_ACTIVATED=false
TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_6=false
PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED=false
REAL_CAPITAL_MOVEMENT_REACHABLE=false
LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED=false
CAPABILITY_11_1_DEPENDENCY_SATISFIED=true
CAPABILITY_11_2_DEPENDENCY_SATISFIED=true
CAPABILITY_11_3_DEPENDENCY_SATISFIED=true
CAPABILITY_11_4_DEPENDENCY_SATISFIED=true
CAPABILITY_11_5_DEPENDENCY_SATISFIED=true
CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED=true
CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED=false
TESTNET_ORDER_LIFECYCLE_PROVEN=false
TESTNET_RECONCILIATION_PROVEN=false
TESTNET_RESTART_PROVEN=false
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=false
TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=false
TESTNET_KILL_SWITCH_PROVEN=false
TESTNET_AUTONOMOUS_RECOVERY_PROVEN=false
TESTNET_EVIDENCE_VERIFIED=false
```

## Evidence

- Package: `docs/evidence/capability_11_6_long_running_autonomous_testnet_evidence_v1/`
- Generator: `scripts/ops/generate_capability_11_6_evidence_v1.py`
- Verifier: `scripts/ops/verify_capability_11_6_long_running_autonomous_testnet_evidence_v1.py`
- Tests: `tests/ops/test_capability_11_6_long_running_autonomous_testnet_evidence_v1.py`

## Activation

This capability is **not** an activation. Later Phase 11 stages (including
Cap 11.7) require separate Owner-GO and activation contracts.
