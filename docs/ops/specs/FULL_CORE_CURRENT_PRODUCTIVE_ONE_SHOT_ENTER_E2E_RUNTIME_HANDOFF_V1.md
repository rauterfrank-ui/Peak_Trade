---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1
status: active
scope: CURRENT productive Enter one-shot E2E prepare handoff (Cap-2.4 → PRE_EXTERNAL → POST CLI)
capability: FULL_CORE_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1
last_updated: 2026-09-27
---

# Full Core Current Productive One Shot Enter E2E Runtime Handoff V1

Derived spec. Non-SSOT. Consumes Owner-GO
`OWNER_GO_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1`.

```text
ORIGIN_MAIN_SHA=live git origin/main (29P chain)
POST_PATH_BOUND_BASELINE_SHA=1e859eaa79f48308cf7037656c6465191ed9993b
PRE_EXTERNAL_OWNER_GO=OWNER_GO_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1
POST_OWNER_GO=OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1
K1_OWNER_GO=OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1
REAL_VENUE_POST_ATTEMPTED=false
```

`post_durable_store_root` is a fresh operator-chosen directory for durable POST
Owner-GO consume and external-effect consume ledgers. Do not reuse historical
evidence packs or a store that already recorded `consumed=true`.

`productivity_root` defaults to `runtime&#47;current_productive&#47;cap24_selection_state`.

Prepare (no POST):

`./scripts/pt scripts/ops/run_current_productive_one_shot_enter_e2e_prepare_v1.py`

Code:
`src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_one_shot_enter_e2e_runtime_handoff_v1.py`
