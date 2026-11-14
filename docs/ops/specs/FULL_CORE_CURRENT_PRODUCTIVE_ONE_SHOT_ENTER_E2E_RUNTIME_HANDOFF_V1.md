---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1
status: active
scope: CURRENT productive Enter preparation through PRE_EXTERNAL and local pre-live checks
capability: FULL_CORE_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1
last_updated: 2026-11-14
---

# Full Core Current Productive One Shot Enter E2E Runtime Handoff V1

Derived spec. Non-SSOT. Consumes Owner-GO
`OWNER_GO_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1`.

```text
ORIGIN_MAIN_SHA=live git origin/main (29P chain)
POST_PATH_BOUND_BASELINE_SHA=fca07afa1fa74a94cdecde3876c9c30ad79ba828
PRE_EXTERNAL_OWNER_GO=OWNER_GO_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1
POST_OWNER_GO=OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1
K1_OWNER_GO=OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1
REAL_VENUE_POST_ATTEMPTED=false
E2E_RUNTIME_READY=false
POST_HANDOFF_BLOCKER=POST_PENDING_CONTEXT_REQUIRED:OPERATOR_CLI
```

`post_durable_store_root` identifies the directory checked for existing POST
Owner-GO and external-effect consume records. The prepare path only checks
those records.

`productivity_root` defaults to `runtime&#47;current_productive&#47;cap24_selection_state`.

Prepare (no POST):

`./scripts/pt scripts/ops/run_current_productive_one_shot_enter_e2e_prepare_v1.py`

The result records the prepared envelope and a local pre-live checklist
command, leaves `FINAL_OPERATOR_COMMAND` empty, and returns exit code 2
from the prepare CLI. Preflight uses the same lane-qualified cycle ID in
the original quantity observation and the N1 consumer. The original
pending-order observation is tied to the account observer session. The
operator CLI has no input for that session.
Historical handoff reports can still contain a submit command. The current
CLI refuses it before it reads the envelope or opens K1.

Code:
`src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_one_shot_enter_e2e_runtime_handoff_v1.py`

## Scoped correction — 2026-11-03

The prepare API forwards an explicitly supplied shared portfolio budget owner; absence remains fail-closed. ENTER blocked downstream reports its genuine blocker. Natural long/short fixtures now use causal G17 history; the persistent account-bound test requires actual PRE_EXTERNAL and a reservation. No owner/source acquisition, capital-rule or learning change is implied. See [full-flow repair evidence](../evidence/FIVE_FULL_FLOW_REPAIRS_2026_11_03.md) for the 68-case injected proof and remaining limits.
