---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_BINDING_AND_VERIFIER_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-7 multi-session continuity campaign binding and verifier; no campaign execution
capability: PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_BINDING_AND_VERIFIER_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-7 Campaign Binding And Verifier Implementation V1

## Problem / Root Cause

After Step-6 productive Real-Network session `CLOSED_PASS`, ladder step
`MULTI_SESSION_CONTINUITY_CAMPAIGN` remained `OPEN`, but productive Step-7
campaign package / harness / per-session evidence / campaign bundle /
campaign verifier surfaces were absent.

## Goal

Close only the productive Step-7 **binding** gap:

```text
Campaign owner / entrypoint
+ campaign-state contract (per-session auth; no permanent network enable;
  no auth/confirm reuse; explicit cross-session continuity check)
+ reuse Step-3 restart, Step-4 reconnect, Step-6 stale/adverse (no parallels)
+ per-session evidence contract
+ read-only campaign bundle aggregator
+ campaign verifier (multi-session requirement expressed as >1)
```

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
AUTHORIZATION_CONSUMED=false
CONFIRM_TOKEN_MINTED=false
CONFIRM_TOKEN_CONSUMED=false
PHASE_9_2_STEP_7_STATUS=OPEN
PHASE_9_2_SESSION_LADDER_COMPLETE=false
STEP7_BINDING_IMPLEMENTED=true
READY_FOR_SEPARATE_OWNER_GO_CAMPAIGN_EXECUTION=true
MULTI_SESSION_REQUIREMENT_EXPRESSION=>1
```

This capability does **not** authorize or execute a multi-session campaign
and does not mint or consume authorization or confirm tokens.

## Call graph

### CALL_GRAPH_BEFORE

```text
(absent Step-7 campaign surfaces)
→ HARD_STOP / PREFLIGHT_PASS_STEP7_PRODUCTIVE_PACKAGE_ABSENT
```

### CALL_GRAPH_AFTER

```text
evaluate_step7_binding_gate_v1
→ load_and_validate_campaign_state_contract_v1
→ prove_step7_reuse_bindings_v1 (Step 3/4/6 owners)
→ run_step7_campaign_harness_binding_v1
→ per_session_evidence_contract_v1
→ aggregate_completed_sessions_read_only_v1
→ verify_campaign_bundle_v1
→ NETWORK_SESSION_STARTED=false
→ PHASE_9_2_STEP_7_STATUS=OPEN
→ PHASE_9_2_SESSION_LADDER_COMPLETE=false
```

## Multi-session requirement

No invented governance minimum count. Verifier enforces:

```text
MULTI_SESSION_REQUIREMENT_OPERATOR=>
MULTI_SESSION_REQUIREMENT_OPERAND=1
MULTI_SESSION_REQUIREMENT_EXPRESSION=>1
```

## Explicit non-goals

- no network session start
- no authorization / confirm mint or consume
- no Step-7 CLOSED / ladder complete
- no trading / risk / safety / config-value mutation
- no parallel restart / reconnect / stale semantics

## Owners

| Surface | Path |
| --- | --- |
| Package | `src/ops/phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1/` |
| Entrypoint | `scripts/ops/run_phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.py` |
| Binding config | `config/ops/phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.json` |
| Campaign contract | `config/ops/phase_9_2_public_md_multi_session_continuity_campaign_contract_v1.json` |
| Tests | `tests/ops/test_phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.py` |

## Next safe step

Separate Owner-GO for
`PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_V1`
campaign execution after this binding is merged. Not authorized here.
