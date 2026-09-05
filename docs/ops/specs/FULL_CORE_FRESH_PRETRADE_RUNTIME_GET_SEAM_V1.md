---
docs_token: DOCS_TOKEN_FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1
status: active
scope: Full-Core Fresh Pretrade Runtime GET seam; injectable GET-only port; no POST; no arming
capability: FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-05
---

# Full Core Fresh Pretrade Runtime Get Seam V1

## Goal

Implement the Full-Core Fresh Pretrade Runtime GET path as typed evidence.
Do not arm Live. Do not POST. Do not perform a productive venue GET in this
persist. Canary HTTP is not Full-Core transport.

```text
FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED=true
FRESH_PRETRADE_GET_AUTHORITY=VENUE_PRETRADE_GATES
FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION
FRESH_PRETRADE_GET_JOIN_SEAM=join_fresh_pretrade_runtime_get_into_admission_inputs_v1
AUTHORITY_COUNT=1
PARALLEL_PRODUCTIVE_PATH_ADDED=false
FRESH_GET_ALONE_CAN_ADMIT=false
FRESH_GET_CAN_OVERRIDE_OTHER_GATES=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
FULL_CORE_SYSTEM_E2E_PROVEN=false
CURRENT_LIVE_CORE_PATH_PROVEN=false
```

## Required GET set

Unique endpoints, public vs private:

```text
PUBLIC=/api/v5/public/instruments
PUBLIC=/api/v5/public/price-limit
PRIVATE=/api/v5/account/max-size
PRIVATE=/api/v5/account/leverage-info
PRIVATE=/api/v5/account/config
PRIVATE=/api/v5/account/positions
PRIVATE=/api/v5/account/balance
```

Typed items bound to those endpoints:

```text
INSTRUMENT_STATE + MAX_SIZE share instruments
POS_MODE + ACCOUNT_MODE share config
PRICE_BAND, MAX_AVAILABLE, LEVERAGE, MARGIN_MODE, AVAILABLE_MARGIN
```

Positions/reconciliation beyond MARGIN_MODE `mgnMode`/`tdMode` is out of
scope. Canary venue-pretrade-limit extra gate remains canary-only.

## Freshness

```text
FRESHNESS_SEMANTICS=FRESH_GET_PER_PRETRADE_DECISION
TTL_INVENTED=false
HISTORICAL_REUSE_IS_STALE=true
FIXTURE_OR_REPLAY_MARKER_IS_STALE=true
INJECTED_TEST_DOUBLE_CANNOT_CLAIM_VENUE_CONTACT=true
PRODUCTIVE_VENUE_TRANSPORT_NOT_BOUND=true
```

## Fail-closed

Missing, malformed, stale, contradictory, auth-failure, public-failure, one
required item missing, or POST/non-GET fail-closed. Trusted GET evidence does
not set LIVE_ENABLED, LIVE_ARMED, or WIRE_SEND_PERMITTED. Admission remains
`admitted=false`.

## Non-claims

```text
Canary LiveCanaryHttpClientV1 is not Full-Core transport
No productive venue GET is performed by this persist
LIVE_ACCOUNT_BOUND remains unimplemented
Economic canary consumers remain REUSABLE_MECHANISM_ONLY
Fresh GET does not admit Live
```

## Next remaining Full-Core building block

```text
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ACCOUNT_BOUND_IMPLEMENTED
MAX_SAFE_REPO_INTERNAL_NEXT_SLICE=NO_FURTHER_REPO_INTERNAL_SLICE_WITHOUT_LIVE_ACCOUNT_BOUND_OWNER_GO
FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE=true
NEXT_STEP_REQUIRES_OWNER_GO=true
```
