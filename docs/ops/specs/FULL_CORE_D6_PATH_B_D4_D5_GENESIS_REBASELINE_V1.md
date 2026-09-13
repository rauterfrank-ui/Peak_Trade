---
docs_token: DOCS_TOKEN_FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1
status: active
scope: Full-Core D6 PATH_B D4/D5 genesis rebaseline; new reconstruction epoch without reconstructing the legacy D4/D5 runtime chain; one authorized GET /api/v5/account/config as D4 bootstrap source; genesis point-window without completeness claim; observation S1-S5 not executed; no mapping; no MS2; no D7; no POST; no LiveExecutionPort construction
capability: FULL_CORE_D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-13
---

# Full Core D6 PATH_B D4 D5 Genesis Rebaseline V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.BB.

```text
OWNER_GO=OWNER_GO_D6_PATH_B_D4_D5_GENESIS_REBASELINE_CONTINUE_V1
OWNER_GO_STATUS=CONSUMED
WORKPACKAGE=D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1
GENESIS_REBASELINE_SELECTED_BY_OWNER=true
LEGACY_D4_D5_RUNTIME_CHAIN=NOT_RECONSTRUCTED
HISTORICAL_CONTINUITY_CLAIMED=false
HISTORICAL_COMPLETENESS_CLAIMED=false
PRE_GENESIS_DATA_IMPORTED=false
PRE_GENESIS_PERIOD=OUT_OF_SCOPE_FOR_NEW_RUNTIME_CHAIN
D4_GENESIS_BOOTSTRAP_SOURCE=FRESH_AUTHENTICATED_ACCOUNT_CONFIG
POINT_WINDOW_DOES_NOT_ASSERT_ZERO_PRIOR_EVENTS=true
NEW_CANONICAL_RUNTIME_CHAIN_STARTS_AT_GENESIS_AS_OF=true
D4_POST_GENESIS_OBSERVATION_MUST_NOT_MINT_IDENTITY=true
OBSERVATION_EXECUTED=false
OBSERVATION_EXECUTION_AUTHORIZED=false
OBSERVATION_NETWORK_GET_AUTHORIZED=false
KIND_SET_RESOLVED=false
MS2_AUTHORIZED=false
D6_FULLY_CLOSED=false
D7_AUTHORIZED=false
C01_REHABILITATION_FORBIDDEN=true
ATLAS_AUTHORITY=NONE
NETWORK_POST_PERFORMED=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
C17_CREATED=false
RECONSTRUCTION_ENGINE_CREATED=false
AUTHORITY_EFFECT=NONE
GENESIS_ID=D4D5GENESIS8d3f573ffc0c59b4
GENESIS_AS_OF=2026-09-13T17:03:18Z
ACCOUNT_CONFIG_GET_PERFORMED=true
ADDITIONAL_READ_ONLY_GETS=0
D4_GENESIS_FIELD_FAIL_CLOSED=bound_td_mode
D4_RUNTIME_INSTANCE_PRESENT=false
D5_RUNTIME_INSTANCE_PRESENT=false
OBSERVATION_S0_PREREQUISITES_SATISFIED=false
```

This persist starts a new canonical D4/D5 runtime chain. It does not
reconstruct missing historical D4/D5 runtime instances. Evidence
created by this persist is valid only from `GENESIS_AS_OF`. Earlier
periods are out of scope for the new chain.

The one authorized network action is `GET &#47;api&#47;v5&#47;account&#47;config`.
That fresh authenticated response may bootstrap observable account
identity facts for the genesis boundary. Env, credential contents,
defaults, fixtures, and historical evidence remain forbidden mint
sources. Missing members fail closed on that field.

The D5 genesis window is a point window
`start = end = observed_at_as_of = GENESIS_AS_OF`. That does not
assert zero prior events and does not prove historical completeness.
Observation S1-S5 remain unauthorized.
